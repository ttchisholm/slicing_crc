# MIT License

# Copyright (c) 2023 Tom Chisholm

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, Edge, NextTimeStep
from cocotb.clock import Clock
from cocotb_test.simulator import run


import glob
import pytest
import numpy as np
import zlib
import os

from generate_crc_tables import write_crc_tables

class CRC_TB:
    def __init__(self, dut):
        self.dut = dut

        self.data_width = len(self.dut.i_data)
        self.clk_period = round(1 / (10.3125 / self.data_width), 2) # ps precision

        cocotb.start_soon(Clock(dut.i_clk, self.clk_period, units="ns").start())

        self.dut.i_data.value = 0
        self.dut.i_valid.value = 0

@cocotb.test()
async def crc_test(dut):
    
    tb = CRC_TB(dut)

    number_tests = 100
    packet_length_range = [1, 1024]
    test_vectors = [np.random.randint(0, 256, np.random.randint(*packet_length_range, 1)[0], dtype=np.uint8) \
                    for _ in range(number_tests)]

    results = [zlib.crc32(bytearray(tv)) for tv in test_vectors]

    assert (tb.data_width % 8 == 0)
    input_width_bytes = tb.data_width // 8

    # concatonate the test vector to match the input width
    # https://stackoverflow.com/questions/434287/how-to-iterate-over-a-list-in-chunks
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    for tv, res in zip(test_vectors, results):

        await FallingEdge(tb.dut.i_clk)
        tb.dut.i_reset.value = 1
        await FallingEdge(tb.dut.i_clk)
        tb.dut.i_reset.value = 0
        

        for ivalues in chunker(tv, input_width_bytes):

            ivalue = 0
            ivalid = 0
            for i, v in enumerate(ivalues):
                ivalue = ivalue | (int(v) <<  (i * 8))
                ivalid = ivalid | (1 << i)

            tb.dut.i_data.value = ivalue
            tb.dut.i_valid.value = ivalid
            await FallingEdge(tb.dut.i_clk)
        
        tb.dut.i_valid.value = 0

        if (tb.dut.REGISTER_OUTPUT):
             await RisingEdge(tb.dut.i_clk)

        assert tb.dut.o_crc.value.integer == res, \
        f'CRC result invalid (expected={res:04x}, actual={tb.dut.o_crc.value.integer:04x})'
   


@pytest.mark.parametrize(
    "parameters", [
        {"SLICE_LENGTH": "1" },  
        {"SLICE_LENGTH": "2" }, 
        {"SLICE_LENGTH": "4" }, 
        {"SLICE_LENGTH": "8" },  
        {"SLICE_LENGTH": "16" },
        {"SLICE_LENGTH": "16", "REGISTER_OUTPUT" : "0" },   
        ])
def test_slicing_crc(parameters):

    polynomial = 0x04C11DB7 # Polynomial for CRC32 (Ethernet)
    sim_build = "./sim_build/" + ",".join((f"{key}={value}" for key, value in parameters.items()))

    os.makedirs(sim_build, exist_ok=True)

    write_crc_tables(os.path.join(sim_build, 'crc_tables.mem'), polynomial, int(parameters['SLICE_LENGTH']))

    run(
        verilog_sources=glob.glob('../hdl/slicing_crc.sv'),
        toplevel="slicing_crc",

        module="test_slicing_crc",
        simulator="icarus",
        verilog_compile_args=["-g2012"],
        includes=["../hdl", "../../", "../../../"],

        parameters=parameters,
        extra_env=parameters,
        sim_build=sim_build
    )