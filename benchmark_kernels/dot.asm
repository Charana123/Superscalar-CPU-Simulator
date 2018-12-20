# dot(int *a, int *b, int *c, int N)
main:
# load (a,b,c) of dot(a,b,c) into $s0, $s1, $s2 respectively
li $s0 c100
li $s1 c200
li $s2 c300
# int N = 64
li $s3 c64
j init

init:
# int i = 0
li $s4 c0
# check loop condition
bge $s4 $s3 exit
j initloop

initloop:
# a[i] = i; b[i] = i
sw $s4 $s0 $s4
sw $s4 $s1 $s4
# i++
addi $s4 $s4 c1
bge $s4 $s3 setup
j initloop

setup:
# int i = 0
li $s4 c0
# check loop condition
bge $s4 $s3 exit
j loop


# for(int i = N; i <= 0; i--){
#   c[i] = a[i] * b[i]
# }
loop:
# c[i] = a[i] * b[i]
lw $t0 $s0 $s4
lw $t1 $s1 $s4
mul $t2 $t1 $t0
sw $t2 $s2 $s4
# i--; i >= 0
addi $s4 $s4 c1
bge $s4 $s3 exit
# loop back
j loop

exit:
# Set return and return
li $v0 c0
jr $ra

