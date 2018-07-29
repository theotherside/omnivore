# generic6502 input template locations
import numpy as np

VIDEO_WIDTH = 280
VIDEO_HEIGHT = 192

VIDEO_SIZE = VIDEO_WIDTH * VIDEO_HEIGHT
AUDIO_SIZE = 2048
MAIN_MEMORY_SIZE = 1<<16
STATESAV_MAX_SIZE = MAIN_MEMORY_SIZE + 256

ACCESS_TYPE_READ = 1
ACCESS_TYPE_WRITE = 2
ACCESS_TYPE_EXECUTE = 4
ACCESS_TYPE_VIDEO = 8
ACCESS_TYPE_DISPLAY_LIST = 16


INPUT_DTYPE = np.dtype([
    ("keychar", np.uint8),
    ("keycode", np.uint8),
])

OUTPUT_DTYPE = np.dtype([
    ("cycles_since_power_on", np.uint64),
    ("instructions_since_power_on", np.uint64),
    ("frame_number", np.uint32),
    ("current_cycle_in_frame", np.uint32),
    ("final_cycle_in_frame", np.uint32),
    ("current_instruction_in_frame", np.uint32),
    ("frame_status", np.uint8),
    ("breakpoint_id", np.uint8),
    ("unused1", np.uint8),
    ("unused2", np.uint8),
    ("memory_access", np.uint16, MAIN_MEMORY_SIZE),
    ("access_type", np.uint8, MAIN_MEMORY_SIZE),
    ("state", np.uint8, STATESAV_MAX_SIZE),
    ("video", np.uint8, VIDEO_SIZE),
    ("audio", np.uint8, AUDIO_SIZE),
])

STATESAV_DTYPE = np.dtype([
    ("PC", '<u2'),
    ("A", np.uint8),
    ("X", np.uint8),
    ("Y", np.uint8),
    ("SP", np.uint8),
    ("P", np.uint8),
    ("memory", np.uint8, MAIN_MEMORY_SIZE),
    ])

CPU_DTYPE = np.dtype([
    ("PC", '<u2'),
    ("A", np.uint8),
    ("X", np.uint8),
    ("Y", np.uint8),
    ("SP", np.uint8),
    ("P", np.uint8),
    ])
