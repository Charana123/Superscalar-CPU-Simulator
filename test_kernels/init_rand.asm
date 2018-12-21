main:
# address of array
li $s0 c100
# int N = 10
li $s2 c50
j init

init:
# int i = 0
li $s1 c0
# check loop condition
bge $s1 $s2 exit
j initloop

initloop:
# syscall(44) - put random number in $f0
li $v0 c44
syscall
# a[i] = random value
sw $f0 $s0 $s1
# i++
addi $s1 $s1 c1
bge $s1 $s2 exit
j initloop

exit:
# Set return and return
li $v0 c0
jr $ra
