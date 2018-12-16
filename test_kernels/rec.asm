main:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# main
li $s0 c0
li $a0 c5
# jump to 'rec'
jal rec
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# set return 0 and return
jr $ra

rec:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# exit loop if eql
ble $a0 $s0 end
# jump to 'rec'
subi $a0 $a0 c1
jal rec
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# jr
jr $ra

end:
# set return 0 and return
jr $ra
