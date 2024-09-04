<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

The project is a simple example tpu for operations on 4x4 matrices. The availabel operations are : 
- SETMP: set the memory pointer to a given location
- WRITE: write a scalar to memory at a given address
- READ: read a scalar from memory at a given address
- MMUL: element wise multiplication of matrix A and B store in C
- DOT: perform dot product of matrix A and B, store in C
- MATMUL: Matrix multiplication of A and B, store in C
- SUM: sum of matrix A, output straight to output

## How to test

1. start by setting the MP to 0 with SETMP.
2. Write matrix Data to the memory, WRITE auto increments the MP 
3. perform desired operation (eg: MMUL, DOT, MATMUL) 
4. use SETMP to set MP at the start of the result
5. use READ to write the memory to the output pins, MP is auto-incremented.
6. enjoy !

## External hardware

probably a mcu which could do the operation by itself without any issues...