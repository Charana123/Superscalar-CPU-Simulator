import assembler
from frontend_components import InstructionQueue, ReseravationStation, RegisterAliasTable
from backend_components import ReorderBuffer, LoadStoreQueue, CommonDataBus
from execution_units import ALU, LSU, BU

class State(object):

    def __init__(self, filename):
        self.PROGRAM = assembler.readProgram(filename)
        self.RETIRED_INSTRUCTIONS = 0
        self.TOTAL_CYCLES = 0
        self.PC = -1
        self.REGISTER_FILE = [0] * 34
        self.STACK = [0] * 100
        self.PIPELINE_STALLED = False
        self.PIPELINE = {
            "decode": None,
            "writeback": None
        }
        self.REGISTER_ADDRESS_STACK = []
        self.REGISTER_ADDRESS_STACK_MAX = 16
        self.REGISTER_ADDRESS_STACK_FULL = False
        self.JAL_INST_ADDR = None
        self.ALUs = [ALU(), ALU()]
        self.ALU_RS = ReseravationStation(self.ALUs, size=5)
        self.BUs = [BU()]
        self.BU_RS = ReseravationStation(self.BUs, size=5)
        self.LSUs = [LSU()]
        self.LSU_RS = ReseravationStation(self.LSUs, size=5)
        self.RAT = RegisterAliasTable()
        self.ROB = ReorderBuffer(100)
        self.LSQ = LoadStoreQueue(100)
        self.INSTRUCTION_QUEUE = InstructionQueue()
        self.CDB = CommonDataBus(self)
        self.SpeculativelyTaken = []


