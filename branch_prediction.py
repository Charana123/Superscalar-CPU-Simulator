from functional import generate, first
from util import toString
from consts import N_BIT_HISTORY


class LocalBranchHistoryBuffers(object):

    class LocalBranchHistoryBufferEntry(object):
        def __init__(self, taken):
            self.history = [taken]

        def update(self, taken):
            self.history.append(taken)
            self.history = self.history[:N_BIT_HISTORY-1]

        def __str__(self):
            return "history: %s" % toString(self.history)

        def __repr__(self):
            return self.__str__()

    def __init__(self):
        self.entries = {}

    def __str__(self):
        return toString(entries.items())

    def __repr__(self):
        return self.__repr__()

    def getBranchHistory(self, branch_pc):
        return self.entries.get(branch_pc, None)

    def update(self, branch_pc, taken):
        if branch_pc not in self.entries:
            self.entires[branch_pc] = self.LocalBranchHistoryBufferEntry(taken)
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
            self.entries[pattern_idx] = min(0, max(4, self.entries[pattern_idx]))
            self.taken[pattern_idx] = True if self.entries[pattern_idx] > 2 else False

        def __str__(self):
            return str({
                "entries": toString(self.entries),
                "taken": toString(self.taken)
            })

        def __repr__(self):
            return self.__str__()

    bitStringToInteger = reduce(lambda acc, (i, taken): acc + (taken * 2 ** i), enumerate(BHB_Entry.history), 0)

    def __init__(self):
        self.entries = {}

    def getPrediction(self, branch_pc, BHB_Entry):
        pattern_idx = self.bitStringToInteger(BHB_Entry.history)
        if branch_pc not in self.entries:
            self.entries[branch_pc] = self.PatternHistoryTableEntry()
        BHT_entry = self.entries[branch_pc]
        return BHT_entry.taken[pattern_idx]

    def update(self, branch_pc, BHB_Entry, taken):
        pattern_idx = self.bitStringToInteger(BHB_Entry.history)
        self.entries[branch_pc].update(pattern_idx, taken)

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()


class BranchTargetBuffer():

    def __init__(self):
        self.entries = {}

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()

    def get(self, pc):
        return self.entries[pc]

    def create(self, inst, branch_pc):
        self.entries[branch_pc] = inst["arg3"]


class RegisterAddressStackCheckpoint(object):

    def __init__(self):
        self.entries = {}

    def speculativeSave(self, branch_inst_seq_id, REGISTER_ADDRESS_STACK):
        self.entries[branch_inst_seq_id] = list(REGISTER_ADDRESS_STACK)

    def get(self, branch_inst_seq_id):
        return self.entries[branch_inst_seq_id]


def makePrediction(inst, branch_pc, STATE):
    branch_inst_seq_id = inst["inst_seq_id"]
    # Create RAS Checkpoint for each branch instruction
    STATE.RAS.speculativeSave(branch_inst_seq_id, STATE.REGISTER_ADDRESS_STACK)
    # Dynamic prediction - If BTB entry exists (i.e. branch previously speculated)
    BHB_Entry = STATE.BHB.getBranchHistory(branch_pc)
    if BHB_Entry is not None:
        taken = STATE.PHT.getPrediction(branch_pc, BHB_Entry)
        return taken
    # Static prediction - if no BHB entry exists, create one and statically predict
    # All conditional branches are NOT TAKEN since -
        # They check the loop break condition i.e. forward jump (breaks backward jump back into the loop)
        # Jumps to the ELSE condition of an IF-ELSE (that not likely to be taken compared to the IF)
    return False


def updatePrediction(inst, branch_pc, taken):
    # Create or Update Branch History Buffer
    STATE.BHB.update(branch_pc, taken)
    # Update Pattern History Table
    BHB_Entry = STATE.BHB.getBranchHistory(branch_pc)
    STATE.PHT.update(branch_pc, BHB_Entry, taken)


def BranchTargetAddressCache(object):

    class BranchTargetAddressCacheEntry(object):
        def __init__(self, branch_pc):
            self.branch_pc = branch_pc

        def setTargetAddress(target_address):
            self.target_address = target_address

    def __init__(self, size=32):
        self.size = size
        self.entries = generate(self.BranchTargetAddressEntry, self.size)

    def getBTACEntry(self, branch_pc):
        return first(lambda entry: entry.branch_pc == branch_pc, self.entries)



class BranchTargetInstructionCache(object):

    class BranchTargetInstructionEntry(object):
        def __init__(self, branch_pc):
            self.branch_pc = branch_pc

        def setInstructions(insts):
            self.insts = insts

    def __init__(self, size=32):
        self.size = size
        self.entries = generate(self.BranchTargetInstructionEntry, self.size)

    def getBTICEntry(self, branch_pc):
        return first(lambda entry: entry.branch_pc == branch_pc, self.entries)






















