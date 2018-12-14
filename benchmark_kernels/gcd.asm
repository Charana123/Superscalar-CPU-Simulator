main:
# load (x,y) of gcd(x,y) into $s1 and $s2 respectively
li $s1 c8
li $s2 c4
# check loop condition
beq $s2 $zero exit
# start loop
j loop

loop:
# $s3 = arg 1 % arg2
mod $s3 $s1 $s2
# set arg1 to arg2
move $s1 $s2
# set arg2 to remainder
move $s2 $s3
# exit if $s3 == 0
beq $s3 $zero exit
# recursive call
j loop

exit:
# Set return and return
# gcd(x, y) found in $s1
move $v0 $s1
jr $ra















