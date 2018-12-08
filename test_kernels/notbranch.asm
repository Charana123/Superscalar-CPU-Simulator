main:
li $t0 c5
li $t1 c3
beq $t0 $t1 label1
j exit

label1:
li $s0 c1
j exit

exit:
li $v0 c0
jr $ra
