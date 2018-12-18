main:
# Load s0,s1,s2 with the heap addresses of vectors a,b,c
li $s0 c0
li $s1 c40
li $s2 c80
# Copy vector length into s2
li $s3 c4
# Loop counter
li $s4 c0
# Loop max
li $s5 c100
j loop

# for(int i = 0; i < 100; i++){
#    c[i] = a[i] == b[i] ? a[i] : b[i];
# }


loop:
# load a and b for vector length
vload $vr0 $s0 $s4
vload $vr1 $s1 $s4
# Compute vector mask
vcmpeq $vr0 $vr1 $vr2
# Copy based on mask
vblend $vr0 $vr1 $vr2 $vr3
# Store to c
vstore $vr3 $s2 $s4
# Increment loop/vector counter
add $s4 $s4 $s3
# Compare and jump
bge $s4 $s5 exit
j loop

exit:
# Set return and return
move $v0 $s1
jr $ra








