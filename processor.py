import sys
import assembler
import consts

REGISTER_MNEMONICS = consts.REGISTER_MNEMONICS

def run():
    global PC, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_STALLED, TOTAL_CYCLES, RETIRED_INSTRUCTIONS
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
            print("INCREMENT")
        print("PC: %d" % PC)

def issue():
    global PROGRAM, PC, NEW_PIPELINE, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, JAL_INST_ADDR

    if PIPELINE_STALLED:
        NEW_PIPELINE["execute"] = None
        return
    else:
        inst = dict(PROGRAM[PC])
        NEW_PIPELINE["execute"] = dict(PROGRAM[PC])

        # Resolve unconditional branches
        if inst["opcode"] in ["j", "jal"]:
            if inst["opcode"] == "jal":
                JAL_INST_ADDR = PC
                if len(REGISTER_ADDRESS_STACK) < REGISTER_ADDRESS_STACK_MAX:
                    REGISTER_ADDRESS_STACK.append(PC)
                    print("REGISTER_ADDRESS_STACK = %s" %str(REGISTER_ADDRESS_STACK))
                    REGISTER_ADDRESS_STACK_FULL = False
                else:
                    REGISTER_ADDRESS_STACK_FULL = True
            PC = inst["arg1"]
        if inst["opcode"] == "jr":
            if REGISTER_ADDRESS_STACK_FULL:
                print("PIPELINE STALLED")
                PIPELINE_STALLED = True
            else:
                PC = REGISTER_ADDRESS_STACK.pop() + 1
                NEW_PIPELINE["execute"] = dict(PROGRAM[PC])
                print("pop", inst)

        # Speculative branching for conditional branches
        if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
            PIPELINE_STALLED = True
        if inst["opcode"] == "syscall":
            PIPELINE_STALLED = True

def execute():
    global PC, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, PIPELINE_STALLED

    dec_inst = OLD_PIPELINE["execute"]
    if dec_inst == None:
        return

    def readReg(arg):
        global PIPELINE_EXECUTE_REGISTER, REGISTER_MNEMONICS, REGISTER_FILE
        print("PIPELINE_EXECUTE_REGISTER", PIPELINE_EXECUTE_REGISTER)
        for pipeline_reg in PIPELINE_EXECUTE_REGISTER:
            if pipeline_reg[0][0] == '$':
                if pipeline_reg[0] == arg:
                    return pipeline_reg[1]
        reg_num = REGISTER_MNEMONICS[arg]
        return REGISTER_FILE[reg_num]

    def readMem(address):
        global PIPELINE_EXECUTE_REGISTER, STACK
        for pipeline_reg in PIPELINE_EXECUTE_REGISTER:
            if pipeline_reg[0][0] == 'm':
                if int(pipeline_reg[0][1:]) == address:
                    return pipeline_reg[1]
        return STACK[address]

    def parseMnemonics(dec_instr, args):
        for arg_num in args:
            arg = dec_instr[arg_num]
            if arg != -1 and isinstance(arg, str):
                if arg[0] == '$':
                    dec_inst[arg_num] = readReg(arg)
                if arg[0] == 'c':
                    dec_instr[arg_num] = int(arg[1:])

    # Evaluate registers and consts
    parseMnemonics(dec_inst, ["arg2", "arg3"])
    print("parsed_dec_exec", dec_inst)

    if dec_inst["opcode"] in ["add", "addi"]:
        NEW_PIPELINE["writeback"] = [("register", dec_inst["arg1"], dec_inst["arg2"] + dec_inst["arg3"])]
    elif dec_inst["opcode"] in ["sub", "subi"]:
        NEW_PIPELINE["writeback"] = [("register", dec_inst["arg1"], dec_inst["arg2"] - dec_inst["arg3"])]
    elif dec_inst["opcode"] == "mul":
        NEW_PIPELINE["writeback"] = [("register", dec_inst["arg1"], dec_inst["arg2"] * dec_inst["arg3"])]
    elif dec_inst["opcode"] == "div":
        parseMnemonics(dec_inst, ["arg1"])
        if dec_inst["arg2"] == 0:
            print("divide by zero exception")
            exit()
        NEW_PIPELINE["writeback"] = [("register", "$lo", dec_inst["arg1"] / dec_inst["arg2"]),
                ("register", "$hi", dec_inst["arg1"] % dec_inst["arg2"])]
    elif dec_inst["opcode"] == "lw":
        NEW_PIPELINE["writeback"] = [("register", dec_inst["arg1"], readMem(dec_inst["arg2"] + dec_inst["arg3"]))]
    elif dec_inst["opcode"] == "lui":
        NEW_PIPELINE["writeback"] = [("register", dec_inst["arg1"], dec_inst["arg2"] << 16)]
    elif dec_inst["opcode"] == "sw":
        parseMnemonics(dec_inst, ["arg1"])
        NEW_PIPELINE["writeback"] = [("memory", dec_inst["arg2"] + dec_inst["arg3"], dec_inst["arg1"])]
    elif(dec_inst["opcode"] == "beq" or dec_inst["opcode"] == "bne" or
        dec_inst["opcode"] == "bgt" or dec_inst["opcode"] == "bge" or
        dec_inst["opcode"] == "blt" or dec_inst["opcode"] == "ble"):
        parseMnemonics(dec_inst, ["arg1"])
        if((dec_inst["opcode"] == "beq" and dec_inst["arg1"] == dec_inst["arg2"]) or
            (dec_inst["opcode"] == "bne" and dec_inst["arg1"] != dec_inst["arg2"]) or
            (dec_inst["opcode"] == "bgt" and dec_inst["arg1"] > dec_inst["arg2"]) or
            (dec_inst["opcode"] == "bge" and dec_inst["arg1"] >= dec_inst["arg2"]) or
            (dec_inst["opcode"] == "blt" and dec_inst["arg1"] < dec_inst["arg2"]) or
            (dec_inst["opcode"] == "ble" and dec_inst["arg1"] <= dec_inst["arg2"])):
            # NEW_PIPELINE["writeback"] = [("pc", "pc", dec_inst["arg3"])]
            NEW_PIPELINE["writeback"] = [("pc", "pc", dec_inst["arg3"]),
                    ("stalled", "stalled", False)]
        if((dec_inst["opcode"] == "beq" and not (dec_inst["arg1"] == dec_inst["arg2"])) or
            (dec_inst["opcode"] == "bne" and not(dec_inst["arg1"] != dec_inst["arg2"])) or
            (dec_inst["opcode"] == "bgt" and not(dec_inst["arg1"] > dec_inst["arg2"])) or
            (dec_inst["opcode"] == "bge" and not(dec_inst["arg1"] >= dec_inst["arg2"])) or
            (dec_inst["opcode"] == "blt" and not(dec_inst["arg1"] < dec_inst["arg2"])) or
            (dec_inst["opcode"] == "ble" and not(dec_inst["arg1"] <= dec_inst["arg2"]))):
            NEW_PIPELINE["writeback"] = [("stalled", "stalled", False)]
    elif dec_inst["opcode"] == "jr":
        # NEW_PIPELINE["writeback"] = [("pc", "pc", REGISTER_FILE[REGISTER_MNEMONICS[dec_inst["arg1"]]])]
        if PIPELINE_STALLED:
            NEW_PIPELINE["writeback"] = [("pc", "pc", readReg(dec_inst["arg1"])),
                    ("stalled", "stalled", False)]
        else:
            NEW_PIPELINE["writeback"] = []
    elif dec_inst["opcode"] == "j":
        # NEW_PIPELINE["writeback"] = [("pc", "pc", dec_inst["arg1"])]
        NEW_PIPELINE["writeback"] = []
    elif dec_inst["opcode"] == "jal":
        NEW_PIPELINE["writeback"] = [("register", "$ra", JAL_INST_ADDR)]
    elif dec_inst["opcode"] == "syscall":
        syscall_type = readReg("$v0")
        print("syscall_type = %d" % syscall_type)
        if syscall_type == 10:
            NEW_PIPELINE["writeback"] = [("syscall", "exit")]
    else:
        print("invalid opcode")
        exit()

    side_affects = NEW_PIPELINE["writeback"]
    print("side_affects", side_affects)
    shouldCommit = lambda side_affect: side_affect[0] == "register" or side_affect[0] == "memory"
    side_affects = filter(shouldCommit, side_affects)
    print("side_affects", side_affects)
    PIPELINE_EXECUTE_REGISTER = []
    for side_affect in side_affects:
        (ttype, dest, res) = side_affect
        if ttype == "register":
            PIPELINE_EXECUTE_REGISTER.append((dest, res))
        if ttype == "memory":
            PIPELINE_EXECUTE_REGISTER.append(("m" + str(dest), res))


def evaluateSideAffect():

    global OLD_PIPELINE, RETIRED_INSTRUCTIONS
    side_affects = OLD_PIPELINE["writeback"]
    if side_affects == None:
        return
    RETIRED_INSTRUCTIONS += 1

    def execSysCall(side_affect):
        ttype, syscall_ttype = side_affect
        if syscall_ttype == "exit":
            return True

    def writeBack(side_affect):
        global REGISTER_MNEMONICS, REGISTER_FILE, REGISTER_ADDRESS, STACK, PC, PIPELINE_STALLED
        (ttype, dest, res) = side_affect
        if ttype == "register":
            reg_num = REGISTER_MNEMONICS[dest]
            REGISTER_FILE[reg_num] = res
            # print("REGISTER_FILE[%d] = %d" % (reg_num, res))
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
    global PROGRAM
    PROGRAM = assembler.readProgram(filename)
    global PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES

    RETIRED_INSTRUCTIONS = 0
    TOTAL_CYCLES = 0
    PC = 0
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
    print(PROGRAM)
    run()

if __name__ == "__main__":
    runProgram(sys.argv[1])










