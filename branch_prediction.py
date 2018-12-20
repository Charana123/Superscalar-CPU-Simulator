from functional import generate, first
from util import toString
import abc

################# BRANCH PREDICTOR ######################
class BaseBranchPredictor(object):
    def __init__(self):
        pass

    @abc.abstractmethod
    def getLatestBranchHistory(branch_pc, branch_inst_seq_id):
        pass

    @abc.abstractmethod
    def getLatestSpeculativeBranchHistory(branch_pc, branch_inst_seq_id):
        pass

    @abc.abstractmethod
    def makePrediction(branch_pc, branch_inst_seq_id):
        pass

    @abc.abstractmethod
    def updatePrediction(branch_pc, branch_inst_seq_id, taken):
        pass



################# Branch Target Address and Branch Target Instruction Manipulation ####################

def deleteBTIACEntries(branch_pc, STATE):
    STATE.BTAC.deleteBTACEntry()
    STATE.BTIC.deleteBTICEntry()

def createBTIACEntries(branch_pc, TA, TI, STATE):
    STATE.BTAC.createBTACEntry(branch_pc, TA)
    STATE.BTIC.createBTICEntry(branch_pc, TI)

def getBTIAC(branch_pc, STATE):
    BTACEntry = STATE.BTAC.getBTACEntry(branch_pc)
    # If BTAC exists, go to TA and set pipeline decode to TI
    if BTACEntry is not None:
        TA = BTACEntry.TA
        BTICEntry = STATE.BTIC.getBTICEntry(branch_pc)
        TI = dict(BTICEntry.TI)
        return TA, TI
    else:
        return None


class BranchTargetAddressCache(object):

    class BranchTargetAddressCacheEntry(object):
        def setTargetAddress(self, TA):
            self.TA = TA

        def __str__(self):
            return "TA: %d" % self.TA

        def __repr__(self):
            return self.__str__()

    def __init__(self):
        self.entries = {}

    def getBTACEntry(self, branch_pc):
        return self.entries.get(branch_pc, None)

    def createBTACEntry(self, branch_pc, TA):
        BTAEntry = self.BranchTargetAddressCacheEntry()
        BTAEntry.setTargetAddress(TA)
        self.entries[branch_pc] = BTAEntry

    def deleteBTACEntry(self, branch_pc):
        del self.entries[branch_pc]

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()

class BranchTargetInstructionCache(object):

    class BranchTargetInstructionEntry(object):
        def setTargetInstruction(self, TI):
            self.TI = TI

        def __str__(self):
            return "TI: %s" % str(self.TI)

        def __repr__(self):
            return self.__str__()

    def __init__(self):
        self.entries = {}

    def getBTICEntry(self, branch_pc):
        return self.entries.get(branch_pc, None)

    def createBTICEntry(self, branch_pc, TI):
        BTIEntry = self.BranchTargetInstructionEntry()
        BTIEntry.setTargetInstruction(TI)
        self.entries[branch_pc] = BTIEntry

    def deleteBTICEntry(self, branch_pc):
        del self.entries[branch_pc]

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()

############# RETURN ADDRESS PREDICTION ###################
class RegisterAddressStackCheckpoint(object):

    def __init__(self):
        self.entries = {}

    def saveCheckpoint(self, inst_seq_id, RAS):
        self.entries[inst_seq_id] = list(RAS)

    def retrieveCheckpoint(self, inst_seq_id):
        RAS_Checkpoint = self.entries[inst_seq_id]
        del self.entries[inst_seq_id]
        return RAS_Checkpoint














