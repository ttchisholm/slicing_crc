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

def generate_byte_table(poly, bit_reverse_poly=True):
    bit_reverse_poly = True

    poly = int('{:032b}'.format(poly)[::-1], 2) if bit_reverse_poly else poly

    table = []
    for d in range(256):
        t = d
        for i in range(8):
            t = (t >> 1) ^ ((t & 0x01) * poly)
        table.append(t)
    return table


def generate_slicing_tables(poly, n, bit_reverse_poly=True):
    crc_tables = []
    crc_tables.append(generate_byte_table(poly, bit_reverse_poly))

    for j in range(1, n):
        crc_tables.append([])
        for i in range(256):
            crc_tables[j].append((crc_tables[j-1][i] >> 8) ^ crc_tables[0][crc_tables[j-1][i] & 0xFF])

    return crc_tables

def write_crc_tables(path, poly, n, bit_reverse_poly=True):
    crc_tables = generate_slicing_tables(poly, n)

    with open(path, 'w') as f:
        f.writelines([l + '\n' for l in [' '.join([f'{ti:08x}' for ti in t]) for t in crc_tables]])

if __name__ == "__main__":

    polynomial = 0x04C11DB7 # Polynomial for CRC32 (Ethernet)
    max_slice_length = 16

    write_crc_tables('../hdl/crc_tables.mem', polynomial, max_slice_length, 16)

