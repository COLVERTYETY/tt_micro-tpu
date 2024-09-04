# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from enum import IntEnum

def int2list(i, width=2):
    res= [int(x) for x in bin(i)[2:]]
    while len(res)<width:
        res.insert(0,0)
    return res

def list2int(l):
    return int("".join(str(x) for x in l), 2)

class op(IntEnum):
    # CLEARMP = 1 # reset mp to 0
    NOOP = 0 # do nothing
    SETMP = 1 # set mp to X
    WRITE = 2 # write to memory at mp, increment mp
    READ = 3 # read from memory at mp, increment mp
    MMUL = 4 # element-wise multiply of matrix at A and B, store in C
    DOT = 5 # dot product of matrix at A and B, store in C
    MATMUL = 6 # matrix multiplication of matrix at A and B, store in C
    SUM = 7 # sum of matrix at A, store in C
    # ADD = 9 # add matrix at A to scalar, store in C
    # SUB = 10 # subtract matrix at A from scalar, store in C
    # PROD = 12 # product of matrix at A, store in C
    # MAX = 13 # max of matrix at A, store in C
    # MIN = 14 # min of matrix at A, store in C

@cocotb.test()
async def test_WRITE_READ(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test WRITE and READ operations")

    inputs = [(op.SETMP, 0)]
    for i in range(16):
        inputs.append((op.WRITE, 1))
    for i in range(16):
        inputs.append((op.WRITE, 2))
    for i in range(16):
        inputs.append((op.WRITE, 3))
    for i in range(16):
        inputs.append((op.WRITE, 4))
    # await ClockCycles(dut.clk, 1)
    for inp in inputs:
        dut.ui_in.value = int(inp[0])
        dut.uio_in.value = inp[1]
        await ClockCycles(dut.clk, 1)
    dut.ui_in.value = int(op.SETMP)
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 1)
    once = True
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        dut.uio_in.value = 0
        await ClockCycles(dut.clk, 1)
        dut._log.info(f"Expected 1, got {dut.uo_out.value} at i={i}")
        if once:
            await ClockCycles(dut.clk, 1)
            once = False
        assert dut.uo_out.value == 1 , f"Expected 1, got {dut.uo_out.value} at i={i}"
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == 2, f"Expected 2, got {dut.uo_out.value} at i={i+16}"
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == 3 , f"Expected 3, got {dut.uo_out.value} at i={i+32}"
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == 4 , f"Expected 4, got {dut.uo_out.value} at i={i+48}"

@cocotb.test()
async def test_MMUL(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test WRITE and READ operations")

    inputs = [(op.SETMP, 0)]
    for i in range(16):
        inputs.append((op.WRITE, 1))
    for i in range(16):
        inputs.append((op.WRITE, 2))
    for i in range(16):
        inputs.append((op.WRITE, 3))
    for i in range(16):
        inputs.append((op.WRITE, 4))
    # await ClockCycles(dut.clk, 1)
    for inp in inputs:
        dut.ui_in.value = int(inp[0])
        dut.uio_in.value = inp[1]
        await ClockCycles(dut.clk, 1)
    
    inp2 = []
    inp2.extend(int2list(1))
    inp2.extend(int2list(2))
    inp2.extend(int2list(3))
    inp2.extend(int2list(0))
    mmul = (op.MMUL, list2int((inp2)))
    dut.ui_in.value= int(mmul[0])
    dut.uio_in.value = mmul[1]
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = int(op.SETMP)
    dut.uio_in.value = 16*3
    await ClockCycles(dut.clk, 1)
    once = True
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        await ClockCycles(dut.clk, 1)
        if once:
            await ClockCycles(dut.clk, 1)
            once = False
        assert dut.uo_out.value == 6 , f"mmul doesn't return correct result"

@cocotb.test()
async def test_DOT(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test WRITE and READ operations")

    inputs = [(op.SETMP, 0)]
    for i in range(16):
        inputs.append((op.WRITE, 1))
    for i in range(16):
        inputs.append((op.WRITE, 2))
    for i in range(16):
        inputs.append((op.WRITE, 3))
    for i in range(16):
        inputs.append((op.WRITE, 4))
    # await ClockCycles(dut.clk, 1)
    for inp in inputs:
        dut.ui_in.value = int(inp[0])
        dut.uio_in.value = inp[1]
        await ClockCycles(dut.clk, 1)
    
    inp2 = []
    inp2.extend(int2list(3))
    inp2.extend(int2list(1))
    inp2.extend(int2list(2))
    inp2.extend(int2list(0))
    dot = (op.DOT, list2int((inp2)))
    dut.ui_in.value= int(dot[0])
    dut.uio_in.value = dot[1]
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = int(op.SETMP)
    dut.uio_in.value = 16*2
    await ClockCycles(dut.clk, 1)
    once = True
    dut.ui_in.value = int(op.READ)
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 32 , f"dot doesn't return correct result"



@cocotb.test()
async def test_SUM(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test WRITE and READ operations")

    inputs = [(op.SETMP, 0)]
    for i in range(16):
        inputs.append((op.WRITE, 1))
    for i in range(16):
        inputs.append((op.WRITE, 2))
    for i in range(16):
        inputs.append((op.WRITE, 3))
    for i in range(16):
        inputs.append((op.WRITE, 4))
    # await ClockCycles(dut.clk, 1)
    for inp in inputs:
        dut.ui_in.value = int(inp[0])
        dut.uio_in.value = inp[1]
        await ClockCycles(dut.clk, 1)
    
    inp2 = []
    inp2.extend(int2list(2))
    inp2.extend(int2list(0))
    inp2.extend(int2list(0))
    inp2.extend(int2list(0))
    sum = (op.SUM, list2int((inp2)))
    dut.ui_in.value= int(sum[0])
    dut.uio_in.value = sum[1]
    await ClockCycles(dut.clk, 2)
    # dut.ui_in.value = int(op.SETMP)
    # dut.uio_in.value = 16*2
    # await ClockCycles(dut.clk, 1)
    # once = True
    # dut.ui_in.value = int(op.READ)
    # await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 3*16 , f"sum doesn't return correct result"

@cocotb.test()
async def test_MATMUL(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test WRITE and READ operations")

    inputs = [(op.SETMP, 0)]
    for i in range(16):
        inputs.append((op.WRITE, 1))
    for i in range(16):
        inputs.append((op.WRITE, 2))
    for i in range(16):
        inputs.append((op.WRITE, 3))
    for i in range(16):
        inputs.append((op.WRITE, 4))
    # await ClockCycles(dut.clk, 1)
    for inp in inputs:
        dut.ui_in.value = int(inp[0])
        dut.uio_in.value = inp[1]
        await ClockCycles(dut.clk, 1)
    
    inp2 = []
    inp2.extend(int2list(3))
    inp2.extend(int2list(1))
    inp2.extend(int2list(0))
    inp2.extend(int2list(0))
    matmul = (op.MATMUL, list2int((inp2)))
    dut.ui_in.value= int(matmul[0])
    dut.uio_in.value = matmul[1]
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = int(op.SETMP)
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 1)
    once = True
    for i in range(16):
        dut.ui_in.value = int(op.READ)
        await ClockCycles(dut.clk, 1)
        if once:
            await ClockCycles(dut.clk, 1)
            once = False
        assert dut.uo_out.value == 32 , f"matmul doesn't return correct result"

@cocotb.test()
async def test_full_random(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test all possible ionputs")

    for i in range(256):
        for j in range(256):
            dut.ui_in.value = i
            dut.uio_in.value = j
            await ClockCycles(dut.clk, 1)
            assert dut.rst_n.value == 1 