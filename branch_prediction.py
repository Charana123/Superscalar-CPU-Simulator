from functional import generate, first
from util import toString
from consts import N_BIT_HISTORY


################################# Branch Prediction #####################################3

class LocalBranchHistoryBuffers(object):

    class LocalBranchHistoryBufferEntry(object):
        def __init__(self):
            self.history = []

        def update(self, taken):
            self.history.append(taken)
            self.history = self.history[-N_BIT_HISTORY:]

        def __str__(self):
            return "history: %s" % toString(self.history)

        def __repr__(self):
            return self.__str__()

    def __init__(self):
        self.entries = {}

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__repr__()

    def getBranchHistory(self, branch_pc):
        if branch_pc not in self.entries.keys():
            self.entries[branch_pc] = LocalBranchHistoryBuffers.LocalBranchHistoryBufferEntry()
        return self.entries[branch_pc]

    def update(self, branch_pc, taken):
        self.entries[branch_pc].update(taken)


class PatternHistoryTables(object):

    class PatternHistoryTableEntry():

        def __init__(self):
            # An N-bit branch-history has 2^N possible branch-histories
            self.histories = 2 ** N_BIT_HISTORY
            # The prediction for every branch-history is set to 'weakly not taken'
            # as conditions represent forward jumps and are speculatively not taken
            self.entries = [2] * self.histories
            self.taken = [False] * self.histories

        def update(self, pattern_idx, taken):
            self.entries[pattern_idx] += 1 if taken else -1
            self.entries[pattern_idx] = self.clamp(self.entries[pattern_idx], 4, 0)
            self.taken[pattern_idx] = True if self.entries[pattern_idx] > 2 else False

        def clamp(self, value, maxi, mini):
            if value > maxi:
                return maxi
            elif value < mini:
                return mini
            else:
                return value

        def __str__(self):
            return str({
                "entries": toString(self.entries),
                "taken": toString(self.taken)
            })

        def __repr__(self):
            return self.__str__()

    def bitStringToInteger(self, BHB_Entry):
        return reduce(lambda acc, (i, taken): acc + (taken * 2 ** i),
                enumerate(BHB_Entry.history),
                0)

    def __init__(self):
        self.entries = {}

    def getPrediction(self, branch_pc, BHB_Entry):
        pattern_idx = self.bitStringToInteger(BHB_Entry)
        if branch_pc not in self.entries.keys():
            self.entries[branch_pc] = self.PatternHistoryTableEntry()
        BHT_entry = self.entries[branch_pc]
        return BHT_entry.taken[pattern_idx]

    def update(self, branch_pc, BHB_Entry, taken):
        pattern_idx = self.bitStringToInteger(BHB_Entry)
        self.entries[branch_pc].update(pattern_idx, taken)

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()


class RegisterAddressStackCheckpoint(object):

    def __init__(self):
        self.entries = {}

    def saveCheckpoint(self, inst_seq_id, RAS):
        self.entries[inst_seq_id] = list(RAS)

    def retrieveCheckpoint(self, inst_seq_id):
        RAS_Checkpoint = self.entries[inst_seq_id]
        del self.entries[inst_seq_id]
        return RAS_Checkpoint

def getLatestBranchHistory(branch_pc, STATE):
    BHB_Entry = STATE.BHB.getBranchHistory(branch_pc)
    return BHB_Entry.history[-1]

def makePrediction(branch_pc, STATE):
    # Get prediction OR
    # create Branch History Buffer (BHB) and Pattern History Table (PHT) entries AND predict FALSE
    # i.e. all conditionals are not taken
    BHB_Entry = STATE.BHB.getBranchHistory(branch_pc)
    taken = STATE.PHT.getPrediction(branch_pc, BHB_Entry)
    return taken

def updatePrediction(branch_pc, taken, STATE):
    # Update Branch History Buffer
    STATE.BHB.update(branch_pc, taken)
    # Update Pattern History Table
    BHB_Entry = STATE.BHB.getBranchHistory(branch_pc)
    STATE.PHT.update(branch_pc, BHB_Entry, taken)

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

















