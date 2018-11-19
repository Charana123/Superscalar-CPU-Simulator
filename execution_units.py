import processor
import abc
import uuid

class BaseUnit(object):
    def __init__(self):
        self.inputt = None
        self.OCCUPIED = False
        self.output = []
        self.CYCLES = 0
        self.CYCLES_PER_OPERATION = None
        self.uuid = str(uuid.uuid4())

    def dispatch(self, inst):
        print("super dispatch")
        self.inputt = inst
        self.OCCUPIED = True
        self.CYCLES = 0

    @abc.abstractmethod
    def step(self):
        pass

    def getOutput(self):
        output = self.output[0]
        self.output = self.output[1:]
        return output


class ALU(BaseUnit):

    def __init__(self):
        super(ALU, self).__init__()

    def dispatch(self, inst):
        super(ALU, self).dispatch(inst)
        if inst["opcode"] in ["add", "addi", "sub", "subi", "lui", "syscall"]:
          self.CYCLES_PER_OPERATION = 1
        elif inst["opcode"] == "mul":
          self.CYCLES_PER_OPERATION = 3
        elif inst["opcode"] == "div":
          self.CYCLES_PER_OPERATION = 10

    def step(self):
        print("step = %s" % self.uuid)
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.OCCUPIED = False
            print("OCCUPIED = False")
            if self.inputt["opcode"] in ["add", "addi"]:
                self.output.append([("register", self.inputt["arg1"], self.inputt["arg2"] + self.inputt["arg3"])])
            elif self.inputt["opcode"] in ["sub", "subi"]:
                self.output.append([("register", self.inputt["arg1"], self.inputt["arg2"] - self.inputt["arg3"])])
            elif self.inputt["opcode"] == "mul":
                self.output.append([("register", self.inputt["arg1"], self.inputt["arg2"] * self.inputt["arg3"])])
            elif self.inputt["opcode"] == "div":
                processor.parseMnemonics(self.inputt, ["arg1"])
                if self.inputt["arg2"] == 0:
                    print("divide by zero exception")
                    exit()
                self.output.append([("register", "$lo", self.inputt["arg1"] / self.inputt["arg2"]),
                        ("register", "$hi", self.inputt["arg1"] % self.inputt["arg2"])])
            elif self.inputt["opcode"] == "lui":
                self.output.append([("register", self.inputt["arg1"], self.inputt["arg2"] << 16)])
            elif self.inputt["opcode"] == "syscall":
                syscall_type = processor.readReg("$v0")
                print("syscall_type = %d" % syscall_type)
                if syscall_type == 10:
                    self.output.append([("syscall", "exit")])
            else:
                print("invalid ALU op")
                exit()

class LSU(BaseUnit):
    def __init__(self):
      super(LSU, self).__init__()

    def dispatch(self, inst):
        super(LSU, self).dispatch(inst)
        if inst["opcode"] in ["lw", "sw"]:
          self.CYCLES_PER_OPERATION = 3

    def step(self):
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.OCCUPIED = False
            if self.inputt["opcode"] == "lw":
                self.output.append([("register", self.inputt["arg1"], processor.readMem(self.inputt["arg2"] + self.inputt["arg3"]))])
            elif self.inputt["opcode"] == "sw":
                processor.parseMnemonics(self.inputt, ["arg1"])
                self.output.append([("memory", self.inputt["arg2"] + self.inputt["arg3"], self.inputt["arg1"])])
            else:
                print("invalid load-store op")
                exit()

class BU(BaseUnit):
    def __init__(self):
        super(BU, self).__init__()

    def dispatch(self, inst):
        super(BU, self).dispatch(inst)
        if self.inputt["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble", "jr", "jal"]:
            self.CYCLES_PER_OPERATION = 1

    def step(self):
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.OCCUPIED = False
            if self.inputt["opcode"] in ["beq", "bne", "bgt", "bge", "blt", "ble"]:
                processor.parseMnemonics(self.inputt, ["arg1"])
                if((self.inputt["opcode"] == "beq" and self.inputt["arg1"] == self.inputt["arg2"]) or
                    (self.inputt["opcode"] == "bne" and self.inputt["arg1"] != self.inputt["arg2"]) or
                    (self.inputt["opcode"] == "bgt" and self.inputt["arg1"] > self.inputt["arg2"]) or
                    (self.inputt["opcode"] == "bge" and self.inputt["arg1"] >= self.inputt["arg2"]) or
                    (self.inputt["opcode"] == "blt" and self.inputt["arg1"] < self.inputt["arg2"]) or
                    (self.inputt["opcode"] == "ble" and self.inputt["arg1"] <= self.inputt["arg2"])):
                    self.output.append([("pc", "pc", self.inputt["arg3"]),
                            ("stalled", "stalled", False)])
                if((self.inputt["opcode"] == "beq" and not (self.inputt["arg1"] == self.inputt["arg2"])) or
                    (self.inputt["opcode"] == "bne" and not(self.inputt["arg1"] != self.inputt["arg2"])) or
                    (self.inputt["opcode"] == "bgt" and not(self.inputt["arg1"] > self.inputt["arg2"])) or
                    (self.inputt["opcode"] == "bge" and not(self.inputt["arg1"] >= self.inputt["arg2"])) or
                    (self.inputt["opcode"] == "ble" and not(self.inputt["arg1"] <= self.inputt["arg2"]))):
                    self.output.append([("stalled", "stalled", False)])
            elif self.inputt["opcode"] == "jr":
                self.output.append([("pc", "pc", processor.readReg(self.inputt["arg1"])),
                    ("stalled", "stalled", False)])
            elif self.inputt["opcode"] == "jal":
                self.output.append([("register", "$ra", processor.JAL_INST_ADDR)])
            else:
                print("invalid branch-jump instruction")
                exit()

def readReg(arg):
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB
    print("PIPELINE_EXECUTE_REGISTER", PIPELINE_EXECUTE_REGISTER)
    for pipeline_reg in PIPELINE_EXECUTE_REGISTER:
        if pipeline_reg[0][0] == '$':
            if pipeline_reg[0] == arg:
                return pipeline_reg[1]
    reg_num = REGISTER_MNEMONICS[arg]
    return REGISTER_FILE[reg_num]


def readMem(address):
    global PROGRAM, PC, REGISTER_FILE, STACK, OLD_PIPELINE, NEW_PIPELINE, PIPELINE_EXECUTE_REGISTER, REGISTER_ADDRESS_STACK, REGISTER_ADDRESS_STACK_MAX, PIPELINE_STALLED, REGISTER_ADDRESS_STACK_FULL, JAL_INST_ADDR, RETIRED_INSTRUCTIONS, TOTAL_CYCLES, ALUs, BUs, LSUs, ROB
    for pipeline_reg in PIPELINE_EXECUTE_REGISTER:
        if pipeline_reg[0][0] == 'm':
            if int(pipeline_reg[0][1:]) == address:
                return pipeline_reg[1]
    return STACK[address]

def parseMnemonics(inst, args):
    for arg_num in args:
        arg = inst[arg_num]
        if arg != -1 and isinstance(arg, str):
            if arg[0] == '$':
                inst[arg_num] = readReg(arg)
            if arg[0] == 'c':
                inst[arg_num] = int(arg[1:])
