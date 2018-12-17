import sys
from branch_prediction import makePrediction, getBTIAC, createBTIACEntries, deleteBTIACEntries
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
        if ok:
            return


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
        return True
    STATE.TOTAL_CYCLES += 1
    if not STATE.PIPELINE_STALLED:
        STATE.PC += STATE.INCREMENT
        STATE.INCREMENT = 4
    return False

def fetch():
    global STATE

    # PIPELINE["decode"] reset every cycle
    STATE.PIPELINE["decode"] = []
    # superscalar -
        # If end of function/file reaches, stop fetching
        # If seen [j,jal] encountered, continue fetching from there
        # Instructions beyond branches, unseen relative unconditionals, indirect unconditionals are still fetched (if EOF isn't reached) and should be removed
    i = 0
    while len(STATE.PIPELINE["decode"]) != 4:
        # Stall the pipeline if end of function/file reached
        if STATE.PC+i >= len(STATE.PROGRAM) or not isinstance(STATE.PROGRAM[STATE.PC+i], dict):
            STATE.PIPELINE_STALLED = True
            print("stalled1")

        # if pipeline is stalled, skip fetch
        if STATE.PIPELINE_STALLED:
            return

        # fetch next instruction
        inst = dict(STATE.PROGRAM[STATE.PC+i])
        inst_seq_id = getNextUUID()
        inst["inst_seq_id"] = inst_seq_id
        inst["pc"] = STATE.PC+i

        # Check BTAC and BTIC to get TA and TI ["J", "JAL"] (if they exist)
        # otherwise the [J, JAL] instruction is sent to decode
        if inst["opcode"] in ["j", "jal"]:
            TAI = getBTIAC(inst["pc"], STATE)
            if TAI is not None:
                TA, TI = TAI
                STATE.INCREMENT = 4 - (i + 1)
                STATE.PC = TA + 1 # Continues fetching from TA + 2 onward
                i = 0
                TI["inst_seq_id"] = getNextUUID()
                STATE.PIPELINE["decode"].append(TI)
                STATE.PCS.append(TI["pc"])
                if inst["opcode"] == "jal":
                    if len(STATE.RAS) < STATE.RAS_MAX:
                        STATE.RAS.append(inst["pc"])
                        STATE.RETIRED_INSTRUCTIONS += 1
                    else:
                        STATE.UNSTORED_JALS += 1
                        STATE.INSTRUCTION_QUEUE.push(inst)
                else:
                    STATE.RETIRED_INSTRUCTIONS += 1 # No ROB entry for jump
            else:
                STATE.PIPELINE["decode"].append(inst)
                STATE.PCS.append(inst["pc"])
        else:
            STATE.PIPELINE["decode"].append(inst)
            STATE.PCS.append(inst["pc"])

        i += 1



def decode():
    global STATE

    if STATE.PIPELINE["decode"] == []:
        return

    for i in range(len(STATE.PIPELINE["decode"])):

        inst = STATE.PIPELINE["decode"][i]

        # Instruction opcode is made avaialable at the decode stage
        if inst["opcode"] == "j":
            # Create BTAC and BTIC entries (if they do not exist) for [J, JAL]
            branch_pc, TA, TI = inst["pc"], inst["arg1"], dict(STATE.PROGRAM[inst["arg1"] + 1])
            TI["pc"] = inst["arg1"] + 1
            createBTIACEntries(branch_pc, TA, TI, STATE)

            # Update PC
            STATE.PC = inst["arg1"] + 1
            STATE.RETIRED_INSTRUCTIONS += 1 # No ROB entry for jump
            # Flush instructions after jump and unstall if potentially overread and stalled
            STATE.PIPELINE_STALLED = False
            return

        elif inst["opcode"] == "jal":
            # Create BTAC and BTIC entries (if they do not exist) for [J, JAL]
            branch_pc, TA, TI = inst["pc"], inst["arg1"], dict(STATE.PROGRAM[inst["arg1"] + 1])
            TI["pc"] = inst["arg1"] + 1
            createBTIACEntries(branch_pc, TA, TI, STATE)

            # Add to RAS (Return Address Stack) if not full
            if len(STATE.RAS) < STATE.RAS_MAX:
                STATE.RAS.append(inst["pc"])
                STATE.RETIRED_INSTRUCTIONS += 1
            else:
                STATE.UNSTORED_JALS += 1
                # If jump and link cannot store to RAS, return target stored in $ra
                STATE.INSTRUCTION_QUEUE.push(inst)

            # Update PC and $ra
            STATE.PC = inst["arg1"] + 1
            # Flush instructions after jump
            STATE.PIPELINE_STALLED = False
            return

        elif inst["opcode"] in COND_BRANCH_OPCODES:
            # Create TA entry (for ROB commit, branch recovery)
            pc, TA, TI = inst["pc"], inst["arg3"], dict(STATE.PROGRAM[inst["arg3"] + 1])
            TI["pc"] = inst["arg3"] + 1
            createBTIACEntries(pc, TA, TI, STATE)
            # Checkpoint RAS
            STATE.RASC.saveCheckpoint(inst["inst_seq_id"], STATE.RAS)
            # Make a branch speculation (ie. always
            taken = makePrediction(inst["pc"], STATE)
            if taken:
                STATE.PC = inst["arg3"] + 1
                STATE.INSTRUCTION_QUEUE.push(inst)
                # Flush instructions after branch
                return
            else:
                STATE.INSTRUCTION_QUEUE.push(inst)

        elif inst["opcode"] == "jr":
            print("jr2")
            # If RAS full, stall, else pop return address and continue
            if STATE.UNSTORED_JALS != 0:
                STATE.PIPELINE_STALLED = True
                print("stalled2")
                # if return jump cannot pop from RAS, load value of $ra from load pipeline
                STATE.INSTRUCTION_QUEUE.push(inst)
            else:
                print("jr1")
                STATE.PC = STATE.RAS.pop() + 1
                STATE.PIPELINE_STALLED = False
                STATE.RETIRED_INSTRUCTIONS += 1 # No ROB entry for jump return

        elif inst["opcode"] in ["syscall"]:
            print("stalled3")
            STATE.PIPELINE_STALLED = True
            STATE.INSTRUCTION_QUEUE.push(inst)

        elif inst["opcode"] == "lw":
            # Checkpoint RAS
            STATE.RASC.saveCheckpoint(inst["inst_seq_id"], STATE.RAS)
            STATE.INSTRUCTION_QUEUE.push(inst)

        else:
            # Push to instruction queue
            STATE.INSTRUCTION_QUEUE.push(inst)


def issue():
    global STATE, RTYPE_OPCODES, LOAD_OPCODES, STORE_OPCODES, COND_BRANCH_OPCODES

    for _ in range(4):
        inst = STATE.INSTRUCTION_QUEUE.peek()
        # Skip is Instruction Queue in empty
        if inst is None:
            return

        nofreeRS = (inst["opcode"] in RTYPE_OPCODES and not STATE.ALU_RS.freeRSAvailable()) or \
            (inst["opcode"] in LOAD_OPCODES + STORE_OPCODES and not STATE.LSU_RS.freeRSAvailable()) or \
            (inst["opcode"] in COND_BRANCH_OPCODES + ["jr", "jal", "syscall"] and not STATE.BU_RS.freeRSAvailable())

        if nofreeRS or STATE.ROB.FULL or STATE.LSQ.FULL:
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

    for _ in range(4):
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
        STATE.PIPELINE["writeback"] = []
        return
    # Select oldest 4 writebacks
    def fu_sort(fu_ttype):
        if fu_ttype == "alu":
            return 1
        if fu_ttype == "lsu":
            return 2
        if fu_ttype == "bu":
            return 3
    fin_fus = sorted(fin_fus, key=lambda writeback: fu_sort(writeback.ttype))
    highest_prorioty_fus = fin_fus[:4]
    STATE.PIPELINE["writeback"] = [fu.output for fu in highest_prorioty_fus]
    for fu in highest_prorioty_fus:
        fu.flush()


def writeback():
    global STATE

    # Broascasts the next writeback over the CDB to update the RSs, ROB and LSQ
    writebacks = STATE.PIPELINE["writeback"]
    if writebacks == []:
        return
    for writeback in writebacks:
        STATE.CDB.writeback(STATE, writeback)


def commit():
    global STATE

    for _ in range(4):
        # Commit next entry of ROB (and optionally the ROB) to the architectural state (memory and register file)
        try:
            STATE.ROB.commit(STATE)
        except backend_components.ReorderBuffer.PipelineFlush:
            # Flush ROB and LSQ
            STATE.ROB.flush()
            STATE.LSQ.flush()
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
            return False
        except backend_components.ReorderBuffer.SyscallExit:
            return True
    return False

def runProgram(filename):
    global STATE
    STATE = State(filename)

    # run()
    Debugger(STATE, runCycle).run()

if __name__ == "__main__":
    runProgram(sys.argv[1])









