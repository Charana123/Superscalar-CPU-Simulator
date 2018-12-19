main:
vli $vr0 c50
# t0 == 50
vstore $vr0 $zero c10
# t0 == 50; m10 == 50
vload $vr1 $zero c10
# t0 == 50; t1 == 50; m0 == 50
li $v0 c0
# set return code 0
jr $ra
# return

