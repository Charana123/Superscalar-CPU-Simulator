main:
# Load s0,s1,s2 with the heap addresses of vectors a,b,c
li $s0 c100
li $s1 c200
li $s2 c300
# Copy vector length into s2
li $s3 c4
# Loop max
li $s5 c64
j loop

init:
# int i = 0
li $s4 c0
# check loop condition
bge $s4 $s5 setup
j initloop

initloop:
# a[i] = i; b[i] = i
vli $vr0 $s4
vstore $vr0 $s0 $s4
vstore $vr0 $s1 $s4
# i++
addi $s4 $s4 c4
bge $s4 $s5 setup
j initloop

setup:
# int i = 0
li $s4 c0
# check loop condition
bge $s4 $s5 setup
j loop


# for (int i = 0; i < N; j++){
#   c[i] = b[i] + 5 * a[i];
# }
loop:
# move scalar '5' to vector register 'vr1'
vli $vr0 c5
# load b[j] for vector length
vload $vr1 $s1 $s4
# compute scalar*b[j] for vector length
# i.e. multiply vector register holding 'scalar' into vector memory locations holding b[j] and place result in another vector register
vmul $vr1 $vr1 $vr0
# compute a[j] + scalar*b[j] for the vector length
# i.e. add vector register holding 'scalar*b[j]' into vector memory locations holding a[j] and place result in another vector register
vload $vr2 $s0 $s4
vadd $vr2 $vr2 $vr1
# store the result of a[j] + scalar*b[j] in c[j]
vstore $vr2 $s2 $s4
# Increment loop/vector counter
add $s4 $s4 $s3
# Compare and jump
bge $s4 $s5 exit
j loop

exit:
# Set return and return
move $v0 $s1
jr $ra
