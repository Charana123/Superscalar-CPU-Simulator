import sys
from branch_prediction import branch_predictor
import backend_components
from functional import first, anyy, alll
from state import State
from util import getNextUUID
from consts import RTYPE_OPCODES, LOAD_OPCODES, STORE_OPCODES, COND_BRANCH_OPCODES
from debugger import Debugger


def run():
    while True:
        runCycle()


def runCycle():
    global STATE

    print("PC: %d" % STATE.PC)
    should_exit = commit()
    writeback()
    execute()
    dispatch()
    issue()
    decode()
    fetch()
    if should_exit:
        print("Program Returned Successfully")
        print("STATE.RETIRED_INSTRUCTIONS = %d" % STATE.RETIRED_INSTRUCTIONS)
        print("STATE.TOTAL_CYCLES = %d" % STATE.TOTAL_CYCLES)
        print("IPC = %f" % (float(STATE.RETIRED_INSTRUCTIONS)/STATE.TOTAL_CYCLES))
        return
    STATE.TOTAL_CYCLES += 1
    if not STATE.PIPELINE_STALLED:
        STATE.PC += 1


def fetch():
    global STATE

    def jump(inst):
        if inst["opcode"] == "jal":
            if len(STATE.REGISTER_ADDRESS_STACK) < STATE.REGISTER_ADDRESS_STACK_MAX:
                STATE.REGISTER_ADDRESS_STACK.append(STATE.PC + 1)
                print("REGISTER_ADDRESS_STACK = %s" % str(STATE.REGISTER_ADDRESS_STACK))
                STATE.REGISTER_ADDRESS_STACK_FULL = False
            else:
                STATE.REGISTER_ADDRESS_STACK_FULL = True
        else:
            STATE.RETIRED_INSTRUCTIONS += 1
        return inst["arg1"]

    if STATE.PIPELINE_STALLED:
        STATE.PIPELINE["decode"] = None
        return
    if STATE.PC != -1:
        # jumps
        inst = dict(STATE.PROGRAM[STATE.PC])
        if inst["opcode"] in ["j", "jal"]:
            STATE.PC = jump(inst)
            return
        # non-jumps
        inst_seq_id = getNextUUID()
        inst["inst_seq_id"] = inst_seq_id
        inst["pc"] = STATE.PC
        STATE.PIPELINE["decode"] = inst
        # Speculatively execute conditional branches
        if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
            taken = branch_predictor(inst, STATE.PC, STATE)
            if taken:
                STATE.PC = inst["arg3"]
        if inst["opcode"] == "syscall":
            STATE.PIPELINE_STALLED = True
            return

    # If previous lookahead couldn't make a prediction but the end of the function is reached
    if len(STATE.PROGRAM) == (STATE.PC + 1) or not isinstance(STATE.PROGRAM[STATE.PC + 1], dict):
        STATE.PIPELINE_STALLED = True
        return
    # jump lookahead
    lookahead = dict(STATE.PROGRAM[STATE.PC + 1])
    if lookahead["opcode"] in ["j", "jal"]:
        STATE.PC = jump(lookahead)



def decode():
    global STATE

    # Decodes byte instruction to control signals for the rest of the pipeline
    # Already decoded (by assembler)

    inst = STATE.PIPELINE["decode"]
    if inst is None:
        return
    # Resolve RETURN JUMP instructions that requires register lookup (so can only be performed during decode)
    # Do not push to Instruction Queue, wait for next fetch cycle where it the jump return target will be fetched
    if inst["opcode"] == "jr":
        if STATE.REGISTER_ADDRESS_STACK_FULL:
            STATE.PIPELINE_STALLED = True
        else:
            STATE.PC = STATE.REGISTER_ADDRESS_STACK.pop() + 1
            print("pop")
            STATE.RETIRED_INSTRUCTIONS += 1
            STATE.PIPELINE_STALLED = False
    else:
        # Push to instruction queue
        STATE.INSTRUCTION_QUEUE.push(inst)


def issue():
    global STATE, RTYPE_OPCODES, LOAD_OPCODES, STORE_OPCODES, COND_BRANCH_OPCODES

    inst = STATE.INSTRUCTION_QUEUE.peek()
    # Skip is Instruction Queue in empty
    if inst is None:
        return

    # Abort is no execution unit is free
    if (inst["opcode"] in RTYPE_OPCODES and len(filter(lambda alu: not alu.OCCUPIED, STATE.ALUs)) == 0) or \
         (inst["opcode"] in LOAD_OPCODES + STORE_OPCODES and len(filter(lambda lsu: not lsu.OCCUPIED, STATE.LSUs)) == 0) or \
         (inst["opcode"] in COND_BRANCH_OPCODES + ["syscall"] and len(filter(lambda bu: not bu.OCCUPIED, STATE.BUs)) == 0):
            return

    STATE.INSTRUCTION_QUEUE.pop()
    # issue into RS
    if inst["opcode"] in RTYPE_OPCODES:
        STATE.ALU_RS.issue(STATE, inst)
    if inst["opcode"] in LOAD_OPCODES + STORE_OPCODES:
        STATE.LSU_RS.issue(STATE, inst)
    if inst["opcode"] in COND_BRANCH_OPCODES + ["syscall"]:
        print("syscall issued")
        STATE.BU_RS.issue(STATE, inst)
    # create ROB entry
    STATE.ROB.issue(STATE, inst)
    # Update RAT to point instruction 'dest' to inst_seq_id that will have the latest value of that register
    STATE.RAT.issue(inst)


def dispatch():
    global STATE

    # go through reservation stations and call the dipatch instruction
    for rs in [STATE.ALU_RS, STATE.LSU_RS, STATE.BU_RS]:
        rs.dispatch(STATE)


def execute():
    global STATE

    # Step all OCCUPIED function units
    inuse_fus = filter(lambda fu: fu.OCCUPIED and not fu.FINISHED, STATE.ALUs + STATE.LSUs + STATE.BUs)
    for inuse_fu in inuse_fus:
        inuse_fu.step(STATE)
    # Set to the writeback stage a set of instructions that can write its
    # computation to the STATE.ROB
    fin_fus = [fu for fu in STATE.ALUs + STATE.LSUs + STATE.BUs if fu.OCCUPIED and fu.FINISHED]
    # Skip if nothing to writeback this cycle
    if len(fin_fus) == 0:
        STATE.PIPELINE["writeback"] = None
        return
    # Select oldest writeback
    def fu_sort(fu_ttype):
        if fu_ttype == "alu":
            return 1
        if fu_ttype == "lsu":
            return 2
        if fu_ttype == "bu":
            return 3
    fin_fus = sorted(fin_fus, key=lambda writeback: fu_sort(writeback.ttype))
    highest_prorioty_fu = fin_fus[0]
    STATE.PIPELINE["writeback"] = highest_prorioty_fu.output
    highest_prorioty_fu.flush()


def writeback():
    global STATE

    # Broascasts the next writeback over the CDB to update the RSs, ROB and LSQ
    writeback = STATE.PIPELINE["writeback"]
    if writeback is None:
        return
    STATE.CDB.writeback(STATE, writeback)


def commit():
    global STATE

    # Commit next entry of ROB (and optionally the ROB) to the architectural state (memory and register file)
    try:
        STATE.ROB.commit(STATE)
        return False
    except backend_components.ReorderBuffer.PipelineFlush:
        # Flush Instruction Queue
        STATE.INSTRUCTION_QUEUE.flush()
        # Reset the RAT to point to physical registers (i.e. flush)
        STATE.RAT.flush()
        # Flush Reservation Stations
        for rs in [STATE.ALU_RS, STATE.BU_RS, STATE.LSU_RS]:
            rs.flush()
        # Flush Execution Units
        for fu in STATE.ALUs + STATE.BUs + STATE.LSUs:
            fu.flush()
    except backend_components.ReorderBuffer.SyscallExit:
        return True


if __name__ == "__main__":
    global STATE
    filename = sys.argv[1]
    STATE = State(filename)

    # run()
    Debugger(STATE, runCycle).run()









