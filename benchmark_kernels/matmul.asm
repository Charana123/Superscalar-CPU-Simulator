# dot(int *a, int *b, int *c, int N)
main:
# load (a,b,c) of dot(a,b,c) into $s0, $s1, $s2 respectively
li $s0 c100
li $s1 c200
li $s2 c300
# int dim = 8
li $s3 c8
# int N = 64 (dim * dim)
mul $s6 $s3 $s3
j init

init:
# int temp = 0
li $t0 c0
j initloop

initloop:
# a[i] = i; b[i] = i
sw $s4 $s0 $t0
sw $s4 $s1 $t0
# temp++; if temp > N; break
addi $t0 $t0 c1
bge $t0 $s6 setup
j initloop

setup:
# int i = 0; int j = 0
li $s4 c0
li $s5 c0
# check loop condition
bge $s4 $s3 exit
bge $s5 $s3 exit
j loop

# for(int i = 0; i <= N; i++){
#   for(int j = 0; j <= N; j++){
#       int sum = 0
#       for(int k = 0; k <= N; i++){
#           sum += a[i*N+k] * b[k*N+j]
#       }
#       c[i*N+j] = sum
#   }
# }
loop:
# sum = 0
li $t0 c0
# k = 0
li $t1 c0
# load a[i*N+k]
mul $t2 $s4 $s3
add $t2 $t2 $t1
lw $s0 $s1 $s4
# load b[k*N+j]
mul $t2 $t1 $s3
add $t2 $t2 $t5
lw $s1 $s2 $s5
# compute and store sum += a[i*N+k] * b[k*N+j]
mul $

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















