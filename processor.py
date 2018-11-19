import sys
import assembler
from functional import first
from execution_units import ALU, LSU, BU
from components import InstructionQueue, ReorderBuffer, REGISTER_MNEMONICS

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
            for exec_unit in ALUs + LSUs + BUs:
                exec_unit.step()
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
    pass

def execute():
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB

    inst = OLD_PIPELINE["execute"]
    if inst is None:
        NEW_PIPELINE["writeback"] = None
    else:
        # Evaluate registers and consts
        parseMnemonics(inst, ["arg2", "arg3"])
        print("parsed_dec_exec", inst)

        # Submit instruction to suitable Execution Unit
        if inst["opcode"] in ["add", "addi", "sub", "subi", "lui", "syscall", "mul", "div"]:
            unOccupiedALUs = filter(lambda alu: not alu.OCCUPIED, ALUs)
            print(unOccupiedALUs)
            if len(unOccupiedALUs) != 0:
                unOccupiedALUs[0].submit(inst)
                print("submit ALU")
                ROB.add_inst(unOccupiedALUs[0].uuid)
                print("unOccupiedALUs[0].uuid", unOccupiedALUs[0].uuid)

        if inst["opcode"] in ["lw", "sw"]:
            unOccupiedLSUs = filter(lambda lsu: not lsu.OCCUPIED, LSUs)
            if len(unOccupiedLSUs) != 0:
                unOccupiedLSUs[0].submit(inst)
                print("submit LSU")
                ROB.add_inst(unOccupiedLSUs[0].uuid)
                print("unOccupiedLSUs[0].uuid", unOccupiedLSUs[0].uuid)

        if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble", "jr", "jal"]:
            unOccupiedBUs = filter(lambda bu: not bu.OCCUPIED, BUs)
            if len(unOccupiedBUs) != 0:
                unOccupiedBUs[0].submit(inst)
                print("submit BU")
                ROB.add_inst(unOccupiedBUs[0].uuid)
                print("unOccupiedBUs[0].uuid", unOccupiedBUs[0].uuid)

    # Check this cycle if an instruction can be retired
    tag = ROB.inst_to_retire()
    print("tag", tag)
    exec_unit_with_tag = first(lambda exec_unit: exec_unit.uuid == tag and len(exec_unit.output) > 0, ALUs + LSUs + BUs)
    print("exec_unit_with_tag", exec_unit_with_tag)
    if exec_unit_with_tag is not None:
        print("exec_unit_with_tag.output", exec_unit_with_tag.output)
        print("one")
        ROB.retire_inst()
        NEW_PIPELINE["writeback"] = exec_unit_with_tag.getOutput()
        # Store result of register-write/memory-store in pipeline registers
        side_affects = NEW_PIPELINE["writeback"]
        if side_affects is not None:
            print("side_affects", side_affects)
            side_affects = filter(lambda side_affect: side_affect[0] == "register" or side_affect[0] == "memory", side_affects)
            print("side_affects", side_affects)
            PIPELINE_EXECUTE_REGISTER = []
            for side_affect in side_affects:
                (ttype, dest, res) = side_affect
                if ttype == "register":
                    PIPELINE_EXECUTE_REGISTER.append((dest, res))
                if ttype == "memory":
                    PIPELINE_EXECUTE_REGISTER.append(("m" + str(dest), res))


def evaluateSideAffect():

    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB
    side_affects = OLD_PIPELINE["writeback"]
    if side_affects is None:
        return
    RETIRED_INSTRUCTIONS += 1

    def execSysCall(side_affect):
        ttype, syscall_ttype = side_affect
        if syscall_ttype == "exit":
            return True

    def writeBack(side_affect):
        global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB
        (ttype, dest, res) = side_affect
        if ttype == "register":
            reg_num = REGISTER_MNEMONICS[dest]
            REGISTER_FILE[reg_num] = res
            print("REGISTER_FILE[%d] = %d" % (reg_num, res))
        if ttype == "memory":
            STACK[dest] = res
        if ttype == "pc":
            print("res", res)
            PC = res
        if ttype == "stalled":
            PIPELINE_STALLED = res

    for side_affect in side_affects:
        print("side_affect", side_affect)
        ttype = side_affect[0]
        if ttype == "syscall":
            if execSysCall(side_affect):
                return True
        else:
            writeBack(side_affect)
    return False


def runProgram(filename):
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB, INSTRUCTION_QUEUE
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
    ALUs = [ALU(), ALU()]
    BUs = [BU()]
    LSUs = [LSU()]
    RSs = 
    ROB = ReorderBuffer()
    INSTRUCTION_QUEUE = InstructionQueue()
    print(PROGRAM)
    run()


if __name__ == "__main__":
    runProgram(sys.argv[1])










