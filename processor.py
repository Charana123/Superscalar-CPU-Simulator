import sys
from branch_prediction import branch_predictor
import backend_components
from functional import first, anyy, alll
from state import State
from util import getNextUUID, toString
from consts import RTYPE_OPCODES, LOAD_OPCODES, STORE_OPCODES, COND_BRANCH_OPCODES, UNCOND_JUMP_OPCODES
from debugger import Debugger


def run():
    global STATE
    print("PROGRAM")
    for i, inst in enumerate(STATE.PROGRAM):
        print(i, inst)
    while True:
        ok = runCycle()
        if ok is not None and ok:
            return


def runCycle():
    global STATE

    should_exit = commit()
    writeback()
    execute()
    dispatch()
    issue()
    decode()
    fetch()
    print("PC: %d" % STATE.PC)
    if should_exit:
        print("Program Returned Successfully")
        print("STATE.RETIRED_INSTRUCTIONS = %d" % STATE.RETIRED_INSTRUCTIONS)
        print("STATE.TOTAL_CYCLES = %d" % STATE.TOTAL_CYCLES)
        print("IPC = %f" % (float(STATE.RETIRED_INSTRUCTIONS)/STATE.TOTAL_CYCLES))
        return True
    STATE.TOTAL_CYCLES += 1
    if not STATE.PIPELINE_STALLED:
        STATE.PC += 1


def fetch():
    global STATE

    # if pipeline is stalled, skip fetch
    if STATE.PIPELINE_STALLED:
        STATE.PIPELINE["decode"] = None
        return

    # fetch next instruction
    inst = dict(STATE.PROGRAM[STATE.PC])
    inst_seq_id = getNextUUID()
    inst["inst_seq_id"] = inst_seq_id
    inst["pc"] = STATE.PC
    STATE.PIPELINE["decode"] = inst

    # Optionally check BTB for target address


def decode():
    global STATE

    inst = STATE.PIPELINE["decode"]
    if inst is None:
        return

    # Instruction opcode is made avaialable at the decode stage
    print("STATE.UNSTORED_JALS", STATE.UNSTORED_JALS)
    if inst["opcode"] == "j":
        STATE.PC = inst["arg1"] + 1
        STATE.RETIRED_INSTRUCTIONS += 1 # No ROB entry for jump
    elif inst["opcode"] == "jal":
#        # Add to RAS (Return Address Stack) if not full
#        if len(STATE.REGISTER_ADDRESS_STACK) < STATE.REGISTER_ADDRESS_STACK_MAX:
#            STATE.REGISTER_ADDRESS_STACK.append(inst["pc"])
#            STATE.RETIRED_INSTRUCTIONS += 1 # ROB entry for jump and link if RAS is full
#        else:
#            STATE.UNSTORED_JALS += 1
#            # If jump and link cannot store to RAS, return target stored in $ra
#            STATE.INSTRUCTION_QUEUE.push(inst)
        STATE.INSTRUCTION_QUEUE.push(inst)
        STATE.PC = inst["arg1"] + 1
    elif inst["opcode"] in COND_BRANCH_OPCODES:
        # Make a branch speculation (ie. always taken)
        taken = branch_predictor(inst, STATE)
        if taken:
            STATE.PC = inst["arg3"] + 1
            STATE.INSTRUCTION_QUEUE.push(inst)
        else:
            print("mistake")
            exit()
    elif inst["opcode"] == "jr":
        STATE.PIPELINE_STALLED = True
        STATE.INSTRUCTION_QUEUE.push(inst)
#        # If RAS full, stall, else pop return address and continue
#        if STATE.UNSTORED_JALS != 0:
#            STATE.PIPELINE_STALLED = True
#            # if return jump cannot pop from RAS, load value of $ra from load pipeline
#            STATE.INSTRUCTION_QUEUE.push(inst)
#        else:
#            print("STATE.REGISTER_ADDRESS_STACK", STATE.REGISTER_ADDRESS_STACK)
#            STATE.PC = STATE.REGISTER_ADDRESS_STACK.pop() + 1
#            print("ras", STATE.PC)
#        STATE.RETIRED_INSTRUCTIONS += 1 # No ROB entry for jump return
    elif inst["opcode"] in ["syscall"]:
        STATE.PIPELINE_STALLED = True
        STATE.INSTRUCTION_QUEUE.push(inst)
        print("stalled2")
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
         (inst["opcode"] in COND_BRANCH_OPCODES + ["jr", "jal", "syscall"] and len(filter(lambda bu: not bu.OCCUPIED, STATE.BUs)) == 0):
            return

    STATE.INSTRUCTION_QUEUE.pop()
    # issue into RS
    if inst["opcode"] in RTYPE_OPCODES:
        STATE.ALU_RS.issue(STATE, inst)
    if inst["opcode"] in LOAD_OPCODES + STORE_OPCODES:
        STATE.LSU_RS.issue(STATE, inst)
    if inst["opcode"] in COND_BRANCH_OPCODES + ["noop", "jr", "jal", "syscall"]:
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
        # Flush Pipeline
        STATE.PIPELINE = {
            "decode": None,
            "writeback": None
        }
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

def runProgram(filename):
    global STATE
    STATE = State(filename)

    # run()
    Debugger(STATE, runCycle).run()

if __name__ == "__main__":
    runProgram(sys.argv[1])









