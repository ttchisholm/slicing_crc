# Makefile

# defaults
SIM ?= modelsim
TOPLEVEL_LANG ?= verilog
WAVES ?= 1

VERILOG_SOURCES += $(PWD)/../hdl/slicing_crc.sv


CUSTOM_SIM_DEPS += crc_tables.mem


# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = slicing_crc

# MODULE is the basename of the Python test file
MODULE = test_slicing_crc

# module parameters
export SLICE_LENGTH ?= 8

ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	COMPILE_ARGS += -P $(TOPLEVEL).SLICE_LENGTH=$(SLICE_LENGTH)

	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif

else ifeq ($(SIM), verilator)
	COMPILE_ARGS += -GSLICE_LENGTH=$(SLICE_LENGTH)
	ifeq ($(WAVES), 1)
		COMPILE_ARGS += --trace-fst --trace-structs
	endif 
else ifeq ($(SIM), modelsim)
	COMPILE_ARGS += +cover=sbceft
	SIM_ARGS += -GSLICE_LENGTH=$(SLICE_LENGTH)
	SIM_ARGS += -coverage
	SIM_ARGS += -no_autoacc
	SIM_ARGS +=  -do \" coverage save -onexit $(TOPLEVEL).ucdb; run -all;exit\"
endif

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

crc_tables.mem: $(PWD)/../hdl/crc_tables.mem 
	cp $< $@

iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

clean::
	@rm -rf iverilog_dump.v
	@rm -rf crc32_slice.mem
	@rm -rf dump.fst $(TOPLEVEL).fst