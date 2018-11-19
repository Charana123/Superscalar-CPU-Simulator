import uuid
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


class ReseravationStation(object):

    class ReservationStationEntry(object):
        def __init__(self):
            self.tag = str(uuid.uuid4())  # Unique identifier for RS Entry
            self.cycle = None  # Cycle the instruction was issued (for oldest dispatched first heuristic)
            self.Busy = False
            self.Op = None; self.Dest = None
            # ROB Entries corresponding to pending (in-flight in the pipeline) instructions for source operands
            self.ROBj = None; self.ROBk = None
            # Value of source operands (from the register or ROB entry)
            self.Valuej = None; self.Valuek = None
            # Valid bit i.e. have source and dest operands been resolved
            self.Validj = None; self.Validk = None
            # Memory address of load/store operations
            self.A = None

        def cycle(self):
            return self.cycle

        def tag(self):
            return self.tag

        def issue(self, cycle, RAT, inst):
            self.cycle = cycle
            self.Busy = True
            self.Op = inst["opcode"]
            self.Dest = inst["arg1"]

            # First source operand
            RAT_Entry = RAT[inst["arg2"]]
            if RAT_Entry.Valid:
                # Read from register file
                self.Validj = True
                pass
            if not RAT_Entry.Valid and not RAT_Entry.Pending:
                # Read from ROB using ROB_Entry
                self.Validj = True
                pass

            # Second source operand
            RAT_Entry = RAT[inst["arg3"]]
            if RAT_Entry.Valid:
                # Read from register file
                self.Validk = True
                pass
            if not RAT_Entry.Valid and not RAT_Entry.Pending:
                # Read from ROB using ROB_Entry
                self.Validk = True
                pass

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

    def __init__(self, size, functional_units):
        self.ttype = ttype
        self.size = size
        self.functional_units = functional_units
        self.RSs = [ReseravationStation.ReservationStationEntry()] * size

    def dispatch(self, RAT):
        # Evaluate operands of instruction in ReservationStationEntry
        for rs in self.RSs:
            rs.step()
        FU = first(lambda fu: not fu.OCCUPIED, self.functional_units)
        # Check if any functional/execution units are available to dispatch
        if FU is None:
            return
        # Filter all RS Entries whos instruction is ready to be dispatched
        readyRSs = [(rs.tag(), rs.cycle()) for rs in self.RSs if rs.isReady()]
        if len(readyRSs):
            return
        # Find oldest inst
        oldestRS = reduce(lambda (otag, ocycle), (ntag, ncycle): (ntag, ncycle) if ncycle < ocycle else (otag, ocycle), readyRSs)
        FU.dispatch(oldestRS)

    def nextFreeRS(self):
        freeRSs = filter(lambda rs: not rs.Busy, self.RSs)
        if len(freeRSs) > 0:
            return freeRSs[0]


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

class LoadStoreQueue(object):

    class LoadStoreQueueEntry(object):

        def __init__(self):
            self.seq_id = None
            self.Speculative = None
            self.Store = None
            self.A = None  # Address of load/store
            self.V = None  # Value of load/store
            self.ValidV = False # if value has been resolved
            self.ValidA = False # if address has been resolved

    def __init__(self):
        self.issue_ptr = 0
        self.num_entries = 50
        self.entries = [FutureStoreBuffer.FutureStoreBufferEntry()] * self.num_entries
        self.add_to_store_map = {}

    def isFull(self):
        return self.issue_ptr >= self.num_entries

    def findLSQEntry(self, inst_seq_id):
        return find(lambda entry: entry.inst_seq_id == inst_seq_id, self.entires)

    def execute_store(self, inst_seq_id, address, value):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.A = address; lsq_entry.ValidA = True
        lsq_entry.V = value; lsq_entry.ValidV = True
        # Create/Update memory - address to value mapping
        self.add_to_store_map[address] = value

    def execute_load(self, inst_seq_id, address):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.A = address; lsq_entry.ValidA = True
        # Read from latest LSQ entry in preference to from cache (load to store forwarding)
        if address in self.add_to_store_memory:
            lsq_entry.V = self.add_to_store_map[address]

    def execute_branch(self, branch_id, correct):
        lsq_entry = self.findLSQEntry(branch_id)
        spec_entries = filter(lambda entr: branch_id in entr.Speculative_Tags, self.entries)
        if len(spec_entries) == 0:
            raise Exception("no instructions speculatively issued for branch %s" % branch_id)
        if correct:
            # Set speculative bit to 0, if branch was correctly guessed
            for entry in spec_entries:
                if len(entry.Speculative_Tags) == 1:
                    entry.Speculative = False
                    entry.Speculative_Tags.pop(entry.Speculative_Tags.index(branch_id))
                elif len(entry.Speculative_Tags) > 1:
                    entry.Speculative_Tags.pop(entry.Speculative_Tags.index(branch_id))
        else:
            # Clean LSQ of incorrect speculatively issued instructions
            spec_idx = self.entries.index(spec_entries[0])
            self.entries[spec_idx:] = [self.LoadStoreQueueEntry()] * (self.num_entries - spec_idx)

    def issue(self, inst, inst_seq_id, speculative):
        if self.isFull():
            raise False
        if inst["opcode"] not in ["lw", "sw"]:
            raise Exception("LoadStoreQueue only accepts Load/Store instructions")
        vacant_lsq_entry = self.entries[self.issue_ptr]
        vacant_lsq_entry.seq_id = inst_seq_id
        vacant_lsq_entry.Speculative = speculative
        vacant_lsq_entry.Store = if inst["arg1"] == "sw"
        vacant_lsq_entry.V = None; vacant_lsq_entry.ValidV = None
        vacant_lsq_entry.A = None; vacant_lsq_entry.ValidA = None
        self.issue_ptr += 1
        return True

    def commit(self, STACK):
        # Skip if LoadStoreQueue is empty
        if self.issue_ptr == 0:
            return
        inst_to_retire = self.entries[0]
        if not inst_to_retire.Valid or self.Speculative
            return
        if inst_to_retire.Store:
            STACK[inst_to_retire.A] = inst_to_retire.V
        self.entries = self.entries[1:] + [self.LoadStoreQueueEntry()]
        self.issue_ptr -= 1


class ReorderBuffer(object):

    class ReorderBufferEntry(object):

        def __init__(self):
            self.seq_id = None  # Sequence ID of instruction
            self.Speculative = None  # Whether the instruction was speculatively executed
            self.Speculative_Tags = []  # Tags of the speculative instructions it depends on
            self.Valid = None  # Whether there exists a valid value in the ROB Entry
            self.Value = None  # The computed value of the instruction that must be written to program state
            self.Areg = None  # Architectural register the value must be written to

    def __init__(self):
        self.issue_ptr = 0
        self.num_entries = 50
        self.entries = [ReorderBuffer.ReorderBufferEntry()] * self.num_entries

    def isFull(self):
        return self.issue_ptr >= self.num_entries

    def findROBEntry(self, inst_seq_id):
        return find(lambda entry: entry.inst_seq_id == inst_seq_id, self.entires)

    def execute_store(self, inst_seq_id, address, value):
        entry = findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.A = address
        entry.Value = value

    def execute_rtype(self, inst_seq_id, value):
        entry = findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.Value = value

    def execute_branch(self, branch_id, correct):
        entry = findROBEntry(branch_id)
        spec_entries = filter(lambda entr: branch_id in entr.Speculative_Tags, self.entries)
        if len(spec_entries) == 0:
            raise Exception("no instructions speculatively issued for branch %s" % branch_id)
        if correct:
            # Set speculative bit to 0, if branch was correctly guessed
            for entry in spec_entries:
                if len(entry.Speculative_Tags) == 1:
                    entry.Speculative = False
                    entry.Speculative_Tags.pop(entry.Speculative_Tags.index(branch_id))
                elif len(entry.Speculative_Tags) > 1:
                    entry.Speculative_Tags.pop(entry.Speculative_Tags.index(branch_id))
        else:
            # Clean ROB of incorrectly issued instructions
            spec_idx = self.entries.index(spec_entries[0])
            self.entries[spec_idx:] = [self.ReorderBufferEntry()] * (self.num_entries - spec_idx)


    def issue(self, inst, inst_seq_id, speculative):
        if self.isFull():
            return False
        if inst["opcode"] in ["lw", "sw"]:
            raise Exception("Reorder Buffer does not accept Load/Store instructions")
        vacant_rob_entry = self.entries[self.issue_ptr]
        vacant_rob_entry.inst_seq_id = inst_seq_id
        vacant_rob_entry.Speculative = speculative
        vacant_rob_entry.Valid = False
        vacant_rob_entry.Value = None
        vacant_rob_entry.Areg = inst["arg1"]
        self.issue_ptr += 1
        return True

    # Get UUID of Execution unit with the next instruction to be retired in-order
    def commit(self, REGISTER_MNEMONICS, REGISTER_FILE):
        # Skip if reorder buffer is empty
        if self.issue_ptr == 0:
            return
        inst_to_retire = self.entries[0]
        if not inst_to_retire.Valid or self.Speculative
            return
        else:
            REGISTER_FILE[REGISTER_MNEMONICS[inst_to_retire.Areg]] = inst_to_retire.Value
        self.entries = self.entries[1:] + [self.ReorderBufferEntry()]
        self.issue_ptr -= 1





















