# int main () {
#
# 	int i;
# 	int a[3] = {1,2,3};
# 	int b[3] = {1,2,3};
# 	int c[3];
# 	for(i = 0; i < 3; i++){
# 		c[i] = b[i] + a[i];
# 	}
# }

main:
# int i = 0
li $s0 c0
li $s4 c3
# int a[3] = {1,2,3}
li $t0 c1
li $t1 c2
li $t2 c3
move $s1 $sp
sw $t0 $sp c0
sw $t1 $sp c1
sw $t2 $sp c2
addi $sp $sp c3
# int b[3] = {1,2,3}
move $s2 $sp
sw $t0 $sp c0
sw $t1 $sp c1
sw $t2 $sp c2
addi $sp $sp c3
# int c[3]
move $s3 $sp
addi $sp $sp c3
# jump to for loop
j loop

loop:
lw $t0 $s1 $s0
lw $t1 $s2 $s0
addi $t2 $t0 $t1
sw $t2 $s3 $s0
addi $s0 $s0 c1
bne $s0 $s4 loop
j exit

exit:
# return
jr $ra
