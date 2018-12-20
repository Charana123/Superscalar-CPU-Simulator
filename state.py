import assembler
import numpy as np
from frontend_components import InstructionQueue, ReseravationStation, RegisterAliasTable
from backend_components import ReorderBuffer, LoadStoreQueue, CommonDataBus
from execution_units import ALU, MU, DU, LSU, BU, VDU, VMU, VALU, VLSU
from branch_prediction import BranchTargetAddressCache, BranchTargetInstructionCache, RegisterAddressStackCheckpoint
from consts import REGISTER_MNEMONICS, VECTOR_REGISTER_MNEMONICS, VECTOR_LENGTH
from static_predictor import StaticPredictor
from local_two_level_adaptive_predictor import LocalTwoLevelAdaptivePredictor
from saturating_counter_predictor import SaturatingCounterPredictor

class State(object):

    def __init__(self, filename):
        self.PROGRAM = assembler.readProgram(filename)
        self.RETIRED_INSTRUCTIONS = 0
        self.TOTAL_CYCLES = 0
        self.PC = 0
        self.INCREMENT = 4
        self.N_WAY_SUPERSCALAR = 4
        self.REGISTER_FILE = [0] * len(REGISTER_MNEMONICS)
        self.VECTOR_REGISTER_FILE = [np.zeros(VECTOR_LENGTH, dtype=int)] * len(VECTOR_REGISTER_MNEMONICS)
        self.STACK = [0] * 1000
        self.PIPELINE_STALLED = False
        self.PIPELINE = {
            "decode": [],
            "writeback": []
        }
        self.PCS = []
        self.RAS = []
        self.RAS_MAX = 16
        self.UNSTORED_JALS = 0

        # Basic Operations
        self.DUs = [DU()]
        self.DU_RS = ReseravationStation(self.DUs, size=8)
        self.MUs = [MU()]
        self.MU_RS = ReseravationStation(self.MUs, size=12)
        self.ALUs = [ALU(), ALU()]
        self.ALU_RS = ReseravationStation(self.ALUs, size=16)
        self.BUs = [BU()]
        self.BU_RS = ReseravationStation(self.BUs, size=8)
        self.LSUs = [LSU()]
        self.LSU_RS = ReseravationStation(self.LSUs, size=12)
        # Vector Operations
        self.VDUs = [VDU()]
        self.VDU_RS = ReseravationStation(self.VDUs, size=8)
        self.VMUs = [VMU()]
        self.VMU_RS = ReseravationStation(self.VMUs, size=12)
        self.VALUs = [VALU(), VALU()]
        self.VALU_RS = ReseravationStation(self.VALUs, size=16)
        self.VLSUs = [VLSU()]
        self.VLSU_RS = ReseravationStation(self.VLSUs, size=12)






        self.RAT = RegisterAliasTable()
        self.ROB = ReorderBuffer(100)
        self.LSQ = LoadStoreQueue(100)
        self.INSTRUCTION_QUEUE = InstructionQueue()
        self.CDB = CommonDataBus(self)

        # Target caching
        self.BTAC = BranchTargetAddressCache()
        self.BTIC = BranchTargetInstructionCache()
        # Return branch predictor
        self.RASC = RegisterAddressStackCheckpoint()


    def setFlags(self, prediction_mechanism, n_way_superscalar, pipelined_execution_units):
        # Set Branch Prediction Mechanism
        if prediction_mechanism is not None:
            self.PREDICTION_MECHANISM = prediction_mechanism
        else:
            self.PREDICTION_MECHANISM = 3

        if self.PREDICTION_MECHANISM == 'static':
            self.BP = StaticPredictor()
        elif self.PREDICTION_MECHANISM == '1-level-dynamic':
            self.BP = SaturatingCounterPredictor()
        elif self.PREDICTION_MECHANISM == '2-level-dynamic':
            self.BP = LocalTwoLevelAdaptivePredictor()

        # N-WAY superscalar
        if n_way_superscalar is not None:
            self.N_WAY_SUPERSCALAR = n_way_superscalar
        else:
            self.N_WAY_SUPERSCALAR = 4

        # Pipeline Execution Units
        self.PIPELINED_EXECUTION_UNITS = True


    def getRegisterValue(self, key):
        if key[1:3] == "vr":
            return self.VECTOR_REGISTER_FILE[VECTOR_REGISTER_MNEMONICS[key]]
        else:
            return self.REGISTER_FILE[REGISTER_MNEMONICS[key]]

    def setRegisterValue(self, key, value):
	print("key: %s" % str(key))
	print("value: %s" % str(value))
        if key[1:3] == "vr":
            self.VECTOR_REGISTER_FILE[VECTOR_REGISTER_MNEMONICS[key]] = value
        else:
            self.REGISTER_FILE[REGISTER_MNEMONICS[key]] = value



















