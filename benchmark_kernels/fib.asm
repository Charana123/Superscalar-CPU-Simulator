# int main() {
# 	fib(4);
# }

# func main ()
main:
# Call fibonacci
li $a0 c2
# Save return and jump
sw $ra $sp c1
addi $sp $sp c1
jal fibonacci
# save sub-routine return value to a1
move $a1 $v0
# Restore return and return
subi $sp $sp c1
lw $ra $sp c0
jr $ra

# int fib(int n){
# 	if(n < 3) return 1;
# 	else return fib(n-1) + fib(n-1);
# }

# func fibonacci (int n)
fibonacci:
# Save register states
sw $s1 $sp c0
sw $s0 $sp c1
addi $sp $sp c2
# Load fib argument to $s0
move $s0 $a0
li $s2 c2
ble $s0 $s2 fib_base
# Save return
sw $ra $sp c0
addi $sp $sp c1
# compute f(n-1) + f(n-2)
subi $a0 $s0 c1
jal fibonacci
move $s1 $v0
subi $a0 $s0 c2
jal fibonacci
# Restore return and return
subi $sp $sp c1
lw $ra $sp c0
# Return from fib
j fib_return

fib_base:
# Restore register states
subi $sp $sp c2
lw $s1 $sp c0
lw $s0 $sp c1
# Return value for fib(2) == 1
li $v0 c1
# Return from fib
jr $ra

fib_return:
# save f(n-1) + f(n-2) in return register and return
add $v0 $s1 $v0
# Restore register states
subi $sp $sp c2
lw $s1 $sp c0
lw $s0 $sp c1
# Return from fib
jr $ra




