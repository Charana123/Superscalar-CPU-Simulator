import sys
import assembler
from functional import first, anyy
from execution_units import ALU, LSU, BU
from components import InstructionQueue, ReseravationStation, RegisterAliasTable, LoadStoreQueue, ReorderBuffer, REGISTER_MNEMONICS, CommonDataBus

def run():
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB
    print("PC: %d" % PC)
    while True:
        issue()
        print("issue_inst: %s" % str(NEW_PIPELINE["execute"]))
        execute()
        print("side_affects: %s" % str(NEW_PIPELINE["writeback"]))
        should_exit = evaluateSideAffect()
        if should_exit:
            print("Program Returned Successfully")
            print("RETIRED_INSTRUCTIONS = %d" % RETIRED_INSTRUCTIONS)
            print("TOTAL_CYCLES = %d" % TOTAL_CYCLES)
            print("IPC = %f" % (float(RETIRED_INSTRUCTIONS)/TOTAL_CYCLES))
            return
        OLD_PIPELINE = dict(NEW_PIPELINE)
        NEW_PIPELINE = {
            "execute": None,
            "writeback": None
        }
        print("PIPELINE_STALLED: %s" % str(PIPELINE_STALLED))
        TOTAL_CYCLES += 1
        if not PIPELINE_STALLED:
            PC += 1
#            for exec_unit in ALUs + LSUs + BUs:
#                exec_unit.step()
            print("INCREMENT")
        print("PC: %d" % PC)


def fetch():
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB

    if PIPELINE_STALLED:
            return
    if PC != -1:
            inst = dict(PROGRAM[PC])
            NEW_PIPELINE["decode"] = dict(PROGRAM[PC])
            # Speculative branching for conditional branches, stall atm
            if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
                            PIPELINE_STALLED = True
            if inst["opcode"] == "syscall":
                            PIPELINE_STALLED = True

    lookahead = dict(PROGRAM[PC + 1])

    # Resolve unconditional branches early in the pipeline using a lookahead
    if lookahead["opcode"] in ["j", "jal"]:
        if lookahead["opcode"] == "jal":
            JAL_INST_ADDR = PC + 1
            if len(REGISTER_ADDRESS_STACK) < REGISTER_ADDRESS_STACK_MAX:
                REGISTER_ADDRESS_STACK.append(PC + 1)
                print("REGISTER_ADDRESS_STACK = %s" % str(REGISTER_ADDRESS_STACK))
                REGISTER_ADDRESS_STACK_FULL = False
            else:
                REGISTER_ADDRESS_STACK_FULL = True
        else:
            RETIRED_INSTRUCTIONS += 1
        PC = inst["arg1"]

    # Resolve target address (TA) from BTAC
    # TODO


def decode():
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB

    # Decodes byte instruction to control signals for the rest of the pipeline
    # Already decoded (by assembler)

    inst = OLD_PIPELINE["decode"]
    # Resolve RETURN JUMP instructions that requires register lookup (so can only be performed during decode)
    # Do not push to Instruction Queue, wait for next fetch cycle where it the jump return target will be fetched
    if inst["opcode"] == "jr":
        if REGISTER_ADDRESS_STACK_FULL:
            PIPELINE_STALLED = True
        else:
            PC = REGISTER_ADDRESS_STACK.pop() + 1
            RETIRED_INSTRUCTIONS += 1
    else:
        # Push to instruction queue
        INSTRUCTION_QUEUE.push(inst)


def issue():

    inst = INSTRUCTION_QUEUE.peek()
    # Abort is Instruction Queue in empty
    if inst is None:
        return

    # Abort is no execution unit is free
    if (inst["opcode"] in ["add", "addi", "sub", "subi", "syscall", "mul", "div"] and len(filter(lambda alu: not alu.OCCUPIED, ALUs)) == 0) or \
         (inst["opcode"] in ["lw", "sw"] and len(filter(lambda lsu: not lsu.OCCUPIED, LSUs)) == 0) or \
         (inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble", "jr", "jal"] and len(filter(lambda bu: not bu.OCCUPIED, BUs)) == 0):
            return

    INSTRUCTION_QUEUE.pop()
    NEW_PIPELINE["execute"] = inst

def dispatch():
    # go through reservation stations and call the dipatch instruction
    for rs in [ALU_RS, LSU_RS, BU_RS]:
        rs.dispatch(RAT)

def execute():
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB

    # Step all OCCUPIED function units
    inuse_fus = filter(lambda fu: fu.OCCUPIED and not fu.FINISHED, ALUs + LSUs + BUs)
    for inuse_fs in inuse_fus:
        inuse_fu.step()

    # Set to the writeback stage a set of instructions that can write its
    # computation to the ROB
    writeback_fus = filter(lambda fu: fu.OCCUPIED, ALUs + LSUs)
    writebacks = [ fu.output for fu in writeback_fus ]
    if writebacks == []:
        NEW_PIPELINE["writeback"] = None
    NEW_PIPELINE["writeback"] = writebacks

def writeback():

    # Takes a list of writebacks, each writeback (instr_tag, ttype, dest, res)
    # Transports over the CDB
    writeback = OLD_PIPELINE["writeback"]
    CDB.writeback(writeback)

def commit():

    # Find next instruction to be retired (comparing the instruction sequence id)
    ROB.commit_ptr = LSQ.commit_ptr


def runProgram(filename):
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB, INSTRUCTION_QUEUE, RAT, ALU_RS, BU_RS, LSU_RS, CDB, LSQ
    PROGRAM = assembler.readProgram(filename)

    RETIRED_INSTRUCTIONS = 0
    TOTAL_CYCLES = 0
    PC = -1
    REGISTER_FILE = [0] * 34
    STACK = [0] * 100
    OLD_PIPELINE = {
        "execute": None,
        "writeback": None
    }
    NEW_PIPELINE = {
        "execute": None,
        "writeback": None
    }
    PIPELINE_EXECUTE_REGISTER = []
    REGISTER_ADDRESS_STACK = []
    REGISTER_ADDRESS_STACK_MAX = 16
    REGISTER_ADDRESS_STACK_FULL = False
    PIPELINE_STALLED = False
    JAL_INST_ADDR = None
    ALUs = [ALU(), ALU()]; ALU_RS = ReseravationStation(ALUs, size=5)
    BUs = [BU()]; BU_RS = ReseravationStation(BUs, size=5)
    LSUs = [LSU()]; LSU_RS = ReseravationStation(LSUs, size=5)
    RAT = RegisterAliasTable()
    ROB = ReorderBuffer()
    LSQ = LoadStoreQueue()
    INSTRUCTION_QUEUE = InstructionQueue()
    CDB = CommonDataBus()
    print(PROGRAM)
    run()


if __name__ == "__main__":
    runProgram(sys.argv[1])










