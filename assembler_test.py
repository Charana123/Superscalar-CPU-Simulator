from assembler import readProgram
import unittest

class TestToProgram(unittest.TestCase):

    def test_readProgram(self):
        program = readProgram("./test_kernels/jump.asm")

        expected_program = [
            {"opcode": "jal", "arg1": 3, "arg2": -1, "arg3": -1},
            {"opcode": "addi", "arg1": "$v0", "arg2": "$zero", "arg3": "c10"},
            {"opcode": "syscall", "arg1": -1, "arg2": -1, "arg3": -1},
            "main:",
            {"opcode": "sw", "arg1": "$ra", "arg2": "$sp", "arg3": "c0" },
            {"opcode": "addi", "arg1": "$sp", "arg2": "$sp", "arg3": "c1"},
            {"opcode": "jal", "arg1": 12, "arg2": -1, "arg3": -1},
            {"opcode": "li", "arg1": "$t1", "arg2": "c10", "arg3": -1},
            {"opcode": "subi", "arg1": "$sp", "arg2": "$sp", "arg3": "c1"},
            {"opcode": "lw", "arg1": "$ra", "arg2": "$sp", "arg3": "c0" },
            {"opcode": "li", "arg1": "$v0", "arg2": "c0", "arg3": -1},
            {"opcode": "jr", "arg1": "$ra", "arg2": -1, "arg3": -1},
            "label:",
            {"opcode": "li", "arg1": "$t0", "arg2": "c5", "arg3": -1},
            {"opcode": "li", "arg1": "$v0", "arg2": "c0", "arg3": -1},
            {"opcode": "jr", "arg1": "$ra", "arg2": -1, "arg3": -1}
        ]

        self.assertEqual(len(expected_program), len(program))
        for exp, out in list(zip(expected_program, program)):
            if cmp(exp, out) != 0:
                print exp
                print out
            self.assertEqual(cmp(exp, out), 0)

if __name__ == '__main__':
    unittest.main()




