from asyncore import loop
import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, Edge, NextTimeStep
from cocotb.clock import Clock
from cocotb.result import TestFailure

import numpy as np
import zlib

import debugpy


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
   

