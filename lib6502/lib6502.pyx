import numpy as np
cimport numpy as np

cdef extern:
    int lib6502_init_cpu(float, float)
    int lib6502_clear_state_arrays(np.uint8_t *buf, np.uint8_t *buf)
    int lib6502_configure_state_arrays(np.uint8_t *buf, np.uint8_t *buf)
    int lib6502_step_cpu()
    long lib6502_next_frame(np.uint8_t *buf, np.uint8_t *buf, np.uint8_t *buf)
    void lib6502_get_current_state(np.uint8_t *buf)
    void lib6502_restore_state(np.uint8_t *buf)

def start_emulator(args, python_callback_function, python_callback_args):
    lib6502_init_cpu(1.023, 60.0)  # apple 2 speed

def clear_state_arrays(np.ndarray input not None, np.ndarray output not None):
    cdef np.uint8_t[:] ibuf
    cdef np.uint8_t[:] obuf

    ibuf = input.view(np.uint8)
    obuf = output.view(np.uint8)
    lib6502_clear_state_arrays(&ibuf[0], &obuf[0])

def configure_state_arrays(np.ndarray input not None, np.ndarray output not None):
    cdef np.uint8_t[:] ibuf
    cdef np.uint8_t[:] obuf

    ibuf = input.view(np.uint8)
    obuf = output.view(np.uint8)
    lib6502_configure_state_arrays(&ibuf[0], &obuf[0])

def next_frame(np.ndarray input not None, np.ndarray output not None, np.ndarray debug not None):
    cdef np.uint8_t[:] ibuf  # ignored for this emulator
    cdef np.uint8_t[:] obuf
    cdef np.uint8_t[:] dbuf

    ibuf = input.view(np.uint8)
    obuf = output.view(np.uint8)
    dbuf = debug.view(np.uint8)
    lib6502_next_frame(&ibuf[0], &obuf[0], &dbuf[0])

def get_current_state(np.ndarray output not None):
    cdef np.uint8_t[:] obuf

    obuf = output.view(np.uint8)
    lib6502_get_current_state(&obuf[0])

def load_disk(int disknum, char *filename, int readonly=0):
    raise NotImplementedError

def restore_state(np.ndarray state not None):
    cdef np.uint8_t[:] sbuf
    sbuf = state.view(np.uint8)
    lib6502_restore_state(&sbuf[0])

def monitor_step(int addr=-1):
    lib6502_step_cpu()
    return False

def monitor_summary():
    print("in 6502 monitor")

def monitor_clear():
    pass

def breakpoint_set(int addr):
    pass

def breakpoint_clear():
    pass
