#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "6502-emu_wrapper.h"
#include "libdebugger.h"

long cycles_per_frame;


uint8_t simple_kernel[] = {
	0xa9,0x00,0x85,0x80,0xa9,0x20,0x85,0x81,
	0xa9,0x40,0x85,0x82,0xa9,0x00,0x85,0x83,
	0xa5,0x81,0x85,0x84,0xa0,0x00,0xa5,0x80,
	0x91,0x83,0xc8,0xd0,0xfb,0xe6,0x84,0xa6,
	0x84,0xe4,0x82,0x90,0xf3,0xe6,0x80,0x18,
	0x90,0xe2};

void lib6502_init_debug_kernel() {
	int i;

	for (i=0; i<sizeof(simple_kernel); i++) {
		memory[0xf000 + i] = simple_kernel[i];
	}
	PC = 0xf000;
}

void lib6502_init_cpu(float frequency_mhz, float refresh_rate_hz) {
	init_tables();

	A = 0;
	X = 0;
	Y = 0;
	SP = 0xff;
	SR.byte = 0;
	PC = 0xfffe;
	memset(memory, 0, sizeof(memory));

	cycles_per_frame = (long)((frequency_mhz * 1000000.0) / refresh_rate_hz);

	lib6502_init_debug_kernel();
}

void lib6502_clear_state_arrays(void *input, output_t *output)
{
}

void lib6502_configure_state_arrays(void *input, output_t *output) {
	output->frame_status = 0;
	output->cycles_since_power_on = 0;
	output->instructions_since_power_on = 0;
}

void lib6502_get_current_state(output_t *buf) {
	buf->A = A;
	buf->X = X;
	buf->Y = Y;
	buf->SP = SP;
	save16(buf->PC, PC);
	buf->SR = SR.byte;
	memcpy(buf->memory, memory, 1<<16);
}

void lib6502_restore_state(output_t *buf) {
	A = buf->A;
	X = buf->X;
	Y = buf->Y;
	SP = buf->SP;
	load16(PC, buf->PC);
	SR.byte = buf->SR;
	memcpy(memory, buf->memory, 1<<16);
}

int lib6502_step_cpu(frame_status_t *output)
{
	int count;
	intptr_t index;

	inst = instructions[memory[PC]];

	write_addr = NULL;
	read_addr = NULL;
	jumping = 0;
	extra_cycles = 0;

	output->memory_access[PC] = (uint16_t)output->frame_number;
	output->access_type[PC] = ACCESS_TYPE_EXECUTE;
	count = lengths[inst.mode];
	if (count > 1) {
		output->memory_access[PC + 1] = (uint16_t)output->frame_number;
		output->access_type[PC + 1] = ACCESS_TYPE_EXECUTE;
	}
	if (count > 2) {
		output->memory_access[PC + 2] = (uint16_t)output->frame_number;
		output->access_type[PC + 2] = ACCESS_TYPE_EXECUTE;
	}

	inst.function();
	if (jumping == 0) PC += count;

	// 7 cycle instructions (e.g. ROL $nnnn,X) don't have a penalty cycle for
	// crossing a page boundary.
	if (inst.cycles == 7) extra_cycles = 0;

	if (read_addr != NULL) {
		index = (intptr_t)read_addr - (intptr_t)(&memory[0]);
		if (index >= 0 && index < MAIN_MEMORY_SIZE) {
			output->memory_access[(uint16_t)index] = (uint16_t)output->frame_number;
			output->access_type[(uint16_t)index] = ACCESS_TYPE_READ;
		}
	}
	if (write_addr != NULL) {
		index = (intptr_t)write_addr - (intptr_t)(&memory[0]);
		if (index >= 0 && index < MAIN_MEMORY_SIZE) {
			output->memory_access[(uint16_t)index] = (uint16_t)output->frame_number;
			output->access_type[(uint16_t)index] = ACCESS_TYPE_WRITE;
		}
	}

	return inst.cycles + extra_cycles;
}

int lib6502_register_callback(uint16_t token, uint16_t addr) {
	int value;

	switch (token) {
		case REG_A:
		value = A;
		break;

		case REG_X:
		value = X;
		break;

		case REG_Y:
		value = Y;
		break;

		case REG_PC:
		value = PC;
		break;

		default:
		value = 0;
	}
	printf("lib6502_register_callback: token=%d addr=%04x value=%04x\n", token, addr, value);
	return value;
}

int lib6502_calc_frame(frame_status_t *output, breakpoints_t *breakpoints)
{
	int cycles, bpid, count;

	do {
		cycles = lib6502_step_cpu(output);
		output->current_instruction_in_frame += 1;
		output->instructions_since_power_on += 1;
		output->current_cycle_in_frame += cycles;
		output->cycles_since_power_on += cycles;
		bpid = libdebugger_check_breakpoints(breakpoints, cycles, &lib6502_register_callback);
		if (bpid >= 0) {
			output->frame_status = FRAME_BREAKPOINT;
			output->breakpoint_id = bpid;
			return bpid;
		}
	} while (output->current_cycle_in_frame < output->final_cycle_in_frame);
	output->frame_number += 1;
	return -1;
}

int lib6502_next_frame(void *input, output_t *output, breakpoints_t *breakpoints)
{
	int bpid;

	output->final_cycle_in_frame = cycles_per_frame - 1;
	libdebugger_calc_frame(&lib6502_calc_frame, (frame_status_t *)output, breakpoints);
	lib6502_get_current_state(output);
	return bpid;
}
