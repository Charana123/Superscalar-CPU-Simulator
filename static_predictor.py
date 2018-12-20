from branch_prediction import BaseBranchPredictor

# Variable to set whether conditional branch is "statically always taken" or "always not taken"
always_taken = False

class StaticPredictor(BaseBranchPredictor):

    def __init__(self):
        self.pending_speculative_branches = {}
        self.resolved_speculative_branches = {}
        super(StaticPredictor, self).__init__()

    def getLatestBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.resolved_speculative_branches[branch_pc][branch_inst_seq_id]

    def getLatestSpeculativeBranchHistory(self, branch_pc, branch_inst_seq_id):
        return self.pending_speculative_branches[branch_pc][branch_inst_seq_id]

    def makePrediction(self, branch_pc, branch_inst_seq_id):
        if branch_inst_seq_id == 150:
            print("here")
        if self.pending_speculative_branches.get(branch_pc, None) is not None:
            self.pending_speculative_branches[branch_pc][branch_inst_seq_id] = always_taken
        else:
            self.pending_speculative_branches[branch_pc] = {branch_inst_seq_id: always_taken}
        return always_taken

    def updatePrediction(self, branch_pc, branch_inst_seq_id, taken):
        if self.resolved_speculative_branches.get(branch_pc, None) is not None:
            self.resolved_speculative_branches[branch_pc][branch_inst_seq_id] = taken
        else:
            self.resolved_speculative_branches[branch_pc] = {branch_inst_seq_id: taken}


