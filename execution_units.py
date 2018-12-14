from util import toString
from consts import RTYPE_OPCODES, STORE_OPCODES, LOAD_OPCODES, COND_BRANCH_OPCODES
import abc

class BaseUnit(object):
    def __init__(self, ttype):
        self.ttype = ttype
        self.flush()

    def __str__(self):
        return toString({
            "OCCUPIED": self.OCCUPIED,
            "FINISHED": self.FINISHED,
            "CYCLES": self.CYCLES,
            "CYCLES_PER_OPERATION": self.CYCLES_PER_OPERATION,
            "inputt": self.inputt,
            "output": self.output
        })

    def __repr__(self):
        return self.__str__()

    def flush(self):
        self.inputt = None
        self.FINISHED = False
        self.OCCUPIED = False
        self.output = None
        self.CYCLES = 0
        self.CYCLES_PER_OPERATION = None

    def dispatch(self, inputt):
        self.inputt = inputt
        self.OCCUPIED = True
        self.FINISHED = False
        self.CYCLES = 0

    @abc.abstractmethod
    def step(self, STATE):
        pass


class ALU(BaseUnit):

    def __init__(self):
        super(ALU, self).__init__("alu")

    def __str__(self):
        return super(ALU, self).__str__()

    def __repr__(self):
        return super(ALU, self).__repr__()

    def dispatch(self, inputt):
        super(ALU, self).dispatch(inputt)
        if inputt["opcode"] in ["add", "addi", "sub", "subi"]:
            self.CYCLES_PER_OPERATION = 1
        elif inputt["opcode"] in ["mul", "mod"]:
            self.CYCLES_PER_OPERATION = 3
        elif inputt["opcode"] == "div":
            self.CYCLES_PER_OPERATION = 5

    def step(self, STATE):
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.FINISHED = True
            if self.inputt["opcode"] in ["add", "addi"]:
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["src1"] + self.inputt["src2"]
                }
            elif self.inputt["opcode"] in ["sub", "subi"]:
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["src1"] - self.inputt["src2"]
                }
            elif self.inputt["opcode"] == "mul":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["src1"] * self.inputt["src2"]
                }
            elif self.inputt["opcode"] == "div":
                if self.inputt["src2"] == 0:
                    print("divide by zero exception")
                    exit()
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["src1"] / self.inputt["src2"]
                }
            elif self.inputt["opcode"] == "mod":
                if self.inputt["src2"] == 0:
                    print("divide by zero exception")
                    exit()
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["src1"] % self.inputt["src2"]
                }
            else:
                print("invalid ALU op")
                exit()


class LSU(BaseUnit):
    def __init__(self):
        super(LSU, self).__init__("lsu")

    def __str__(self):
        return super(LSU, self).__str__()

    def __repr__(self):
        return super(LSU, self).__repr__()

    def dispatch(self, inputt):
        super(LSU, self).dispatch(inputt)
        if inputt["opcode"] in ["lw", "sw"]:
          self.CYCLES_PER_OPERATION = 3

    def step(self, STATE):
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.FINISHED = True
            if self.inputt["opcode"] == "lw":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "load",
                    "address": self.inputt["add1"] + self.inputt["add2"]
                }
            elif self.inputt["opcode"] == "sw":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "store",
                    "address": self.inputt["add1"] + self.inputt["add2"],
                    "store_value": self.inputt["src"]
                }
            else:
                exit()


class BU(BaseUnit):
    def __init__(self):
        super(BU, self).__init__("bu")

    def __str__(self):
        return super(BU, self).__str__()

    def __repr__(self):
        return super(BU, self).__repr__()

    def dispatch(self, inputt):
        super(BU, self).dispatch(inputt)
        if self.inputt["opcode"] in COND_BRANCH_OPCODES + ["noop", "jal", "jr", "syscall"]:
            self.CYCLES_PER_OPERATION = 1

    def step(self, STATE):
        if not self.OCCUPIED:
            return
        self.CYCLES += 1
        if self.CYCLES == self.CYCLES_PER_OPERATION:
            self.FINISHED = True
            if self.inputt["opcode"] in COND_BRANCH_OPCODES:
                pc = self.inputt["pc"]
                if((self.inputt["opcode"] == "beq" and self.inputt["src1"] == self.inputt["src2"]) or
                    (self.inputt["opcode"] == "bne" and self.inputt["src1"] != self.inputt["src2"]) or
                    (self.inputt["opcode"] == "bgt" and self.inputt["src1"] > self.inputt["src2"]) or
                    (self.inputt["opcode"] == "bge" and self.inputt["src1"] >= self.inputt["src2"]) or
                    (self.inputt["opcode"] == "blt" and self.inputt["src1"] < self.inputt["src2"]) or
                    (self.inputt["opcode"] == "ble" and self.inputt["src1"] <= self.inputt["src2"])):
                    self.output = {
                        "inst_seq_id": self.inputt["inst_seq_id"],
                        "ttype": "branch",
                        "correct_speculation": STATE.BTB.get(pc).taken
                    }
                if((self.inputt["opcode"] == "beq" and not (self.inputt["src1"] == self.inputt["src2"])) or
                    (self.inputt["opcode"] == "bne" and not(self.inputt["src1"] != self.inputt["src2"])) or
                    (self.inputt["opcode"] == "bgt" and not(self.inputt["src1"] > self.inputt["src2"])) or
                    (self.inputt["opcode"] == "bge" and not(self.inputt["src1"] >= self.inputt["src2"])) or
                    (self.inputt["opcode"] == "ble" and not(self.inputt["src1"] <= self.inputt["src2"]))):
                    self.output = {
                        "inst_seq_id": self.inputt["inst_seq_id"],
                        "ttype": "branch",
                        "correct_speculation": not STATE.BTB.get(pc).taken
                    }
            elif self.inputt["opcode"] == "noop":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "noop"
                }
            elif self.inputt["opcode"] == "jr":
                # set pc and unstall pipeline
                STATE.PC = self.inputt["label"] + 1
                STATE.PIPELINE_STALLED = False
                STATE.UNSTORED_JALS -= 1
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "noop"
                }
            elif self.inputt["opcode"] == "jal":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "register",
                    "result": self.inputt["pc"]
                }
            elif self.inputt["opcode"] == "syscall":
                self.output = {
                    "inst_seq_id": self.inputt["inst_seq_id"],
                    "ttype": "syscall"
                }
                if self.inputt["syscall_type"] == 10:
                    self.output["syscall_type"] = "exit"
            else:
                print("invalid branch-jump instruction")
                exit()






