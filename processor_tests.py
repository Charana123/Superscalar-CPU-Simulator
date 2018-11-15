import processor
import consts
import unittest

class TestProcessor(unittest.TestCase):

    def readReg(self, reg_mnemonic):
        return processor.REGISTER_FILE[processor.REGISTER_MNEMONICS[reg_mnemonic]]

    def readStack(self, idx):
        return processor.STACK[idx]

    def test_arithmetic(self):
        processor.runProgram("./test_kernels/arithmetic.asm")
        print("reg_file", processor.REGISTER_FILE)
        self.assertEqual(self.readReg("$t0"), -25)
        self.assertEqual(self.readReg("$t1"), 3)
        self.assertEqual(self.readReg("$t2"), 3)

    def test_memory(self):
        processor.runProgram("./test_kernels/memory.asm")
        self.assertEqual(self.readReg("$t0"), 50)
        self.assertEqual(self.readReg("$t1"), 50)
        self.assertEqual(self.readReg("$t2"), 65536)

    def test_jump(self):
        processor.runProgram("./test_kernels/jump.asm")
        self.assertEqual(self.readReg("$t0"), 5)
        self.assertEqual(self.readReg("$t1"), 10)

    def test_branch(self):
        processor.runProgram("./test_kernels/branch.asm")
        self.assertEqual(self.readReg("$s0"), 1)
        self.assertEqual(self.readReg("$s1"), 2)
        self.assertEqual(self.readReg("$s2"), 3)
        self.assertEqual(self.readReg("$s3"), 4)
        self.assertEqual(self.readReg("$s4"), 5)
        self.assertEqual(self.readReg("$s5"), 6)

    def test_fib(self):
        processor.runProgram("./benchmark_kernels/fib.asm")
        self.assertEqual(self.readReg("$a1"), 3)

    def test_gcd(self):
        processor.runProgram("./benchmark_kernels/gcd.asm")
        self.assertEqual(self.readReg("$s1"), 4)

    def test_vec_add(self):
        processor.runProgram("./benchmark_kernels/vec_add.asm")
        vecadd_address = self.readReg("$s3")
        self.assertEqual(self.readStack(vecadd_address), 2)
        self.assertEqual(self.readStack(vecadd_address + 1), 4)
        self.assertEqual(self.readStack(vecadd_address + 2), 6)

if __name__ == '__main__':
    unittest.main()











