import sys
from consts import UNCOND_JUMP_OPCODES, COND_BRANCH_OPCODES
import itertools
from util import toString


def readProgram(filename):
    # Read Input File
    with open(filename) as f:
        lines = [l.strip() for l in f.readlines()]
        lines = filter(len, lines)
        lines = filter(lambda l: l[0] != '#', lines)
        lines = ["jal main", "addi $v0 $zero c10", "syscall"] + lines

    isLabel = lambda line: line.split(" ")[0][-1] == ':'

    def toInstruction(line):
        if not isLabel(line):
            temp = line.split(" ")
            return {
                "opcode": temp[0],
                "arg1": temp[1] if len(temp) > 1 else -1,
                "arg2": temp[2] if len(temp) > 2 else -1,
                "arg3": temp[3] if len(temp) > 3 else -1,
                "arg4": temp[4] if len(temp) > 4 else -1,
            }
        return line

    def resolveLabels(inst):
        if isinstance(inst, dict):
            if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
                inst["arg3"] = labels[inst["arg3"]]
            if inst["opcode"] in ["j", "jal"]:
                inst["arg1"] = labels[inst["arg1"]]
        return inst

    def transformPseudoInstructions(inst):
        if isinstance(inst, dict):
            if inst["opcode"] == "move":
                    inst["opcode"] = "add"
                    inst["arg3"] = "$zero"
            if inst["opcode"] == "li":
                    inst["opcode"] = "addi"
                    inst["arg3"] = "$zero"
            if inst["opcode"] == "vli":
                inst["opcode"] = "vaddi"
                inst["arg3"] = "$vrzero"
        return inst

    # for label, insts in program.iteritems():
    program = map(toInstruction, lines)
    program = map(transformPseudoInstructions, program)

#    def appendNOOPsRec(inst):
#        if isinstance(inst, dict) and inst["opcode"] in UNCOND_JUMP_OPCODES + ["jr", "syscall"] + COND_BRANCH_OPCODES:
#            return [inst, {"opcode": "noop", "arg1": -1, "arg2": -1, "arg3": -1}]
#        else:
#            return [inst]
#    temp = map(lambda inst: appendNOOPsRec(inst), program)
#    program = list(itertools.chain.from_iterable(temp))


    # Collect Labels
    def toLabelRec(acc, tup):
        (idx, inst) = tup
        if not isinstance(inst, dict):
            acc[inst[:-1]] = idx
        return acc

    labels = reduce(
        toLabelRec,
        enumerate(program),
        {}
    )

    program = map(resolveLabels, program)


    return program


if __name__ == '__main__':
    program = readProgram(sys.argv[1])
    print(toString(program))
















