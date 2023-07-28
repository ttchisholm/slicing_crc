

set clk_period 1

set_part xczu49dr-ffvf1760-2-e
set_property target_language Verilog [current_project]
read_verilog ../hdl/slicing_crc.sv -sv
read_xdc constraints.xdc

set slice_lengths {4}	;

foreach x $slice_lengths {	;
    set_property generic "SLICE_LENGTH=$x" [current_fileset]

    # Prevent Vivado optimising away data path
    synth_design -top slicing_crc -rtl
    set_property KEEP on [get_nets -filter {NAME =~ o_crc[*]}]

    synth_design -top slicing_crc

    lappend fmaxes [expr {1000 / ($clk_period - [get_property SLACK [get_timing_paths]])}]
}

exec echo $fmaxes

