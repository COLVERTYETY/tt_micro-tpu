from tpu import *
import numpy as np


def test_python_tpu_():
    tpu_ = pyTpu()
    tpu_.step()
    inputs = [(op.SETMP, int2list(0))]
    for i in range(16):
        inputs.append((op.WRITE, int2list(1)))
    for i in range(16):
        inputs.append((op.WRITE, int2list(2)))
    for i in range(16):
        inputs.append((op.WRITE, int2list(3)))
    for i in range(16):
        inputs.append((op.WRITE, int2list(4)))
    inp2 = []
    inp2.extend(int2list(1))
    inp2.extend(int2list(2))
    inp2.extend(int2list(3))
    inp2.extend(int2list(0))
    print(inp2)
    print(bin(list2int(inp2)))
    inputs.append((op.MMUL, inp2))
    for inp in inputs:
        tpu_.input = int2list(int(inp[0]))
        tpu_.input2 = inp[1]
        tpu_.step()
        if(inp[0]!=op.WRITE): print(inp[0].name,"\n", tpu_)
    inp2 = []
    inp2.extend(int2list(3))
    inp2.extend(int2list(1))
    inp2.extend(int2list(2))
    inp2.extend(int2list(0))
    inputs=[(op.DOT, inp2)]
    for inp in inputs:
        tpu_.input = int2list(int(inp[0]))
        tpu_.input2 = inp[1]
        tpu_.step()
        print(inp[0].name,"\n", tpu_)
    inp2 = []
    inp2.extend(int2list(3))
    inp2.extend(int2list(0))
    inp2.extend(int2list(0))
    inp2.extend(int2list(0))
    inputs=[(op.SUM, inp2)]
    for inp in inputs:
        tpu_.input = int2list(int(inp[0]))
        tpu_.input2 = inp[1]
        tpu_.step()
        print(tpu_.output)
        print(inp[0].name,"\n", tpu_)
    inp2 = []
    inp2.extend(int2list(0))
    inp2.extend(int2list(1))
    inp2.extend(int2list(2))
    inp2.extend(int2list(0))
    inputs=[(op.MATMUL, inp2)]
    for inp in inputs:
        tpu_.input = int2list(int(inp[0]))
        tpu_.input2 = inp[1]
        tpu_.step()
        print(inp[0].name,"\n", tpu_)
    return True

def test_tpu_():
    return test()

    



if __name__ == "__main__":
    assert test_python_tpu_()
    assert test_tpu_()
    print("test passed")
    print("generating verilog code")
    t = tpu()
    t.generate()