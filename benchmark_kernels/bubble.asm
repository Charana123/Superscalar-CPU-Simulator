main:
# address of array
li $s0 c100
# int N = 10
li $s3 c10
j init

init:
# int i = 0
li $s1 c0
# check loop condition
bge $s1 $s3 exit
j initloop

initloop:
# syscall(44) - put random number in $f0
li $v0 c44
syscall
# a[i] = random value
sw $f0 $s0 $s1
# i++
addi $s1 $s1 c1
bge $s1 $s3 setup
j initloop

setup:
# int c = 0; int d = 0;
li $s1 c0
li $s2 c0
# check c <= N -1
subi $t1 $s3 c1
bge $s1 $t1 exit
# check d <= N - 1 - c
subi $t2 $t1 $s1
bge $s2 $t2 exit
j bubble

# for(int c = 0; i <= N-1; i++){
#   for(int d = 0; j <= N-1-c; j++){
#       if a[d] > a[d+1]:
#           tmp = a[d+1]
#           a[d+1] = a[d]
#           a[d] = tmp
#       }
#   }
# }
bubble:
# load a[d] and a[d+1]
lw $t1 $s0 $s2
addi $t2 $s2 c1
lw $t3 $s0 $t2
# swap a[d+i] and a[d]
bgt $t1 $t3 else
sw $t3 $s0 $s2
sw $t1 $s0 $t2
addi $s5 $s5 c1
# d++
addi $s2 $s2 c1
# check d <= N - 1 - c
subi $t1 $s3 c1
subi $t2 $t1 $s1
bge $s2 $t2 loopi
# loop break
j bubble

else:
# d++
addi $s2 $s2 c1
# check d <= N - 1 - c
subi $t1 $s3 c1
subi $t2 $t1 $s1
bge $s2 $t2 loopi
# loop break
j bubble

loopi:
# j = 0
li $s2 c0
# i++;
addi $s1 $s1 c1
# check i <= N - 1
subi $t1 $s3 c1
bge $s1 $s1 exit
j bubble

exit:
# Set return and return
li $v0 c0
jr $ra
















