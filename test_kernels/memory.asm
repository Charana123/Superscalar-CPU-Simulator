main:
li $t0 c50
# t0 == 50
sw $t0 $zero c0
# t0 == 50; m0 == 50
lw $t1 $zero c0
# t0 == 50; t1 == 50; m0 == 50
addi $t2 $t1 c5
# t2 == 55; t1 == 50; t0 == 50; m0 == 50
li $v0 c0
# set return code 0
jr $ra
# return
