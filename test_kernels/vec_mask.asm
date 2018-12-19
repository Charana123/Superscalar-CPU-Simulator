main:
vli $vr0 c6
vli $vr1 c5
vcmplt $vr2 $vr0 $vr1
vblend $vr3 $vr0 $vr1 $vr2
li $v0 c0
jr $ra

