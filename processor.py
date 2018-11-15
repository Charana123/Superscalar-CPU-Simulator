import sys
import assembler
import consts

REGISTER_MNEMONICS = consts.REGISTER_MNEMONICS

def run():
    global PC
    while True:
        inst = fetch()
        print("inst: %s" % str(inst))
        dec_inst = decode(inst)
        print("dec_inst: %s" % str(dec_inst))
        side_affect = execute(dec_inst)
        print("side_affect: %s" % str(side_affect))
        should_exit = evaluateSideAffect(side_affect)
        print("exit", should_exit)
        if should_exit:
            print("Program Returned Successfully")
            return
        PC += 1
        print("PC: %d" % PC)

def fetch():
    global PROGRAM, PC
    return dict(PROGRAM[PC])

def decode(inst):

    # Transform pseduo-instructions
    print(inst)
    if inst["opcode"] == "move":
        inst["opcode"] = "add"
        inst["arg3"] = "$zero"
    if inst["opcode"] == "li":
        inst["opcode"] = "addi"
        inst["arg3"] = "$zero"
    if inst["opcode"] == "mfhi":
        inst["opcode"] = "add"
        inst["arg2"] = "$zero"
        inst["arg3"] = "$hi"
    if inst["opcode"] == "mflo":
        inst["opcode"] = "add"
        inst["arg2"] = "$zero"
        inst["arg3"] = "$lo"

    print("xxx", inst)
    # Evaluate registers and consts
    parseMnemonics(inst, ["arg2", "arg3"])
    return inst

def parseMnemonics(instr, args):
    global REGISTER_MNEMONICS, REGISTER_FILE
    for arg_num in args:
        arg = instr[arg_num]
        if arg != -1 and isinstance(arg, str):
            if arg[0] == '$':
                reg_num = REGISTER_MNEMONICS[arg]
                instr[arg_num] = REGISTER_FILE[reg_num]
            if arg[0] == 'c':
                instr[arg_num] = int(arg[1:])

def execute(dec_inst):
    global REGISTER_MNEMONICS, REGISTER_FILE, STACK, PC
    if dec_inst["opcode"] in ["add", "addi"]:
        return [("register", dec_inst["arg1"], dec_inst["arg2"] + dec_inst["arg3"])]
    if dec_inst["opcode"] in ["sub", "subi"]:
        return [("register", dec_inst["arg1"], dec_inst["arg2"] - dec_inst["arg3"])]
    if dec_inst["opcode"] == "mul":
        return [("register", dec_inst["arg1"], dec_inst["arg2"] * dec_inst["arg3"])]
    if dec_inst["opcode"] == "div":
        parseMnemonics(dec_inst, ["arg1"])
        if dec_inst["arg2"] == 0:
            print("divide by zero exception")
            exit()
        return [("register", "$lo", dec_inst["arg1"] / dec_inst["arg2"]),
                ("register", "$hi", dec_inst["arg1"] % dec_inst["arg2"])]
    if dec_inst["opcode"] == "lw":
        return [("register", dec_inst["arg1"], STACK[dec_inst["arg2"] + dec_inst["arg3"]])]
    if dec_inst["opcode"] == "lui":
        return [("register", dec_inst["arg1"], dec_inst["arg2"] << 16)]
    if dec_inst["opcode"] == "sw":
        parseMnemonics(dec_inst, ["arg1"])
        return [("memory", dec_inst["arg2"] + dec_inst["arg3"], dec_inst["arg1"])]
    if(dec_inst["opcode"] == "beq" or dec_inst["opcode"] == "bne" or
        dec_inst["opcode"] == "bgt" or dec_inst["opcode"] == "bge" or
        dec_inst["opcode"] == "blt" or dec_inst["opcode"] == "ble"):
        parseMnemonics(dec_inst, ["arg1"])
    if((dec_inst["opcode"] == "beq" and dec_inst["arg1"] == dec_inst["arg2"]) or
        (dec_inst["opcode"] == "bne" and dec_inst["arg1"] != dec_inst["arg2"]) or
        (dec_inst["opcode"] == "bgt" and dec_inst["arg1"] > dec_inst["arg2"]) or
        (dec_inst["opcode"] == "bge" and dec_inst["arg1"] >= dec_inst["arg2"]) or
        (dec_inst["opcode"] == "blt" and dec_inst["arg1"] < dec_inst["arg2"]) or
        (dec_inst["opcode"] == "ble" and dec_inst["arg1"] <= dec_inst["arg2"])):
        return [("pc", "pc", dec_inst["arg3"]),
                ("btic", dec_inst["arg3"], PC),
                ("bitprediction", 1, PC)]
    if((dec_inst["opcode"] == "beq" and not (dec_inst["arg1"] == dec_inst["arg2"])) or
        (dec_inst["opcode"] == "bne" and not(dec_inst["arg1"] != dec_inst["arg2"])) or
        (dec_inst["opcode"] == "bgt" and not(dec_inst["arg1"] > dec_inst["arg2"])) or
        (dec_inst["opcode"] == "bge" and not(dec_inst["arg1"] >= dec_inst["arg2"])) or
        (dec_inst["opcode"] == "blt" and not(dec_inst["arg1"] < dec_inst["arg2"])) or
        (dec_inst["opcode"] == "ble" and not(dec_inst["arg1"] <= dec_inst["arg2"]))):
        return [("bitprediction", 0, PC)]
    if dec_inst["opcode"] == "jr":
        return [("pc", "pc", REGISTER_FILE[REGISTER_MNEMONICS[dec_inst["arg1"]]]),
                ("btic", dec_inst["arg3"], PC),
                ("bitprediction", 1, PC)]
    if dec_inst["opcode"] == "j":
        return [("pc", "pc", dec_inst["arg1"])]
    if dec_inst["opcode"] == "jal":
        return [("pc", "pc", dec_inst["arg1"]),
                ("btic", dec_inst["arg3"], PC),
                ("register", "$ra", PC)]
    if dec_inst["opcode"] == "syscall":
        syscall_type = REGISTER_FILE[REGISTER_MNEMONICS["$v0"]]
        if syscall_type == 10:
            return [("syscall", "exit")]
    print("invalid opcode")
    exit()

def evaluateSideAffect(side_affects):

    def execSysCall(side_affect):
        ttype, syscall_ttype = side_affect
        if syscall_ttype == "exit":
            return True

    def writeBack(side_affect):
        global REGISTER_MNEMONICS, REGISTER_FILE, STACK, PC
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
        if ttype == "btic":
            pass
        if ttype == "bitprediction":
            pass

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
    global PC, REGISTER_FILE, STACK
    PC = 0
    REGISTER_FILE = [0] * 34
    STACK = [0] * 100
    print(PROGRAM)
    run()

if __name__ == "__main__":
    runProgram(sys.argv[1])










