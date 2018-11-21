from functional import first, anyy

REGISTER_MNEMONICS = {
    "$zero": 0,
    "$at": 1,
    "$v0": 2, "$v1": 3, # return value of sub-routine
    "$a0": 4, "$a1": 5, "$a2": 6, "$a3": 7, # arguments to sub-routine
    "$t0": 8, "$t1": 9, "$t2": 10, "$t3": 11, "$t4": 12, "$t5": 13,
    "$t6": 14, "$t7": 15, # temporary registers (not preserved across function calls)
    "$s0": 16, "$s1": 17, "$s2": 18, "$s3": 19, "$s4": 20, "$s5": 21, "$s6": 22, "$s7": 23, # saved registers (preserved accross function calls i.e. stored on stack)
    "$t8": 24, "$t9": 25, "$k0": 26, "$k1": 27, "$gp": 28, # global pointer (points to start "data" segment in memory
    "$sp": 29, # stack pointer
    "$fp": 30, # frame pointer (used to store prior value of $sp before stack frame is pushed)
    "$ra": 31, # return address (stores PC on jump and link instruction i.e. jal)
    "$hi": 32, "$lo": 33,
}

class InstructionQueue(object):
    def __init__(self):
        self.instruction_queue = []

    def peek(self):
        if len(self.instruction_queue) > 0:
            return self.instruction_queue[0]

    def pop(self):
        self.instruction_queue.pop(0)

    def push(self, inst):
        self.instruction_queue.append(inst)

class RegisterAliasTable(object):

    class RegisterAliasTableEntry(object):

        def __init__(self):
            self.Valid = True
            self.Pending = False
            self.ROBi = None

    def __init__(self):
        global REGISTER_MNEMONICS
        self.RAT = dict([ (key, self.RegisterAliasTableEntry()) for key in REGISTER_MNEMONICS.keys()])

    def __getitem__(self, key):
        return self.RAT[key]

    def __setitem__(self, key, value):
        self.RAT[key] = value

class ReseravationStation(object):

    class ReservationStationEntry(object):
        def __init__(self):
            # TODO self.tag = str(uuid.uuid4())  # Unique identifier for RS Entry
            self.inst_seq_id = None  # Cycle the instruction was issued (for oldest dispatched first heuristic)
            self.Busy = False
            self.Speculative = False
            self.Op = None; self.Dest = None
            # ROB Entries corresponding to pending (in-flight in the pipeline) instructions for source operands
            self.ROBj = None; self.ROBk = None
            # Value of source operands (from the register or ROB entry)
            self.Valuej = None; self.Valuek = None
            # Is the source operand required
            self.Necessaryj = None; self.Necessaryk = None
            # Valid bit i.e. have source and dest operands been resolved
            self.Validj = None; self.Validk = None

        def cycle(self):
            return self.inst_seq_id

        def tag(self):
            return self.tag

        def issue(self, cycle, RAT, inst, speculative):
            self.inst_seq_id = inst_seq_id
            self.Busy = True
            self.Speculative = speculative
            self.Op = inst["opcode"]
            self.Dest = inst["arg1"]
            self.Necessaryj = -1 # TODO
            self.Necessaryk = -1 # TODO

#            # First source operand
#            RAT_Entry = RAT[inst["arg2"]]
#            if RAT_Entry.Valid:
#                # Read from register file
#                self.Validj = True
#                pass
#            if not RAT_Entry.Valid and not RAT_Entry.Pending:
#                # Read from ROB using ROB_Entry
#                self.Validj = True
#                pass
#
#            # Second source operand
#            RAT_Entry = RAT[inst["arg3"]]
#            if RAT_Entry.Valid:
#                # Read from register file
#                self.Validk = True
#                pass
#            if not RAT_Entry.Valid and not RAT_Entry.Pending:
#                # Read from ROB using ROB_Entry
#                self.Validk = True
#                pass

        def step(self, RAT):
            if self.Validj != True:
                RAT_Entry = RAT[inst["arg2"]]
                if RAT_Entry.Valid:
                    # Read from register file
                    self.Validj = True
                    pass
                if not RAT_Entry.Valid and not RAT_Entry.Pending:
                    # Read from ROB using ROB Entry
                    self.Validj = True
                    pass

            if self.Validk != True:
                RAT_Entry = RAT[inst["arg3"]]
                if RAT_Entry.Valid:
                    # Read from register file
                    self.Validk = True
                    pass
                if not RAT_Entry.Valid and not RAT_Entry.Pending:
                    # Read from ROB using ROB Entry
                    self.Validk = True
                    pass

        def isReady():
            if self.Validj and self.Validk:
                return True
            else:
                return False

    def __init__(self, functional_units, size = None):
        self.ttype = ttype
        if size is None:
            self.size = len(functional_units)
        else:
            self.size = size
        self.functional_units = functional_units
        self.RSEntries = [ReseravationStation.ReservationStationEntry()] * size

    def dispatch(self, RAT):
        # Evaluate operands of instruction in ReservationStationEntry
        for rs_entry in self.RSEntries:
            rs_entry.step()
        FU = first(lambda fu: not fu.OCCUPIED, self.functional_units)
        # Check if any functional/execution units are available to dispatch
        if FU is None:
            return
        # Filter all RS Entries whos instruction is ready to be dispatched
        readyRSs = [(rs_entry.tag(), rs_entry.cycle()) for rs_entry in self.RSs if rs_entry.isReady()]
        if len(readyRSs):
            return
        # Find oldest inst
        oldestRS = reduce(lambda (otag, ocycle), (ntag, ncycle): (ntag, ncycle) if ncycle < ocycle else (otag, ocycle), readyRSs)
        FU.dispatch(oldestRS)

    def nextFreeRSEntry(self):
        freeRSs = filter(lambda rs_entry: not rs_entry.Busy, self.RSs)
        if len(freeRSs) > 0:
            return freeRSs[0]

    def writeback_rtype(self, reg_writeback):
        (inst_id, _, dest_rob_idx, val) = reg_writeback
        # Complete RS entries whose operands point to ROB entries
        # i.e. The operands are necessary for the instruction and not resolved yet
        for rs_entry in self.RSEntries:
            if rs_entry.Necessaryj and not rs_entry.Validj and rs_entry.ROBj == dest_rob_idx:
                rs_entry.Validj = True
                rs_entry.Valuej = val
            if rs_entry.Necessaryk and not rs_entry.Validk and rs_entry.ROBk == dest_rob_idx:
                rs_entry.Validk = True
                rs_entry.Valuek = val






