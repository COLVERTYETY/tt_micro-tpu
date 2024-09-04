from amaranth import *
from amaranth import Elaboratable, Module, Signal, unsigned, Const , Mux
from amaranth.sim import Simulator
from amaranth.back import rtlil, verilog
from amaranth.lib.crc import Algorithm
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from enum import Enum, IntEnum
import tabulate

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

class pyTpu:
    def __init__(self) -> None:
        self.memory = [0]*(4*16)
        self.mp = 0
        self.input = [0]*8 # 4 bits for operation
        self.input2 = [0]*8 # memory address or scalar
        self.output = 0

    def __repr__(self) -> str:
        headers = ["adress start", "adress stop", "Value"]
        table = []
        prev = self.memory[0]
        prev_start=0
        for i, value in enumerate(self.memory):
            if value!=prev:
                table.append((prev_start, i, prev))
                prev = value
                prev_start = i
        table.append((prev_start, len(self.memory)-1, self.memory[-1]))
        return tabulate.tabulate(table, headers=headers)

    def step(self):
        # handle input
        current_op = list2int(self.input[0:4]) 
        # convert binary representation to enum
        current_op = op(current_op)
        match current_op:
            case op.SETMP:
                self.mp = list2int(self.input2)
            case op.WRITE:
                self.memory[self.mp] = list2int(self.input2)
                self.mp += 1
            case op.READ:
                self.output = self.memory[self.mp]
                self.mp += 1
            case op.MMUL:
                index_A = list2int(self.input2[0:2])*16
                index_B = list2int(self.input2[2:4])*16
                index_C = list2int(self.input2[4:6])*16
                for i in range(4):
                    for j in range(4):
                        self.memory[index_C + i*4 + j] = self.memory[index_A + i*4 + j] * self.memory[index_B + i*4 + j]
                
            case op.DOT:
                index_A = list2int(self.input2[0:2])*16
                index_B = list2int(self.input2[2:4])*16
                index_C = list2int(self.input2[4:6])*16
                self.output = 0
                for i in range(4):
                    self.output += self.memory[index_A + i] * self.memory[index_B + i]
                self.memory[index_C] = self.output
                self.mp += 1
            case op.MATMUL:
                index_A = list2int(self.input2[0:2])*16
                index_B = list2int(self.input2[2:4])*16
                index_C = list2int(self.input2[4:6])*16
                for i in range(4):
                    for j in range(4):
                        self.output = 0
                        for k in range(4):
                            self.output += self.memory[index_A + i*4 + k] * self.memory[index_B + k*4 + j]
                        self.memory[index_C + i*4 + j] = self.output
                self.mp += 1
            case op.SUM:
                index_A = list2int(self.input2[0:2])*16
                self.output=0
                for i in range(16):
                    self.output+= self.memory[index_A+i]
            case _:
                pass

class tpu(wiring.Component):
    def __init__(self) -> None:
        
        self.input = Signal(unsigned(8), name="ui_in")
        self.input2 = Signal(unsigned(8), name="uio_in")
        self.output = Signal(unsigned(8), name="uo_out")
        
        self.uio_out = Signal(8) # bidir, out
        self.uio_oe = Signal(8) # bidir, IOs: Enable path (active high: 0=input, 1=output)
        self.ena = Signal()
        self.clk = Signal()
        self.rst_n = Signal()

        self.memory = Array(Signal(unsigned(8), name=f"m_{i}") for i in range(4*16))
        self.mp = Signal(unsigned(8))
        
        self.index_A = Signal(unsigned(8))
        self.index_B = Signal(unsigned(8))
        self.index_C = Signal(unsigned(8))

    
    def elaborate(self, platform):
        m = Module()
        
        # tmp = Signal(unsigned(8))

        m.d.comb += self.index_A.eq(self.input2[6:8] * 16)
        m.d.comb += self.index_B.eq(self.input2[4:6] * 16)
        m.d.comb += self.index_C.eq(self.input2[2:4] * 16)       

        # m.d.sync+= self.mp.eq(self.input2*(self.input[0:4]==Const(op.SETMP.value)))
        # m.d.comb += tmp.eq(self.mp)
        with m.Switch(self.input[0:4]):
            with m.Case(op.SETMP.value):
                m.d.sync += self.mp.eq(self.input2)
            with m.Case(op.WRITE.value):
                m.d.sync += self.memory[self.mp].eq(self.input2)
                m.d.sync += self.mp.eq(self.mp + 1)
                # m.d.sync += self.memory[tmp].eq(self.input2)
                # m.d.sync += self.mp.eq(self.mp + 1)
            with m.Case(op.READ.value):
                m.d.sync += self.output.eq(self.memory[self.mp])
                m.d.sync += self.mp.eq(self.mp + 1)
                # m.d.sync += self.output.eq(self.memory[tmp])
                # m.d.sync += self.mp.eq(self.mp + 1)
            with m.Case(op.MMUL.value):
                for i in range(4):
                    for j in range(4):
                        m.d.sync += self.memory[self.index_C + i*4 + j].eq(self.memory[self.index_A + i*4 + j] * self.memory[self.index_B + i*4 + j])
            with m.Case(op.MATMUL.value):
                for i in range(4):
                    for j in range(4):
                        temp = 0
                        for k in range(4):
                            temp += self.memory[self.index_A + i*4 + k] * self.memory[self.index_B + k*4 + j]
                        m.d.sync += self.memory[self.index_C + i*4 + j].eq(temp)
            with m.Case(op.DOT.value):
                temp = 0
                for i in range(4):
                    temp += self.memory[self.index_A + i] * self.memory[self.index_B + i]
                m.d.sync += self.memory[self.index_C].eq(temp)
                m.d.sync += self.mp.eq(self.mp + 1)
            with m.Case(op.SUM.value):
                temp = 0
                for i in range(16):
                    temp += self.memory[self.index_A + i]
                m.d.sync += self.output.eq(temp)
            with m.Default():
                pass
        return m

    def generate(self):
        m = self.elaborate(None)
         # clock and reset
        cd_sync = ClockDomain("sync")
        m.domains += cd_sync
        m.d.comb += [
            ClockSignal("sync").eq(self.clk),
            ResetSignal("sync").eq(~self.rst_n),
        ]
        m.d.comb += [
            self.uio_out.eq(0xff),
            self.uio_oe.eq(0x00),
        ]
        # convert the module to verilog
        with open("top_tpu.v", "w") as f:
            f.write(verilog.convert(m, 
                                    name="tt_um_COLVERTYETY_top",
                                    emit_src=False, strip_internal_attrs=True,
                                    ports=[self.input, self.output, self.input2, self.uio_out, self.uio_oe, self.ena, self.clk, self.rst_n]
                                    ))

def test():
    dut = tpu()
    sim = Simulator(dut)
    sim.add_clock(1e-6)

    async def test_bench(ctx):
        def display():
            headers = ["adress start", "adress stop", "Value"]
            table = []
            prev = int(ctx.get(dut.memory[0]))
            prev_start=0
            for i, val in enumerate(dut.memory[1:]):
                value = int(ctx.get(val))
                if value!=prev:
                    table.append((prev_start, i, prev))
                    prev = int(value)
                    prev_start = i+1
            table.append((prev_start, len(dut.memory)-1, int(ctx.get(dut.memory[-1]))))
            print(tabulate.tabulate(table, headers=headers))

        inputs = [(op.SETMP, 0)]
        for i in range(16):
            inputs.append((op.WRITE, 1))
        for i in range(16):
            inputs.append((op.WRITE, 2))
        for i in range(16):
            inputs.append((op.WRITE, 3))
        for i in range(16):
            inputs.append((op.WRITE, 4))
        # await ctx.tick()
        # once = True
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick()
            # ctx.set(dut.input,  0)
            # ctx.set(dut.input2, 0)
            # if once: await ctx.tick()
            display()
        inputs = [(op.SETMP, 0)]
        for i in range(64):
            inputs.append((op.READ, 0))
        outputs = []
        once = True
        # await ctx.tick()
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick().repeat(1)
            # if once: await ctx.tick()
            if not once: outputs.append(int(ctx.get(dut.output)))
            once = False
        print(outputs)
        for i in range(0,16):
            assert outputs[i]==1, f"expected 1 got {outputs[i]} at {i}"
        for i in range(16,32):
            assert outputs[i]==2, f"expected 2 got {outputs[i]} at {i}"
        for i in range(32,48):
            assert outputs[i]==3, f"expected 3 got {outputs[i]} at {i}"
        for i in range(48,63):
            assert outputs[i]==4, f"expected 4 got {outputs[i]} at {i}"

        inp2 = []
        inp2.extend(int2list(1))
        inp2.extend(int2list(2))
        inp2.extend(int2list(3))
        inp2.extend(int2list(0))
        print(inp2)
        print(bin(list2int(inp2)))
        inputs.append((op.MMUL, list2int((inp2))))
        await ctx.tick()
        prev2 = None
        prev1 = None
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick().repeat(1)
            # print(inp[1], ctx.get(dut.input2))
            # yield self.input.eq(int2list(int(inp[0])))
            # yield self.input2.eq(inp[1])
            # yield
            # if(inp[0]!=op.WRITE):
            if prev2!=inp[1] or prev1!=inp[0]:
                prev2 = inp[1]
                prev1 = inp[0]
                print(inp[0].name, inp[1], bin(inp[1]), ctx.get(dut.input2[0:2]), ctx.get(dut.input2[2:4]), ctx.get(dut.input2[4:6]), ctx.get(dut.input2[6:8]))
                display()
                
        for i in range(48,64):
            assert ctx.get(dut.memory[i])==6
        inp2 = []
        inp2.extend(int2list(3))
        inp2.extend(int2list(1))
        inp2.extend(int2list(2))
        inp2.extend(int2list(0))
        inputs=[(op.DOT, list2int(inp2))]
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick().repeat(1)
            display()
        assert ctx.get(dut.memory[32])==48
        inp2 = []
        inp2.extend(int2list(3))
        inp2.extend(int2list(0))
        inp2.extend(int2list(0))
        inp2.extend(int2list(0))
        inputs=[(op.SUM, list2int(inp2))]
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick().repeat(1)
            print("SUM of 3", ctx.get(dut.output))
            display()
        assert ctx.get(dut.output)==6*16
        inp2 = []
        inp2.extend(int2list(0))
        inp2.extend(int2list(1))
        inp2.extend(int2list(2))
        inp2.extend(int2list(0))
        inputs=[(op.MATMUL, list2int(inp2))]
        for inp in inputs:
            ctx.set(dut.input,  int(inp[0]))
            ctx.set(dut.input2, inp[1])
            await ctx.tick().repeat(1)
            print(inp[0].name)
            display()
        for i in range(32,48):
            assert ctx.get(dut.memory[i])==8
            
        

    sim.add_testbench(test_bench)
    with sim.write_vcd("tpu.vcd"):
        sim.run()

    return True
