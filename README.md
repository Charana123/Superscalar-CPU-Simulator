# Superscalar Processor
A simulator for a superscalar out-of-order processor in python.

## How to Run

To simply run an benchmark program, try:
``` python processor.py ../benchmark_kernels/fib.asm ```

For more information try:
``` python processor.py --help ```

<p align="center">
    <a href="https://raw.githubusercontent.com/Charana123/Superscalar-CPU-Simulator/master/processor.png">
        <img alt="ScreenShot~ prompt" width="100%" height="100%" src="https://raw.githubusercontent.com/Charana123/Superscalar-CPU-Simulator/master/processor.png">
    </a> with a Register Alias Table (RAT) and Reorder Buffer (ROB)
</p>

## Features

### Instruction Set Architecture
1. Supports Arithmetic, Load and Store, Unconditional Jumps (e.g. jump and link, system call), Conditional Jumps (e.g. branch if equal)
2. Support multi-cycle instructions
3. Only supports integer operation (no float point i.e. FPU)

### Pipeline
1. 7 stage pipeline - fetch, decode, issue, dispatch, execute, writeback, commit
2. Execution Units - ALU (Arithmetic Logic Unit), MU (Multiplication Unit), DU (Division Unit), LSU (Load Store Unit)
3. Decouples fetch-decode and writeback-commit with instruction queue and reorder buffer.
4. Execution units of multi-cycle instructions are fully pipelined (bar the DU, which cannot be pipelined)
5. Priority writeback - prioritises the retirement of slow multi-cycle instructions when more options than the pipeline width are available

<p align="center">
    <a href="https://raw.githubusercontent.com/Charana123/Superscalar-CPU-Simulator/master/pipeline.png">
        <img alt="ScreenShot~ prompt" width="50%" height="50%" src="https://raw.githubusercontent.com/Charana123/Superscalar-CPU-Simulator/master/pipeline.png">
    </a>
</p>

### Branch Prediction
1. Speculative execution with infinite levels of speculative depth
3. Implements a Two-level local dynamic/adaptive predictor for conditional branch prediction
    - Implements a N-bit local pattern history (N = 2 default)
    - Implements a 2^N entry branch history register table with S-bit saturating counters (S = 2 default)
2. Implements a Branch Target Address Cache and Instruction Cache (BTAIC) to cache branch speculations
4. Implements a Return Address Stack (RAS) to return from multiple nested function calls
    - Uses a checkpointing mechanism to recover from failed branch speculation
5. Recovers from mispredicted branches by flushing at commit

### Optimisations
1. N-way superscalar where N is configurable
2. Implements Tomasulos Algorithm - for out-of-order execution of instructions that writeback to registers
3. Implements a Load Store Queue (with store-to-load forwarding) - for out-of-order execution of instructions that writeback to memory
    - Recovers from a wrongly speculatively loaded value of memory addresses by flushing at commit
4. Implements Register Renaming with a Register Alias Table (RAT) and Reorder Buffer (ROB)

### Vectorization
1. configurable vector length - default 16 (AVX2 ISE) .
2. Vector ISA - Vector Arithemetic Operations, Vector Load and Store Operations, Vector Mask Operations, Vector Blend Operations






















