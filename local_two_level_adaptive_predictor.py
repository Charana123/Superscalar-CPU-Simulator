from branch_prediction import BaseBranchPredictor

N_BIT_HISTORY = 2
always_taken = False

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
            self.entries = [n.histories - 1 if always_taken else 0] * self.histories
            self.taken = [always_taken] * self.histories

        def update(self, pattern_idx, taken):
            self.entries[pattern_idx] += 1 if taken else -1
            self.entries[pattern_idx] = self.clamp(self.entries[pattern_idx], self.histories-1, 0)
            self.taken[pattern_idx] = True if self.entries[pattern_idx] > self.histories/2 else False

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

class LocalTwoLevelAdaptivePredictor(BaseBranchPredictor):

    def __init__(self):
        self.BHB = LocalBranchHistoryBuffers()
        self.PHT = PatternHistoryTables()
        self.pending_speculative_branches = {}
        self.resolved_speculative_branches = {}
        super(LocalTwoLevelAdaptivePredictor, self).__init__()

    def getLatestBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.resolved_speculative_branches[branch_pc][branch_inst_seq_id]

    def getLatestSpeculativeBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.pending_speculative_branches[branch_pc][branch_inst_seq_id]

    def makePrediction(self, branch_pc, branch_inst_seq_id):
        # Get prediction OR
        # create Branch History Buffer (BHB) and Pattern History Table (PHT) entries AND predict FALSE
        # i.e. all conditionals are not taken
        BHB_Entry = self.BHB.getBranchHistory(branch_pc)
        taken = self.PHT.getPrediction(branch_pc, BHB_Entry)

        if self.pending_speculative_branches.get(branch_pc, None) is not None:
            self.pending_speculative_branches[branch_pc][branch_inst_seq_id] = taken
        else:
            self.pending_speculative_branches[branch_pc] = {branch_inst_seq_id: taken}
        return taken

    def updatePrediction(self, branch_pc, branch_inst_seq_id, was_taken):
        if self.resolved_speculative_branches.get(branch_pc, None) is not None:
            self.resolved_speculative_branches[branch_pc][branch_inst_seq_id] = was_taken
        else:
            self.resolved_speculative_branches[branch_pc] = {branch_inst_seq_id: was_taken}

        # Update Branch History Buffer
        self.BHB.update(branch_pc, was_taken)
        # Update Pattern History Table
        BHB_Entry = self.BHB.getBranchHistory(branch_pc)
        self.PHT.update(branch_pc, BHB_Entry, was_taken)










