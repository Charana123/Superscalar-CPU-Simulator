import assembler
from frontend_components import InstructionQueue, ReseravationStation, RegisterAliasTable
from backend_components import ReorderBuffer, LoadStoreQueue, CommonDataBus
from execution_units import ALU, MU, DU, LSU, BU
from branch_prediction import BranchTargetAddressCache, BranchTargetInstructionCache, LocalBranchHistoryBuffers, PatternHistoryTables, RegisterAddressStackCheckpoint

class State(object):

    def __init__(self, filename):
        self.PROGRAM = assembler.readProgram(filename)
        self.RETIRED_INSTRUCTIONS = 0
        self.TOTAL_CYCLES = 0
        self.PC = 0
        self.INCREMENT = 4
        self.REGISTER_FILE = [0] * 34
        self.STACK = [0] * 100
        self.PIPELINE_STALLED = False
        self.PIPELINE = {
            "decode": [],
            "writeback": []
        }
        self.PCS = []
        self.RAS = []
        self.RAS_MAX = 16
        self.UNSTORED_JALS = 0
        self.DUs = [DU()]
        self.DU_RS = ReseravationStation(self.DUs, size=8)
        self.MUs = [MU(), MU()]
        self.MU_RS = ReseravationStation(self.MUs, size=12)
        self.ALUs = [ALU(), ALU(), ALU(), ALU()]
        self.ALU_RS = ReseravationStation(self.ALUs, size=16)
        self.BUs = [BU()]
        self.BU_RS = ReseravationStation(self.BUs, size=8)
        self.LSUs = [LSU(), LSU()]
        self.LSU_RS = ReseravationStation(self.LSUs, size=12)
        self.RAT = RegisterAliasTable()
        self.ROB = ReorderBuffer(100)
        self.LSQ = LoadStoreQueue(100)
        self.INSTRUCTION_QUEUE = InstructionQueue()
        self.CDB = CommonDataBus(self)

        self.BTAC = BranchTargetAddressCache()
        self.BTIC = BranchTargetInstructionCache()
        self.BHB = LocalBranchHistoryBuffers()
        self.PHT = PatternHistoryTables()
        self.RASC = RegisterAddressStackCheckpoint()






