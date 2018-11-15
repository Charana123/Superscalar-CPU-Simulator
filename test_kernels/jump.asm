main:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# jump to 'label'
jal label
# main
li $t1 c10
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# set return 0 and return
li $v0 c0
jr $ra

label:
li $t0 c5
# set return 0 and return
li $v0 c0
jr $ra
