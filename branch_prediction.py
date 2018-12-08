from functional import generate, first
from util import toString


class BranchTargetBuffer():
    class BranchTargetBufferEntry():

        def __init__(self, REGISTER_ADDRESS_STACK_COPY, inst, branch_pc, taken):
            self.Busy = True
            self.REGISTER_ADDRESS_STACK_COPY = REGISTER_ADDRESS_STACK_COPY
            self.target_address = inst["arg3"]
            self.branch_pc = branch_pc
            self.taken = taken

        def __str__(self):
            return str({
                "busy": self.Busy,
                "target_address": self.target_address,
                "branch_pc": self.branch_pc,
                "taken": self.taken
            })

        def __repr__(self):
            return self.__str__()

        def update(self):
            self.taken = not self.taken

    def __init__(self):
        self.entries = {}

    def __str__(self):
        return toString(self.entries.items())

    def __repr__(self):
        return self.__str__()

    def get(self, pc):
        return self.entries.get(pc, None)

    def create(self, REGISTER_ADDRESS_STACK_COPY, inst, branch_pc, taken):
        self.entries[branch_pc] = self.BranchTargetBufferEntry(REGISTER_ADDRESS_STACK_COPY, inst, branch_pc, taken)

    def update(self, pc):
        self.entries[pc].update()

    def commit(self, pc):
        del self.entries[pc]


def branch_predictor(inst, pc, STATE):
    # TODO - Implement Static branching i.e. backward branches always taken, forward branches never taken
    # TODO - Implement Dynamic branching i.e. BTAC and 2-bit branch predictor
    # Always speculatively take conditional branches
    entry = STATE.BTB.get(pc)
    # If BTB entry exists (i.e. branch previously speculated) use it
    if entry is not None:
        return entry.taken
    # Else create BTB entry and speculatively take the branch
    STATE.BTB.create(list(STATE.REGISTER_ADDRESS_STACK), inst, pc, True)
    return True


def BranchTargetAddressCache(self):
    def __init__(self):
        pass














