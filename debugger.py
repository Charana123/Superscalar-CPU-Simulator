import sys
from util import toString

class Debugger(object):
    def __init__(self, STATE, runCycle):
        self.STATE = STATE
        self.runCycle = runCycle

    def run(self):

        while True:
            cmd = sys.stdin.readline().strip().split(" ")
            cmd_op = cmd[0]
            cmd_args = cmd[1:]
            if cmd_op == "n":
                print("\n\n\n\n\n")
                self.runCycle()
                self.printAll()
            elif cmd_opd.startswith("pip"):
                self.printPipeline(cmd_args)
            elif cmd_op.startswith("prog"):
                self.printProgram(cmd_args)
            elif cmd_op.startswith("mem"):
                self.printStack(None)
            elif cmd_op.startswith("reg"):
                self.printRegisters()
            elif cmd_op.startswith("iq"):
                self.printInstructionQueue()
            elif cmd_op.startswith("rs"):
                self.printReservationStations()
            elif cmd_op.startswith("rat"):
                self.printRegisterAliasTable()
            elif cmd_op.startswith("rob"):
                self.printReorderBuffer()
            else:
                print("Invalid Command")


    # ========== PUBLIC FUNCTIONS =========================================
    def printAll(self):
        self.printProgram()
        self.printFetch()
        self.printDecode()
        self.printIssue()
        self.printDispatch()
        self.printExecute()
        self.printWriteback()
        self.printCommit()

    def printFetch(self):
        print "========= Fetch ========="
        print "### Fetches instruction placed in PIPELINE"
        print "Fetch Instruction: %s" % toString(self.STATE.PIPELINE["decode"])
        print "### Speculatively takes/doesnt-taken branch"
        self.printBTB()

    def printDecode(self):
        print "======== Decodes ========="
        print "### Decoded instruction placed in INSTRUCTION QUEUE"
        self.printInstructionQueue()

    def printIssue(self):
        print "======== Issue ========"
        print "### Issued instruction placed in RESERVATION STATIONS"
        self.printReservationStations()
        print "### RAT after issue"
        self.printRegisterAliasTable()

    def printDispatch(self):
        print "========= Dispatch ========"
        print "### Dispatched instruction put into EXECUTION UNITS"
        self.printExecutionUnits()

    def printExecute(self):
        print "========= Execute ========"
        print "### Executed instructions that aren't finished are retained in the EXECUTION UNITS"
        self.printExecutionUnits()
        print "### Instructions that finish this cycle are placed in the PIPELINE"
        print "Writeback Instruction: %s" % toString(self.STATE.PIPELINE["writeback"])

    def printWriteback(self):
        print "========= Writeback ========"
        print "### Results of instructions are written back into RESERVATION STATION entries"
        self.printReservationStations()
        print "### And also into the assosiated ROB entry"
        self.printReorderBuffer()
        self.printLoadStoreBuffer()

    def printCommit(self):
        print "========= Commit ========"
        print "### Instruction to commit are removed from ROB"
        self.printReorderBuffer()
        self.printLoadStoreBuffer()
        print "### Write to global architectural state: STACK and REGISTER"
        self.printStack(None)
        self.printRegisters()


    # ========== INTERNAL FUNCTIONS =========================================
    def printProgram(self):
        print "========= PROGRAM =========="
        print toString(self.STATE.PROGRAM)
        print "============================"

    def printStack(self, cmd_args):
        if cmd_args is not None:
            if len(cmd_args) == 1:
                [ind] = cmd_args
                print "Stack[%d]: %s" % (ind, toString(self.STATE.STACK[ind]))
            if len(cmd_args) == 2:
                [start, end] = cmd_args
                print "Stack[%d:%d]: %s" % (start, end, toString(self.STATE.STACK[start:end]))
        else:
            print "Stack: %s" % toString(self.STATE.STACK)

    def printRegisters(self):
        print "Register File: %s" % toString(self.STATE.REGISTER_FILE)

    def printInstructionQueue(self):
        print "Instruction Queue: %s" % toString(self.STATE.INSTRUCTION_QUEUE)

    def printReservationStations(self):
        print "Busy - ALU RS: %s" % toString(self.STATE.ALU_RS)
        print "Busy - LSU RS: %s" % toString(self.STATE.LSU_RS)
        print "Busy - BU RS: %s" % toString(self.STATE.BU_RS)

    def printExecutionUnits(self):
        busy = lambda fus: filter(lambda fu: fu.OCCUPIED, fus)
        print "Busy - ALU: %s" % toString(busy(self.STATE.ALUs))
        print "Busy - LSU: %s" % toString(busy(self.STATE.LSUs))
        print "Busy - BU: %s" % toString(busy(self.STATE.BUs))

    def printRegisterAliasTable(self):
        print "RAT: %s" % toString(self.STATE.RAT)

    def printReorderBuffer(self):
        print "ROB: %s" % toString(self.STATE.ROB)

    def printLoadStoreBuffer(self):
        print "LSQ: %s" % toString(self.STATE.LSQ)

    def printBTB(self):
        print "BTB: %s" % toString(self.STATE.BTB)














