from util import toString
from functional import first, anyy, alll, generate
from consts import REGISTER_MNEMONICS, VECTOR_REGISTER_MNEMONICS
from consts import ALU_OPCODES, MUL_OPCODES, DIV_OPCODES, LOAD_STORE_OPCODES, COND_BRANCH_OPCODES, VALU_OPCODES, VMUL_OPCODES, VDIV_OPCODES, VLSU_OPCODES, VOTHER_OPCODES


class InstructionQueue(object):
    def __init__(self):
        self.flush()

    def flush(self):
        self.instruction_queue = []

    def __str__(self):
        return toString(self.instruction_queue)

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
            self.inst_seq_id = None

        def __str__(self):
            return toString({
                "valid": self.Valid,
                "pending": self.Pending,
                "inst_seq_id": self.inst_seq_id
            })

        def __repr__(self):
            return self.__str__()

        def issue(self, inst_seq_id):
            self.Valid = False
            self.Pending = True
            self.inst_seq_id = inst_seq_id

        def commit(self):
            # RAT entry becomes valid when ROB entry is commited
            # If valid is true, reservation stations can read directly
            self.Valid = True

        def writeback(self):
            # RAT entry, pending becomes false when value commited to ROB entry
            # if pending is false, reservation stations can read directly from ROB
            self.Pending = False

    def __init__(self):
        self.flush()

    def __str__(self):
        invalid_entries = filter(lambda (key, val): not val.Valid, self.entries.items() + self.vector_entries.items())
        return toString(invalid_entries)

    def flush(self):
        self.entries = dict([(key, self.RegisterAliasTableEntry()) for key in REGISTER_MNEMONICS.keys()])
        self.vector_entries = dict([(key, self.RegisterAliasTableEntry()) for key in VECTOR_REGISTER_MNEMONICS.keys()])

    def __getitem__(self, key):
        if key[1:3] == 'vr':
            return self.vector_entries[key]
        else:
            return self.entries[key]

    def issue(self, inst):
        if inst["opcode"] in ALU_OPCODES + MUL_OPCODES + DIV_OPCODES + ["lw"]:
            dest_reg = inst["arg1"]
            inst_seq_id = inst["inst_seq_id"]
            self.entries[dest_reg].issue(inst_seq_id)
        if inst["opcode"] in VOTHER_OPCODES + VALU_OPCODES + VMUL_OPCODES + VDIV_OPCODES + ["vload"]:
            dest_reg = inst["arg1"]
            inst_seq_id = inst["inst_seq_id"]
            self.vector_entries[dest_reg].issue(inst_seq_id)
        if inst["opcode"] == "jal":
            inst_seq_id = inst["inst_seq_id"]
            self.entries["$ra"].issue(inst_seq_id)

    def commit(self, inst_seq_id):
        dependant_entries = [entry for entry in self.entries.items() + self.vector_entries.items() if entry[1].inst_seq_id == inst_seq_id]
        for entry in dependant_entries:
            entry[1].commit()

    def writeback(self, inst_seq_id):
        dependant_entries = [entry for entry in self.entries.items() + self.vector_entries.items() if entry[1].inst_seq_id == inst_seq_id]
        for entry in dependant_entries:
            entry[1].writeback()


class ReseravationStation(object):
    class ReservationStationEntry(object):
        def __init__(self):
            self.inst_seq_id = None  # Cycle the instruction was issued (for oldest dispatched first heuristic)
            self.pc = None
            self.Busy = False
            self.Op = None
            # entries of the form - (rob_entry, value, valid, label)
            self.Values = []
            # entries of the form - (tag, label)
            self.Tags = []

        def __str__(self):
            return toString({
                "inst_seq_id": self.inst_seq_id,
                "pc": self.pc,
                "busy": self.Busy,
                "op": self.Op,
                "values": self.Values,
                "tags": self.Tags
            })

        def __repr__(self):
            return self.__str__()

        def get_inst_seq_id(self):
            return self.inst_seq_id

        def issue(self, STATE, inst, inst_seq_id):
            self.inst_seq_id = inst["inst_seq_id"]
            self.pc = inst["pc"]
            self.Busy = True
            self.Op = inst["opcode"]

            if inst["opcode"] == "noop":
                tags = []
                values = []
            if inst["opcode"] == "jr":
                tags = []
                values = [("$ra", "label")]
            if inst["opcode"] == "jal":
                tags = [(inst["pc"], "pc")]
                values = []
            if inst["opcode"] in ALU_OPCODES + MUL_OPCODES + DIV_OPCODES:
                tags = [(inst["arg1"], "dest")]
                values = [(inst["arg2"], "src1"), (inst["arg3"], "src2")]
            if inst["opcode"] in VALU_OPCODES + VMUL_OPCODES + VDIV_OPCODES:
                tags = [(inst["arg1"], "dest")]
                values = [(inst["arg2"], "src1"), (inst["arg3"], "src2")]
            if inst["opcode"] == "vblend":
                tags = [(inst["arg1"], "dest")]
                values = [(inst["arg2"], "src1"), (inst["arg3"], "src2"), (inst["arg4"], "mask")]
            if inst["opcode"] == "lw":
                tags = [(inst["arg1"], "dest")]
                values = [(inst["arg2"], "add1"), (inst["arg3"], "add2")]
            if inst["opcode"] == "sw":
                tags = []
                values = [(inst["arg1"], "src"), (inst["arg2"], "add1"), (inst["arg3"], "add2")]
            if inst["opcode"] == "vload":
                tags = [(inst["arg1"], "dest")]
                values = [(inst["arg2"], "add1"), (inst["arg3"], "add2")]
            if inst["opcode"] == "vstore":
                tags = []
                values = [(inst["arg1"], "src"), (inst["arg2"], "add1"), (inst["arg3"], "add2")]
            if inst["opcode"] in COND_BRANCH_OPCODES:
                tags = [(inst["arg3"], "label")]
                values = [(inst["arg1"], "src1"), (inst["arg2"], "src2")]
            if inst["opcode"] == "syscall":
                tags = []
                values = [("$v0", "syscall_type")]
            self.Tags = tags

            def evaluateValueEntries(value):
                (value_src, label) = value
                if value_src[0] == 'c':
                    value = int(value_src[1:])
                    return (value, True, label)
                if value_src[0] == '$':
                    RAT_Entry = STATE.RAT[value_src]
                    if RAT_Entry.Valid:
                        print(label, "one")
                        # Read from register file
			value = STATE.getRegisterValue(value_src)
                        return (value, True, label)
                    if not RAT_Entry.Valid and not RAT_Entry.Pending:
                        print(label, "two")
                        # Read from ROB using ROB_Entry
                        value = STATE.ROB.getValue(STATE, RAT_Entry.inst_seq_id)
                        return (value, True, label)
                    else:
                        print(label, "three")
                        # Map to ROB entry
                        return (RAT_Entry.inst_seq_id, False, label)

            self.Values = map(evaluateValueEntries, values)

        def dispatch(self, STATE, FU):
            result = {"inst_seq_id": self.inst_seq_id, "pc": self.pc, "opcode": self.Op}
            def insert(acc, label, value_tag):
                acc[label] = value_tag
                return acc
            result = reduce(lambda acc, (value, _, label): insert(acc, label, value), self.Values, result)
            result = reduce(lambda acc, (tag, label): insert(acc, label, tag), self.Tags, result)
            self.Busy = False
            FU.dispatch(STATE, result)

        def writeback_rtype_or_load(self, STATE, inst_seq_id, val):
            def writeback_update(value_entry):
                (value_src, valid, label) = value_entry
                if not valid and value_src == inst_seq_id:
                    return (val, True, label)
                else:
                    return value_entry
            self.Values = map(writeback_update, self.Values)

        def isReady(self):
            return alll(lambda (_, valid, __): valid, self.Values)

    # =========== Reservation Station Methods ===============================
    def __init__(self, functional_units, size=None):
        self.ttype = functional_units[0].ttype
        if size is None:
            self.size = len(functional_units)
        else:
            self.size = size
        self.functional_units = functional_units
        self.flush()

    def __str__(self):
        busy = lambda rs_entries: filter(lambda rs_entry: rs_entry.Busy, rs_entries)
        return toString(busy(self.RSEntries))

    def freeRSAvailable(self):
        notBusy = lambda rs_entries: filter(lambda rs_entry: not rs_entry.Busy, rs_entries)
        return len(notBusy(self.RSEntries)) > 0

    def flush(self):
        self.RSEntries = generate(ReseravationStation.ReservationStationEntry, self.size)

    def findRSEntry(self, inst_seq_id):
        return first(lambda rs: rs.get_inst_seq_id() == inst_seq_id, self.RSEntries)

    def dispatch(self, STATE):
        # Check if any functional/execution units are available to dispatch
        FU = first(lambda fu: not fu.isOccupied(STATE), self.functional_units)
        if FU is None:
            return
        # Filter all RS Entries whos instruction is ready to be dispatched
        readyRSIDS = [rs_entry.get_inst_seq_id() for rs_entry in self.RSEntries if rs_entry.Busy and rs_entry.isReady()]
        if len(readyRSIDS) == 0:
            return
        # Find oldest RS Entry and dispatch to appropriate FU
        oldestRSID = reduce(lambda oldest_inst_seq_id, inst_seq_id: min(oldest_inst_seq_id, inst_seq_id), readyRSIDS)
        oldestRS = self.findRSEntry(oldestRSID)
        # Reset RS entry
        oldestRS.dispatch(STATE, FU)

    def issue(self, STATE, inst):
        freeRSs = filter(lambda rs_entry: not rs_entry.Busy, self.RSEntries)
        if len(freeRSs) == 0:
            return False
        freeRSs[0].issue(STATE, inst, inst["inst_seq_id"])
        return True

    def writeback_rtype_or_load(self, STATE, inst_seq_id, val):
        # For each RS entry, resolve unresolved operands (value entries) whos value correspond to the writeback of the current instruction
        for rs_entry in self.RSEntries:
            rs_entry.writeback_rtype_or_load(STATE, inst_seq_id, val)











