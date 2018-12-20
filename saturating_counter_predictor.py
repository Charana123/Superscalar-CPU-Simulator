
from branch_prediction import BaseBranchPredictor

# Variable to set whether conditional branch is "statically always taken" or "always not taken"
N_BIT = 1
always_taken = False

class SaturatingCounterPredictor(BaseBranchPredictor):

    def __init__(self):
        self.STATES = 2 ** N_BIT
        self.saturating_counters = {}
        self.pending_speculative_branches = {}
        self.resolved_speculative_branches = {}
        super(SaturatingCounterPredictor, self).__init__()

    def getLatestBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.resolved_speculative_branches[branch_pc][branch_inst_seq_id]

    def getLatestSpeculativeBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.pending_speculative_branches[branch_pc][branch_inst_seq_id]

    def makePrediction(self, branch_pc, branch_inst_seq_id):
        if self.saturating_counters.get(branch_pc, None) is not None:
            taken = self.saturating_counters[branch_pc]["taken"]
        else:
            self.saturating_counters[branch_pc] = {}
            self.saturating_counters[branch_pc]["counter"] = self.STATES - 1 if always_taken else 0
            self.saturating_counters[branch_pc]["taken"] = always_taken
            taken = always_taken

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

        self.saturating_counters[branch_pc]["counter"] = self.clamp(self.saturating_counters[branch_pc]["counter"] + (1 if was_taken else -1), self.STATES, 0)
        taken = True if self.saturating_counters[branch_pc]["counter"] > (self.STATES/2) else False
        self.saturating_counters[branch_pc]["taken"] = taken

    def clamp(self, value, maxx, minn):
        if value > maxx:
            return maxx
        elif value < minn:
            return minn
        else:
            return value













