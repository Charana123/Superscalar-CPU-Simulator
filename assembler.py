import sys

def readProgram(filename):
    # Read Input File
    with open(filename) as f:
        lines = [l.strip() for l in f.readlines()]
        lines = filter(len, lines)
        lines = filter(lambda l: l[0] != '#', lines)
        lines = ["jal main", "addi $v0 $zero c10", "syscall"] + lines

    # Collect Labels
    isLabel = lambda line: line.split(" ")[0][-1] == ':'
    toLabel = lambda line: line.split(" ")[0][:-1]
    def toLabelRec(acc, tup):
        (idx, line) = tup
        if isLabel(line):
            acc[toLabel(line)] = idx
        return acc

    labels = reduce(
            toLabelRec,
            enumerate(lines),
            {}
    )

#    def toProgramRec(acc, tup):
#        (program, current_func) = acc
#        (idx, line) = tup
#        # is Label
#        if isLabel(line):
#            label = toLabel(line)
#            # Create new function with name of the function label
#            program[label] = []
#            current_func = label
#        # is Instruction
#        else:
#            # Append to existing instructions of a function
#            program[current_func].append(line)
#        return program, current_func
#
#
#    program, _ = reduce(
#        toProgramRec,
#        enumerate(lines),
#        ({}, None)
#    )

    def toInstruction(line):
        if not isLabel(line):
            temp = line.split(" ")
            return {
                "opcode": temp[0],
                "arg1": temp[1] if len(temp) > 1 else -1,
                "arg2": temp[2] if len(temp) > 2 else -1,
                "arg3": temp[3] if len(temp) > 3 else -1,
            }
        return line

    def resolveLabels(inst):
        if isinstance(inst, dict):
            if inst["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
                inst["arg3"] = labels[inst["arg3"]]
            if inst["opcode"] in ["j", "jal"]:
                inst["arg1"]= labels[inst["arg1"]]
        return inst

    def transformPseudoInstructions(inst):
				if isinstance(inst, dict):
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
				return inst

    # for label, insts in program.iteritems():
    program = map(toInstruction, lines)
    program = map(resolveLabels, program)
    program = map(transformPseudoInstructions, program)
    # program[label] = insts

    return program

if __name__ == '__main__':
    program = readProgram(sys.argv[1])
    print(program)
















