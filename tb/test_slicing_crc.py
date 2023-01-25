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

        self.data_width = len(self.dut.data)
        self.clk_period = round(1 / (10.3125 / self.data_width), 2) # ps precision

        cocotb.start_soon(Clock(dut.clk, self.clk_period, units="ns").start())

        self.dut.data.value = 0
        self.dut.valid.value = 0

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

        await FallingEdge(tb.dut.clk)
        tb.dut.reset.value = 1
        await FallingEdge(tb.dut.clk)
        tb.dut.reset.value = 0
        

        for ivalues in chunker(tv, input_width_bytes):

            ivalue = 0
            ivalid = 0
            for i, v in enumerate(ivalues):
                ivalue = ivalue | (int(v) <<  (i * 8))
                ivalid = ivalid | (1 << i)

            tb.dut.data.value = ivalue
            tb.dut.valid.value = ivalid
            await FallingEdge(tb.dut.clk)
        
        tb.dut.valid.value = 0

        if (tb.dut.REGISTER_OUTPUT):
             await RisingEdge(tb.dut.clk)

        assert tb.dut.crc.value.integer == res, \
        f'CRC result invalid (expected={res:04x}, actual={tb.dut.crc.value.integer:04x})'
   


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

    if not os.path.isdir(sim_build):
         os.mkdir(sim_build)

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