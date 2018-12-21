# dot(int *a, int *b, int *c, int N)
main:
# load (a,b,c) of dot(a,b,c) into $s0, $s1, $s2 respectively
li $s0 c100
li $s1 c200
li $s2 c300
# int dim = 8
li $s3 c4
# int N = 64 (dim * dim)
mul $s7 $s3 $s3
j init

init:
# int temp = 0
li $t0 c0
j initloop

initloop:
# a[i] = i; b[i] = i
sw $t0 $s0 $t0
sw $t0 $s1 $t0
# temp++; if temp > N; break
addi $t0 $t0 c1
bge $t0 $s7 setup
j initloop

setup:
# int i = 0; int j = 0; int k = 0
li $s4 c0
li $s5 c0
li $s6 c0
# k = 0
li $s6 c0
# sum = 0
li $t0 c0
# check loop condition
bge $s4 $s3 exit
bge $s5 $s3 exit
j matmul

# for(int i = 0; i <= N; i++){
#   for(int j = 0; j <= N; j++){
#       int sum = 0
#       for(int k = 0; k <= N; i++){
#           sum += a[i*N+k] * b[k*N+j]
#       }
#       c[i*N+j] = sum
#   }
# }
matmul:
# load a[i*N+k]
mul $t2 $s4 $s3
add $t2 $t2 $s6
lw $t3 $s0 $t2
# load b[k*N+j]
mul $t2 $s6 $s3
add $t2 $t2 $s5
lw $t4 $s1 $t2
# compute and store sum += a[i*N+k] * b[k*N+j]
mul $t5 $t4 $t3
add $t0 $t0 $t5
# k++; k <= N
addi $s6 $s6 c1
bge $s6 $s3 loopj
# loop back
j matmul

loopj:
# k = 0
li $s6 c0
# c[i*N+j] = sum
mul $t2 $s4 $s3
add $t2 $t2 $s5
sw $t0 $s2 $t2
# sum = 0
li $t0 c0
# j++; j <= N
addi $s5 $s5 c1
bge $s5 $s3 loopi
j matmul

loopi:
# j = 0
li $s5 c0
# i++; i <= N
addi $s4 $s4 c1
bge $s4 $s3 exit
j loopj

exit:
# Set return and return
li $v0 c0
jr $ra















