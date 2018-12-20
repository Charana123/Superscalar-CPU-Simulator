from util import toString
from consts import COND_BRANCH_OPCODES
from functional import alll, anyy
import numpy as np
import abc

class BaseUnit(object):
    def __init__(self, ttype):
        self.ttype = ttype
        self.flush()

    def __str__(self):
        return toString({
            "OCCUPIED": self.isOccupied(None),
            "FINISHED": self.isFinished(),
            "CYCLES_PER_OPERATION": self.CYCLES_PER_OPERATION,
            "output": self.output
        })

    def __repr__(self):
        return self.__str__()

    def flush(self):
        self.output = [None] * self.CYCLES_PER_OPERATION

    def dispatch(self, STATE, inputt):
        if self.CYCLES_PER_OPERATION == 1:
            self.output[0] = self.compute(STATE, inputt)
        else:
            self.output[0] = inputt

    def isOccupied(self, STATE):
        if STATE is not None and STATE.PIPELINED_EXECUTION_UNITS:
            return anyy(lambda elem: elem is not None, self.output)
        else:
            if self.output[0] is not None:
                return True
            else:
                return False

    def isFinished(self):
        if self.output[-1] is not None:
            return True
        else:
            return False

    def getOutput(self):
        output = self.output[self.CYCLES_PER_OPERATION-1]
        self.output[self.CYCLES_PER_OPERATION-1] = None
        return output

    @abc.abstractmethod
    def step(self, STATE):
        pass

    @abc.abstractmethod
    def compute(self, STATE, inputt):
        pass


class MU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 3
        super(MU, self).__init__("mu")

    def __str__(self):
        return super(MU, self).__str__()

    def __repr__(self):
        return super(MU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(MU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, inputt):
        if inputt["opcode"] == "mul":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["src1"] * inputt["src2"]
            }
        else:
            print("invalid MU op")
            exit()
        return output

class DU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 5
        super(DU, self).__init__("du")

    def __str__(self):
        return super(DU, self).__str__()

    def __repr__(self):
        return super(DU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(DU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):

        if inputt["opcode"] == "div":
            if inputt["src2"] == 0:
                print("divide by zero exception")
                exit()
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["src1"] / inputt["src2"]
            }
        elif inputt["opcode"] == "mod":
            if inputt["src2"] == 0:
                print("divide by zero exception")
                exit()
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["src1"] % inputt["src2"]
            }
        else:
            print("invalid DU op")
            exit()

        return output



class ALU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 1
        super(ALU, self).__init__("alu")

    def __str__(self):
        return super(ALU, self).__str__()

    def __repr__(self):
        return super(ALU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(ALU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] in ["add", "addi"]:
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["src1"] + inputt["src2"]
            }
        elif inputt["opcode"] in ["sub", "subi"]:
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["src1"] - inputt["src2"]
            }
        else:
            print("invalid ALU op")
            exit()
        return output



class LSU(BaseUnit):
    def __init__(self):
        self.CYCLES_PER_OPERATION = 3
        super(LSU, self).__init__("lsu")

    def __str__(self):
        return super(LSU, self).__str__()

    def __repr__(self):
        return super(LSU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(LSU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] == "lw":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "load",
                "address": inputt["add1"] + inputt["add2"]
            }
        elif inputt["opcode"] == "sw":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "store",
                "address": inputt["add1"] + inputt["add2"],
                "store_value": inputt["src"]
            }
        else:
            print("invalid LSU op")
            exit()
        return output


class BU(BaseUnit):
    def __init__(self):
        self.CYCLES_PER_OPERATION = 1
        super(BU, self).__init__("bu")

    def __str__(self):
        return super(BU, self).__str__()

    def __repr__(self):
        return super(BU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(BU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] in COND_BRANCH_OPCODES:
            branch_pc = inputt["pc"]
            branch_inst_seq_id = inputt["inst_seq_id"]
            taken = STATE.BP.getLatestSpeculativeBranchHistory(branch_pc, branch_inst_seq_id)
            if((inputt["opcode"] == "beq" and inputt["src1"] == inputt["src2"]) or
                (inputt["opcode"] == "bne" and inputt["src1"] != inputt["src2"]) or
                (inputt["opcode"] == "bgt" and inputt["src1"] > inputt["src2"]) or
                (inputt["opcode"] == "bge" and inputt["src1"] >= inputt["src2"]) or
                (inputt["opcode"] == "blt" and inputt["src1"] < inputt["src2"]) or
                (inputt["opcode"] == "ble" and inputt["src1"] <= inputt["src2"])):
                STATE.BP.updatePrediction(branch_pc, branch_inst_seq_id, True)
                output = {
                    "inst_seq_id": inputt["inst_seq_id"],
                    "ttype": "branch",
                    "correct_speculation": taken
                }
            if((inputt["opcode"] == "beq" and not (inputt["src1"] == inputt["src2"])) or
                (inputt["opcode"] == "bne" and not(inputt["src1"] != inputt["src2"])) or
                (inputt["opcode"] == "bgt" and not(inputt["src1"] > inputt["src2"])) or
                (inputt["opcode"] == "bge" and not(inputt["src1"] >= inputt["src2"])) or
                (inputt["opcode"] == "blt" and not (inputt["src1"] < inputt["src2"])) or
                (inputt["opcode"] == "ble" and not(inputt["src1"] <= inputt["src2"]))):
                STATE.BP.updatePrediction(branch_pc, branch_inst_seq_id, False)
                output = {
                    "inst_seq_id": inputt["inst_seq_id"],
                    "ttype": "branch",
                    "correct_speculation": not taken
                }
        elif inputt["opcode"] == "noop":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "noop"
            }
        elif inputt["opcode"] == "jr":
            STATE.UNSTORED_JALS -= 1
            # set pc and unstall pipeline
            STATE.PC = inputt["label"] + 1
            STATE.PIPELINE_STALLED = False
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "noop"
            }
        elif inputt["opcode"] == "jal":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "register",
                "result": inputt["pc"]
            }
        elif inputt["opcode"] == "syscall":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "syscall"
            }
            if inputt["syscall_type"] == 10:
                output["syscall_type"] = "exit"
        else:
            print("invalid BU op")
            exit()
        return output


class VALU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 2
        super(VALU, self).__init__("valu")

    def __str__(self):
        return super(VALU, self).__str__()

    def __repr__(self):
        return super(VALU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(VALU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] in ["vadd", "vaddi"]:
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": inputt["src1"] + inputt["src2"]
            }
        elif inputt["opcode"] in ["vsub", "vsubi"]:
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": inputt["src1"] - inputt["src2"]
            }
	elif inputt["opcode"] in ["vcmpeq", "vcmpgt", "vcmplt"]:
	    output = {
		"inst_seq_id": inputt["inst_seq_id"],
		"ttype": "vector_register",
	    }
	    if inputt["opcode"] == "vcmpeq":
		output["result"] = (inputt["src1"] == inputt["src2"]).astype(int)
	    elif inputt["opcode"] == "vcmpgt":
		output["result"] = (inputt["src1"] > inputt["src2"]).astype(int)
	    elif inputt["opcode"] == "vcmplt":
		output["result"] = (inputt["src1"] < inputt["src2"]).astype(int)
	    else:
		print("invalid mask op")
		exit()
	elif inputt["opcode"] == "vblend":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": np.where(inputt["mask"], inputt["src1"], inputt["src2"])
            }
        else:
            print("invalid VALU op")
            exit()
        return output


class VMU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 5
        super(VMU, self).__init__("vmu")

    def __str__(self):
        return super(VMU, self).__str__()

    def __repr__(self):
        return super(VMU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(VMU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] == "vmul":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": inputt["src1"] * inputt["src2"]
            }
        else:
            print("invalid VMU op")
            exit()
        return output


class VDU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 7
        super(VDU, self).__init__("vdu")

    def __str__(self):
        return super(VDU, self).__str__()

    def __repr__(self):
        return super(VDU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(VDU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] == "vdiv":
            if anyy(lambda v: v == 0, inputt["src2"]):
                print("divide by zero exception")
                exit()
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": inputt["src1"] / inputt["src2"]
            }
        elif inputt["opcode"] == "vmod":
            if anyy(lambda v: v == 0, inputt["src2"]):
                print("divide by zero exception")
                exit()
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_register",
                "result": inputt["src1"] % inputt["src2"]
            }
        else:
            print("invalid VDU op")
            exit()
        return output


class VLSU(BaseUnit):

    def __init__(self):
        self.CYCLES_PER_OPERATION = 5
        super(VLSU, self).__init__("vlsu")

    def __str__(self):
        return super(VLSU, self).__str__()

    def __repr__(self):
        return super(VLSU, self).__repr__()

    def dispatch(self, STATE, inputt):
        super(VLSU, self).dispatch(STATE, inputt)

    def step(self, STATE):

        if self.CYCLES_PER_OPERATION > 2:
            for i in range(0, self.CYCLES_PER_OPERATION-2):
                if self.output[i+1] is None:
                    self.output[i+1] = self.output[i]
                    self.output[i] = None

        if self.CYCLES_PER_OPERATION > 1:
            if self.output[self.CYCLES_PER_OPERATION-1] is None and self.output[self.CYCLES_PER_OPERATION-2] is not None:
                inputt = self.output[self.CYCLES_PER_OPERATION-2]
                output = self.compute(STATE, inputt)
                self.output[self.CYCLES_PER_OPERATION-1] = output
                self.output[self.CYCLES_PER_OPERATION-2] = None

    def compute(self, STATE, inputt):
        if inputt["opcode"] == "vload":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_load",
                "address": inputt["add1"] + inputt["add2"]
            }
        elif inputt["opcode"] == "vstore":
            output = {
                "inst_seq_id": inputt["inst_seq_id"],
                "ttype": "vector_store",
                "address": inputt["add1"] + inputt["add2"],
                "store_value": inputt["src"]
            }
        else:
            print("invalid VLSU op")
            exit()
        return output

