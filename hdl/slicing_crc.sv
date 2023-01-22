module slicing_crc #(
    parameter SLICE_LENGTH = 1,
    parameter INITIAL_CRC = 32'hFFFFFFFF,
    parameter INVERT_OUTPUT = 1,
    parameter REGISTER_OUTPUT = 1
) (
    input wire clk,
    input wire reset,
    input wire [8*SLICE_LENGTH-1:0] data,
    input wire [SLICE_LENGTH-1:0] valid,
    output wire [31:0] crc
);

    logic [31:0] crc_tables [SLICE_LENGTH][256];

    initial begin
        $readmemh("crc_tables.mem", crc_tables); //todo check dimensions
    end

    logic [31:0] prev_crc, crc_calc, crc_out;

    initial prev_crc <= INITIAL_CRC;

    always @(posedge clk)
    if (reset) begin
        prev_crc <= INITIAL_CRC;
    end else if (valid) begin
        prev_crc <= crc_calc;
    end


    wire [31:0] table_outs [SLICE_LENGTH];
    genvar gi;
    generate for (gi = 0; gi < SLICE_LENGTH; gi++) begin
        wire [7:0] table_lookup;
        wire [31:0] table_out;

        assign table_lookup = (gi < 4) ? data[8*gi +: 8] ^ prev_crc[8*gi +: 8] : data[8*gi +: 8];
        assign table_out = crc_tables[SLICE_LENGTH - gi - 1][table_lookup]; // Not table[0] is for last (ms) byte
        assign table_outs[gi] = table_out; // Keep both for debugging 
    end endgenerate

    always @(*) begin
        crc_calc = 0;
        for (int i = 0; i < SLICE_LENGTH; i++) crc_calc = crc_calc ^ table_outs[i];

        crc_calc = crc_calc ^ prev_crc >> (8*SLICE_LENGTH); // If slice length < 4, need to xor in the remaining bytes of previous crc
    end

    // wire [31:0] lookup, tout;
    // assign lookup = data ^ prev_crc[7:0];
    // assign tout = crc_tables[0][lookup];
    // assign crc_calc = (prev_crc >> 8) ^ tout;

    assign crc_out = REGISTER_OUTPUT ? prev_crc : crc_calc;
    assign crc = INVERT_OUTPUT ? ~crc_out : crc_out;

endmodule