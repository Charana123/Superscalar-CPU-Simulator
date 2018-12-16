main:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# main
li $t1 c10
# jump to 'label'
jal label
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# set return 0 and return
li $v0 c0
jr $ra
 label:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# main
li $t2 c15
# jump to 'label'
jal label2
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# set return 0 and return
li $v0 c0
jr $ra
 label2:
# store $ra in stack
sw $ra $sp c0
addi $sp $sp c1
# main
li $t3 c30
# jump to 'label'
jal label3
# load $ra from stack
subi $sp $sp c1
lw $ra $sp c0
# set return 0 and return
li $v0 c0
jr $ra
 label3:
li $t4 c35
# set return 0 and return
li $v0 c0
jr $ra
