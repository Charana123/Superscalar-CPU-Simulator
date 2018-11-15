main:
li $t0 c10
# t0 = 10
li $t1 c5
# t0 = 10; t1 = 5
add $t2 $t0 $t1
# t0 = 10; t1 = 5; t2 = 15
addi $t0 $t0 c5
# t0 = 15; t1 = 5; t2 = 15
sub $t0 $t0 $t1
# t0 = 10; t1 = 5; t2 = 15
subi $t0 $t0 c15
# t0 = -5; t1 = 5; t2 = 15
mul $t0 $t0 $t1
# t0 = -25; t1 = 5; t2 = 15
div $t2 $t1
mflo $t2
# t0 = -25; t1 = 5; t2 = 3
move $t1 $t2
# t0 = -25; t1 = 3; t2 = 3
li $v0 c0
# set return code 0
jr $ra
# return
