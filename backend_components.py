
class CircularBuffer(object):

    def __init__(self, size):
        self.issue_ptr = 0
        self.commit_ptr = 0
        self.size = size
        self.EMPTY = True
        self.FULL = False

    def issue(self, x):
        if self.FULL:
            return False
        ok = self.issue_impl(x)
        if ok:
            self.issue_ptr = (self.issue_ptr + 1) % self.size
            # If after a issue, the issue_ptr points to the commit_ptr, the buffer is full
            if self.issue_ptr == self.commit_ptr:
                self.FULL = True
        return ok

    @abstractmethod
    def issue_impl(self, x):
        pass

    def commit(self, x):
        if self.EMPTY:
            return False
        ok = self.commit_impl(x)
        if ok:
            self.commit_ptr = (self.commit_ptr + 1) % self.size
            # If after a commit, the commit_ptr points to the issue_ptr, the buffer is empty
            if self.issue_ptr == self.commit_ptr:
                self.FULL = False
        return ok

    @ abstractmethod
    def commit_impl(self, x):
        pass


class ReorderBuffer(CircularBuffer):

    class ReorderBufferEntry(object):

        def __init__(self):
            self.seq_id = None  # Sequence ID of instruction
            self.Speculative = None  # Whether the instruction was speculatively executed
            self.Speculative_Tags = []  # Tags of the speculative instructions it depends on
            self.Valid = None  # Whether there exists a valid value in the ROB Entry
            self.Value = None  # The computed value of the instruction that must be written to program state
            self.Areg = None  # Architectural register the value must be written to

    def __init__(self, size):
        super(ReorderBuffer, self).__init__(size)
        self.entries = [ReorderBuffer.ReorderBufferEntry()] * self.size

    def findROBEntry(self, inst_seq_id):
        return find(lambda entry: entry.inst_seq_id == inst_seq_id, self.entires)

    def writeback_rtype(self, inst_seq_id, value):
        entry = findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.Value = value

    def writeback_branch(self, branch_id, correct):
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
            # Clean ROB of incorrectly issued instructions (shift issue_ptr)
            spec_idx = self.entries.index(spec_entries[0])
            self.issue_ptr = spec_idx

    def issue_impl(self, inst, inst_seq_id, speculative):
        if inst["opcode"] in ["lw", "sw"]:
            raise Exception("Reorder Buffer does not accept Load/Store instructions")
        vacant_rob_entry = self.entries[self.issue_ptr]
        vacant_rob_entry.inst_seq_id = inst_seq_id
        vacant_rob_entry.Speculative = speculative
        vacant_rob_entry.Valid = False
        vacant_rob_entry.Value = None
        vacant_rob_entry.Areg = inst["arg1"]
        return True

    def issue(self, inst, inst_seq_id, speculative):
        return super(ReorderBuffer, self).issue(inst, inst_seq_id, speculative)

    def commit_impl(self, REGISTER_MNEMONICS, REGISTER_FILE):
        retire_rob_entry = self.entries[self.commit_ptr]
        if not retire_rob_entry.Valid or retire_rob_entry.Speculative:
            return False
        else:
            REGISTER_FILE[REGISTER_MNEMONICS[retire_rob_entry.Areg]] = retire_rob_entry.Value
            return True

    def commit(self, REGISTER_MNEMONICS, REGISTER_FILE):
        return super(ReorderBuffer, self).commit(REGISTER_MNEMONICS, REGISTER_FILE)


class LoadStoreQueue(CircularBuffer):

    class LoadStoreQueueEntry(object):

        def __init__(self):
            self.seq_id = None
            self.Speculative = None
            self.Store = None
            self.Address = None  # Address of load/store
            self.Value = None  # Value of load/store
            self.ValidV = False # if value has been resolved
            self.ValidA = False # if address has been resolved

    def __init__(self, size):
        super(ReorderBuffer, self).__init__(size)
        self.entries = [FutureStoreBuffer.FutureStoreBufferEntry()] * self.size

    def findLSQEntry(self, inst_seq_id):
        return find(lambda entry: entry.inst_seq_id == inst_seq_id, self.entires)

    def writeback_store(self, inst_seq_id, address, value):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.Address = address; lsq_entry.ValidA = True
        lsq_entry.Value = value; lsq_entry.ValidV = True
        # Create/Update memory - address to value mapping
        self.add_to_store_map[address] = value

    def writeback_load(self, STACK, inst_seq_id, address):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.Address = address; lsq_entry.ValidA = True
        # Read from latest LSQ entry in preference to from cache (load to store forwarding)
        if address in self.add_to_store_memory:
            lsq_entry.Value = self.add_to_store_map[address]
        else:
            lsq_entry.Value = STACK[address]

    def writeback_branch(self, branch_id, correct):
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
            self.issue_ptr = spec_idx

    def issue(self, inst, inst_seq_id, speculative):
        return super(LoadStoreQueue, self).issue(inst, inst_seq_id, speculative)

    def issue_impl(self, inst, inst_seq_id, speculative):
        if inst["opcode"] not in ["lw", "sw"]:
            raise Exception("LoadStoreQueue only accepts Load/Store instructions")
        vacant_lsq_entry = self.entries[self.issue_ptr]
        vacant_lsq_entry.seq_id = inst_seq_id
        vacant_lsq_entry.Speculative = speculative
        vacant_lsq_entry.Store = if inst["arg1"] == "sw"
        vacant_lsq_entry.Value = None; vacant_lsq_entry.ValidV = None
        vacant_lsq_entry.Address = None; vacant_lsq_entry.ValidA = None
        return True

    class LSQViolation(Exception):
        def __init__(self, message, load_seq_id):
            super(LSQViolation, self).__init__(message)
            self.inst_seq_id = load_seq_id

    def commit(self, STACK):
        return super(LoadStoreQueue, self).commit(STACK)

    def commit_impl(self, STACK):
        retire_lsq_entry = self.entries[self.commit_ptr]
        if not retire_lsq_entry.Valid or retire_lsq_entry.Speculative
            return False
        if retire_lsq_entry.Store:
            STACK[retire_lsq_entry.Address] = retire_lsq_entry.Value
            return True
        else:
            if retire_lsq_entry.Value != STACK[retire_lsq_entry.Address]:
                raise LSQViolation("LSQViolation", retire_lsq_entry.seq_id)
            else:
                return True

class CommonDataBus(object):

    def __init__(self, RSs, ROB, LSQ):
        self.RSs = RSs
        self.ROB = ROB
        self.LSQ = LSQ

    def writeback(self, writeback):
        (inst_seq_id, ttype, dest, res) = writeback
        if ttype not in ["register", "load", "store"]:
            raise Exception("CDB cannot writeback branch/jump instructions")
        # Fill ReservationStation Entries
        if ttype == "register":
            for rs in RSs:
                rs.writeback_rtype(writeback)
        # Fill ROB entries for rtype instructions
        if ttype == "register":
            self.ROB.writeback_rtype(inst_seq_id, value=res)
        # Fill LSQ entries for load/store instructions
        if ttype == "load":
            self.LSQ.writeback_load(inst_seq_id, address=res[0], value=res[1])
        if ttype == "store":
            self.LSQ.writeback_store(inst_seq_id, address=res)
        # Notify
        if ttype == "branch":
            self.ROB.writeback_branch(inst_seq_id, value=res)
            self.LSQ.writeback_branch(inst_seq_id, value=res)

