main:
li $t0 c5
li $t1 c5
beq $t0 $t1 label1

label1:
li $s0 c1
# s0 = 1
j label1jump

label1jump:
bge $t0 $t1 label2
j exit

label2:
li $s1 c2
# s1 = 2, s0 = 1
j label2jump

label2jump:
ble $t0 $t1 label3
j exit

label3:
li $s2 c3
# s2 = 3, s1 = 2, s0 = 1
j label3jump

label3jump:
li $t0 c10
li $t1 c5
bne $t0 $t1 label4
j exit

label4:
li $s3 c4
# s3 = 4, s2 = 3, s1 = 2, s0 = 1
j label4jump

label4jump:
bgt $t0 $t1 label5
j exit

label5:
li $s4 c5
# s4 = 5, s3 = 4, s2 = 3, s1 = 2, s0 = 1
j label5jump

label5jump:
li $t0 c5
li $t1 c10
blt $t0 $t1 label6
j exit

label6:
li $s5 c6
# s5 = 6, s4 = 5, s3 = 4, s2 = 3, s1 = 2, s0 = 1
# Set return to 0 and return from main
li $v0 c0
jr $ra

exit:
# Set return to 1 and return from main
li $v0 c1
jr $ra




