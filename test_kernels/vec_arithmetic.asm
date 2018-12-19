main:
vli $vr0 c10
# t0 = 10
vli $vr1 c5
# t0 = 10; t1 = 5
vadd $vr2 $vr0 $vr1
# t0 = 10; t1 = 5; t2 = 15
vaddi $vr0 $vr0 c5
# t0 = 15; t1 = 5; t2 = 15
vsubi $vr0 $vr0 $vr1
# t0 = 10; t1 = 5; t2 = 15
vsubi $vr0 $vr0 c15
# t0 = -5; t1 = 5; t2 = 15
vmul $vr0 $vr0 $vr1
# t0 = -25; t1 = 5; t2 = 15
vdiv $vr2 $vr2 $vr1
# t0 = -25; t1 = 5; t2 = 3
li $v0 c0
# set return code 0
jr $ra
# return

