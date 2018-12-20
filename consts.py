
REGISTER_MNEMONICS = {
    "$zero": 0,
    "$at": 1,
    "$v0": 2, "$v1": 3,  # return value of sub-routine
    "$a0": 4, "$a1": 5, "$a2": 6, "$a3": 7,  # arguments to sub-routine
    "$t0": 8, "$t1": 9, "$t2": 10, "$t3": 11, "$t4": 12, "$t5": 13,
    "$t6": 14, "$t7": 15,  # temporary registers (not preserved across function calls)
    "$s0": 16, "$s1": 17, "$s2": 18, "$s3": 19, "$s4": 20, "$s5": 21, "$s6": 22, "$s7": 23,  # saved registers (preserved accross function calls i.e. stored on stack)
    "$t8": 24, "$t9": 25, "$k0": 26, "$k1": 27, "$gp": 28,  # global pointer (points to start "data" segment in memory
    "$sp": 29,  # stack pointer
    "$fp": 30,  # frame  pointer (used to store prior value of $sp before stack frame is pushed)
    "$ra": 31,  # return address (stores PC on jump and link instruction i.e. jal)
}

VECTOR_REGISTER_MNEMONICS = {
    "$vrzero": 0, "$vr0": 1, "$vr1": 2, "$vr2": 3, "$vr3": 4, "$vr4": 5, "$vr5": 6, "$vr6": 7, "$vr7": 8 # architectural vector registers
}

ALU_OPCODES = ["add", "addi", "sub", "subi"]
MUL_OPCODES = ["mul"]
DIV_OPCODES = ["div", "mod"]
LOAD_STORE_OPCODES = ["lw", "sw"]
COND_BRANCH_OPCODES = ["beq", "bne", "bgt", "bge", "blt", "ble"]
UNCOND_JUMP_OPCODES = ["j", "jal"]

VALU_OPCODES = ["vadd", "vaddi", "vsub", "vsubi", "vcmpeq", "vcmpgt", "vcmplt"]
VOTHER_OPCODES = ["vblend"]
VMUL_OPCODES = ["vmul"]
VDIV_OPCODES = ["vdiv"]
VLSU_OPCODES = ["vstore", "vload"]
VECTOR_LENGTH = 4

