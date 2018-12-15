from util import toString
from functional import first, generate
from branch_prediction import getLatestBranchHistory, getBTIAC
from consts import REGISTER_MNEMONICS, RTYPE_OPCODES, STORE_OPCODES, LOAD_OPCODES, COND_BRANCH_OPCODES
import abc


class CircularBuffer(object):

    def __init__(self, size):
        self.size = size
        self.flush()

    def flush(self):
        self.issue_ptr = 0
        self.commit_ptr = 0
        self.EMPTY = True
        self.FULL = False

    def issue(self, STATE, inst):
        if self.FULL:
            return False
        ok = self.issue_impl(STATE, inst)
        if ok:
            self.issue_ptr = (self.issue_ptr + 1) % self.size
            # ROB cannot be empty if an entry has been issued
            self.EMPTY = False
            # If after a issue, the issue_ptr points to the commit_ptr, the buffer is full
            if self.issue_ptr == self.commit_ptr:
                self.FULL = True
        return ok

    @abc.abstractmethod
    def issue_impl(self, STATE, inst):
        pass

    def commit(self, STATE):
        if self.EMPTY:
            return False
        ok = self.commit_impl(STATE)
        if ok:
            self.commit_ptr = (self.commit_ptr + 1) % self.size
            # ROB cannot be full if an entry has been commited
            self.FULL = False
            # If after a commit, the commit_ptr points to the issue_ptr, the buffer is empty
            if self.issue_ptr == self.commit_ptr:
                self.EMPTY = True
        return ok

    @abc.abstractmethod
    def commit_impl(self, STATE):
        pass


class ReorderBuffer(CircularBuffer):

    class ReorderBufferEntry(object):

        def __init__(self):
            self.inst_seq_id = None  # Sequence ID of instruction
            self.pc = None  # PC of instruction
            self.op_type = None  # To distinguish rtypes, loads, stores, jumps and branches
            self.Valid = None  # Whether there exists a valid value in the ROB Entry
            self.Value = None  # The computed value of the instruction that must be written to program state
            self.Areg = None  # Architectural register the value must be written to

        def __str__(self):
            return toString({
                "inst_seq_id": self.inst_seq_id,
                "pc": self.pc,
                "op_type": self.op_type,
                "valid": self.Valid,
                "value": self.Value,
                "Areg": self.Areg
            })

        def __repr__(self):
            return self.__str__()

    def __init__(self, size):
        super(ReorderBuffer, self).__init__(size)
        self.entries = generate(ReorderBuffer.ReorderBufferEntry, self.size)

    def flush(self):
        super(ReorderBuffer, self).flush()

    def __str__(self):
        busy_entries = None
        if self.EMPTY:
            busy_entries = "ROB is Empty"
        if self.FULL:
            busy_entries = "ROB is Full"
        if self.issue_ptr > self.commit_ptr:
            busy_entries = self.entries[self.commit_ptr: self.issue_ptr]
        if self.issue_ptr < self.commit_ptr:
            busy_entries = self.entries[self.commit_ptr: self.size] + self.entries[:self.issue_ptr]
        return toString(busy_entries)

    def findROBEntry(self, inst_seq_id):
        return first(lambda entry: entry.inst_seq_id == inst_seq_id, self.entries)

    def getValue(self, STATE, inst_seq_id):
        rob_entry = self.findROBEntry(inst_seq_id)
        if rob_entry.op_type == "load":
            lsq_entry = STATE.LSQ.findLSQEntry(inst_seq_id)
            return lsq_entry.Value
        else:
            return rob_entry.Value

    def writeback_rtype(self, inst_seq_id, value):
        entry = self.findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.Value = value

    def writeback_branch(self, inst_seq_id, correct_speculation):
        entry = self.findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.Value = 1 if correct_speculation else 0

    def writeback_syscall(self, inst_seq_id, syscall_type):
        entry = self.findROBEntry(inst_seq_id)
        entry.Valid = True
        entry.Value = syscall_type

    def issue_impl(self, STATE, inst):
        vacant_rob_entry = self.entries[self.issue_ptr]
        vacant_rob_entry.inst_seq_id = inst["inst_seq_id"]
        vacant_rob_entry.pc = inst["pc"]
        vacant_rob_entry.Valid = False
        vacant_rob_entry.Value = None
        print("inst[opcode]", inst["opcode"])
        if inst["opcode"] in RTYPE_OPCODES:
            vacant_rob_entry.op_type = "r_type"
            vacant_rob_entry.Areg = inst["arg1"]
        elif inst["opcode"] == "jal":
            vacant_rob_entry.op_type = "r_type"
            vacant_rob_entry.Areg = "$ra"
        elif inst["opcode"] in LOAD_OPCODES + STORE_OPCODES:
            STATE.LSQ.issue(STATE, inst)
            if inst["opcode"] == "lw":
                vacant_rob_entry.op_type = "load"
            if inst["opcode"] == "sw":
                vacant_rob_entry.op_type = "store"
        elif inst["opcode"] == "syscall":
            vacant_rob_entry.op_type = "syscall"
        elif inst["opcode"] in COND_BRANCH_OPCODES:
            vacant_rob_entry.op_type = "branch"
        elif inst["opcode"] in ["jr", "noop"]:
            vacant_rob_entry.op_type = "noop"
        else:
            print "cannot issue opcode: %s" % inst["opcode"]
            exit()
        return True

    def issue(self, STATE, inst):
        return super(ReorderBuffer, self).issue(STATE, inst)

    class PipelineFlush(Exception):
        def __init__(self):
            super(ReorderBuffer.PipelineFlush, self).__init__("Pipeline Flush")

    class SyscallExit(Exception):
        def __init__(self):
            super(ReorderBuffer.SyscallExit, self).__init__("SYSCALL Exit")

    def commit_impl(self, STATE):

        # Instruction is retired
        STATE.RETIRED_INSTRUCTIONS += 1

        retire_rob_entry = self.entries[self.commit_ptr]
        if retire_rob_entry.op_type in ["load", "store"]:
            try:
                ok = STATE.LSQ.commit(STATE)
                return ok
            except LoadStoreQueue.LSQViolation:
                print("LSQViolation")
                # Update PC
                STATE.PC = retire_rob_entry.pc
                # Unstall Pipeline
                STATE.PIPELINE_STALLED = False
                # Flush Pipeline
                STATE.PIPELINE = {
                    "decode": [],
                    "writeback": []
                }
                raise ReorderBuffer.PipelineFlush()
        if retire_rob_entry.op_type == "branch":
            if not retire_rob_entry.Valid:
                return False
            # The branch was incorrect predicted
            elif retire_rob_entry.Value == 0:
                # Update PC
                taken = getLatestBranchHistory(retire_rob_entry.pc, STATE)
                print("prediction fixed", taken)
                if taken:
                    TA, TI = getBTIAC(retire_rob_entry.pc, STATE)
                    STATE.PC = TA + 2
                    STATE.PIPELINE["decode"] = [TI]
                else:
                    STATE.PC = retire_rob_entry.pc + 1
                print("prediction fixed, pc: %d" % STATE.PC)
                # Unstall pipeline if stalled by a previous (but now flushed) instruction
                STATE.PIPELINE_STALLED = False
                # Flush pipeline
                STATE.PIPELINE["writeback"] = []
                raise ReorderBuffer.PipelineFlush()
            else:
                return True
        if retire_rob_entry.op_type == "r_type":
            if not retire_rob_entry.Valid:
                return False
            else:
                STATE.REGISTER_FILE[REGISTER_MNEMONICS[retire_rob_entry.Areg]] = retire_rob_entry.Value
                STATE.RAT.commit(retire_rob_entry.inst_seq_id)
                print "REGISTER_FILE[REGISTER_MNEMONICS[%s]] = %d" % (retire_rob_entry.Areg, retire_rob_entry.Value)
                return True
        if retire_rob_entry.op_type == "noop":
            return True
        if retire_rob_entry.op_type == "syscall":
            raise ReorderBuffer.SyscallExit

    def commit(self, STATE):
        return super(ReorderBuffer, self).commit(STATE)


class LoadStoreQueue(CircularBuffer):

    class LoadStoreQueueEntry(object):

        def __init__(self):
            self.inst_seq_id = None
            self.pc = None
            self.Store = None
            self.load_dest = None
            self.Address = None  # Address to (load from)/(store to)
            self.ValidA = False  # if address has been resolved
            self.Value = None  # Value (loaded from memory address)/(stored to memory from register)
            self.ValidV = False  # if value has been resolved

        def __str__(self):
            return toString({
                "inst_seq_id": self.inst_seq_id,
                "pc": self.pc,
                "store": self.Store,
                "load_dest": self.load_dest,
                "address": self.Address,
                "valid_address": self.ValidA,
                "value": self.Value,
                "valid_value": self.ValidV
            })

        def __repr__(self):
            return self.__str__()

    def __init__(self, size):
        super(LoadStoreQueue, self).__init__(size)
        self.entries = generate(LoadStoreQueue.LoadStoreQueueEntry, self.size)
        self.add_to_store_map = {}

    def __str__(self):
        busy_entries = None
        if self.EMPTY:
            busy_entries = "LSQ is Empty"
        if self.FULL:
            busy_entries = "LSQ is Full"
        if self.issue_ptr > self.commit_ptr:
            busy_entries = self.entries[self.commit_ptr: self.issue_ptr]
        if self.issue_ptr < self.commit_ptr:
            busy_entries = self.entries[self.commit_ptr: self.size] + self.entries[:self.issue_ptr]
        return toString(busy_entries)

    def flush(self):
        super(LoadStoreQueue, self).flush()

    def findLSQEntry(self, inst_seq_id):
        return first(lambda entry: entry.inst_seq_id == inst_seq_id, self.entries)

    def writeback_store(self, inst_seq_id, address, value):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.Address = address; lsq_entry.ValidA = True
        lsq_entry.Value = value; lsq_entry.ValidV = True
        # Create/Update memory - address to value mapping (store to load forwarding)
        self.add_to_store_map[address] = value

    def writeback_load(self, STATE, inst_seq_id, address):
        lsq_entry = self.findLSQEntry(inst_seq_id)
        lsq_entry.Address = address; lsq_entry.ValidA = True
        # Read from latest LSQ entry in preference to from cache (store to load forwarding)
        if address in self.add_to_store_map:
            lsq_entry.Value = self.add_to_store_map[address]
        else:
            lsq_entry.Value = STATE.STACK[address]
        lsq_entry.ValidV = True
        return lsq_entry.Value

    def issue(self, STATE, inst):
        return super(LoadStoreQueue, self).issue(STATE, inst)

    def issue_impl(self, STATE, inst):
        vacant_lsq_entry = self.entries[self.issue_ptr]
        vacant_lsq_entry.inst_seq_id = inst["inst_seq_id"]
        vacant_lsq_entry.Store = inst["opcode"] == "sw"
        vacant_lsq_entry.Value = None; vacant_lsq_entry.ValidV = None
        vacant_lsq_entry.Address = None; vacant_lsq_entry.ValidA = None
        vacant_lsq_entry.REGISTER_ADDRESS_STACK_COPY = list(STATE.REGISTER_ADDRESS_STACK)
        if not vacant_lsq_entry.Store:
            vacant_lsq_entry.load_dest = inst["arg1"]
        return True

    class LSQViolation(Exception):
        def __init__(self, message, load_seq_id):
            super(LoadStoreQueue.LSQViolation, self).__init__(message)
            self.inst_seq_id = load_seq_id

    def commit(self, STATE):
        return super(LoadStoreQueue, self).commit(STATE)

    def commit_impl(self, STATE):
        retire_lsq_entry = self.entries[self.commit_ptr]
        if not retire_lsq_entry.ValidA or not retire_lsq_entry.ValidV:
            return False
        if retire_lsq_entry.Store:
            STATE.STACK[retire_lsq_entry.Address] = retire_lsq_entry.Value
            print "STACK[%s] = %d" % (retire_lsq_entry.Address, retire_lsq_entry.Value)
            return True
        else:
            if retire_lsq_entry.Value != STATE.STACK[retire_lsq_entry.Address]:
                # Update Return Address Stack
                STATE.REGISTER_ADDRESS_STACK = retire_lsq_entry.REGISTER_ADDRESS_STACK_COPY
                raise LoadStoreQueue.LSQViolation("LSQViolation", retire_lsq_entry.inst_seq_id)
            else:
                # Update Load Register and RAT Entry
                STATE.REGISTER_FILE[REGISTER_MNEMONICS[retire_lsq_entry.load_dest]] = retire_lsq_entry.Value
                STATE.RAT.commit(retire_lsq_entry.inst_seq_id)
                return True


class CommonDataBus(object):

    def __init__(self, STATE):
        self.STATE = STATE

    def writeback(self, STATE, writeback):
        inst_seq_id = writeback["inst_seq_id"]
        ttype = writeback["ttype"]

        if ttype == "noop":
            pass
        if ttype == "syscall":
            syscall_type = writeback["syscall_type"]
            # Fill ROB entries of syscall instructions
            self.STATE.ROB.writeback_syscall(inst_seq_id, syscall_type)
        if ttype == "register":
            result = writeback["result"]
            # Fill ReservationStation Entries
            for rs in [self.STATE.ALU_RS, self.STATE.LSU_RS, self.STATE.BU_RS]:
                rs.writeback_rtype_or_load(STATE, inst_seq_id, result)
            # Fill ROB entries for rtype instructions
            self.STATE.ROB.writeback_rtype(inst_seq_id, result)
            # Pending = False, for RAT entries
            self.STATE.RAT.writeback(inst_seq_id)
        if ttype == "branch":
            correct_speculation = writeback["correct_speculation"]
            # Notify ROB branch entry
            self.STATE.ROB.writeback_branch(inst_seq_id, correct_speculation)
        # Fill LSQ entries for load/store instructions
        if ttype == "load":
            address = writeback["address"]
            value = self.STATE.LSQ.writeback_load(self.STATE, inst_seq_id, address)
            # Fill ReservationStation Entries
            for rs in [self.STATE.ALU_RS, self.STATE.LSU_RS, self.STATE.BU_RS]:
                rs.writeback_rtype_or_load(STATE, inst_seq_id, value)
            # Pending = False, for RAT entries
            self.STATE.RAT.writeback(inst_seq_id)
        if ttype == "store":
            address = writeback["address"]
            store_value = writeback["store_value"]
            self.STATE.LSQ.writeback_store(inst_seq_id, address, store_value)


















