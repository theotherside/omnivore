import os
import tempfile

import numpy as np

from atrcopy import find_diskimage

from .debugger import Debugger
from .debugger.dtypes import FRAME_STATUS_DTYPE

import logging
log = logging.getLogger(__name__)


# Values must correspond to values in libdebugger.h
FRAME_START = 0
FRAME_FINISHED = 1
FRAME_BREAKPOINT = 2
FRAME_WATCHPOINT = 3


class EmulatorBase(Debugger):
    cpu = "<base>"
    name = "<name>"
    pretty_name = "<pretty name>"

    mime_prefix = "<mime type>"

    input_array_dtype = None
    output_array_dtype = None
    width = 320
    height = 192

    low_level_interface = None  # cython module; e.g.: libatari800, lib6502

    def __init__(self):
        Debugger.__init__(self)
        self.input_raw = np.zeros([self.input_array_dtype.itemsize], dtype=np.uint8)
        self.input = self.input_raw.view(dtype=self.input_array_dtype)
        self.output_raw = np.zeros([FRAME_STATUS_DTYPE.itemsize + self.output_array_dtype.itemsize], dtype=np.uint8)
        self.status = self.output_raw[0:FRAME_STATUS_DTYPE.itemsize].view(dtype=FRAME_STATUS_DTYPE)
        self.output = self.output_raw[FRAME_STATUS_DTYPE.itemsize:].view(dtype=self.output_array_dtype)

        self.bootfile = None
        self.frame_count = 0
        self.frame_event = []
        self.history = {}
        self.offsets = None
        self.names = None
        self.save_state_memory_blocks = None
        self.active_event_loop = None
        self.main_memory = None
        self.compute_color_map()
        self.screen_rgb, self.screen_rgba = self.calc_screens()
        self.last_boot_state = None

    @property
    def raw_array(self):
        return self.output_raw

    @property
    def raw_state(self):
        return self.output_raw[self.state_start_offset:]

    @property
    def video_array(self):
        return self.output['video'][0]

    @property
    def audio_array(self):
        return self.output['audio'][0]

    @property
    def state_array(self):
        return self.output['state'][0]

    @property
    def memory_access_array(self):
        return self.status['memory_access'][0]

    @property
    def access_type_array(self):
        return self.status['access_type'][0]

    @property
    def current_frame_number(self):
        return self.status['frame_number'][0]

    @property
    def is_frame_finished(self):
        return self.status['frame_status'][0] == FRAME_FINISHED

    @property
    def current_cycle_in_frame(self):
        return self.status['current_cycle_in_frame'][0]

    @property
    def cycles_user(self):
        return self.status['cycles_user'][0]

    @property
    def cycles_since_power_on(self):
        return self.status['cycles_since_power_on'][0]

    @property
    def break_condition(self):
        if self.status['frame_status'][0] == FRAME_BREAKPOINT:
            bpid = self.status['breakpoint_id'][0]
            return self.get_breakpoint(bpid)
        elif self.status['frame_status'][0] == FRAME_WATCHPOINT:
            bpid = self.status['breakpoint_id'][0]
            return self.get_watchpoint(bpid)
        else:
            return None

    @property
    def stack_pointer(self):
        raise NotImplementedError("define stack_pointer property in subclass")

    @property
    def program_counter(self):
        raise NotImplementedError("define stack_pointer property in subclass")

    @program_counter.setter
    def program_counter(self, value):
        raise NotImplementedError("define stack_pointer property in subclass")

    @property
    def current_cpu_status(self):
        return "not running"

    @classmethod
    def guess_from_document(cls, document):
        try:
            mime = document.metadata.mime
        except:
            pass
        else:
            if mime.startswith(cls.mime_prefix):
                return True
        return False

    ##### Video

    def compute_color_map(self):
        pass

    def calc_screens(self):
        rgb = np.empty((self.height, self.width, 3), np.uint8)
        rgba = np.empty((self.height, self.width, 4), np.uint8)
        return rgb, rgba

    ##### Object serialization

    def report_configuration(self):
        """Return dictionary of configuration parameters"""
        return {}

    def update_configuration(self, conf):
        """Sets some configuration parameters based on the input dictionary.

        Only the parameters specified by the dictionary members are updated,
        other parameters not mentioned are unchanged.
        """
        pass

    def serialize_state(self, mdict):
        return {"name": self.name}

    ##### Initialization

    def configure_emulator(self, emu_args=None, *args, **kwargs):
        self.args = self.process_args(emu_args)
        self.low_level_interface.clear_state_arrays(self.input, self.output_raw)
        self.low_level_interface.start_emulator(self.args)
        self.configure_io_arrays()

    def configure_io_arrays(self):
        self.low_level_interface.configure_state_arrays(self.input, self.output_raw)
        self.parse_state()
        self.generate_save_state_memory_blocks()
        self.cpu_state = self.calc_cpu_data_array()
        self.main_memory = self.calc_main_memory_array()

    def process_args(self, emu_args):
        return emu_args if emu_args else []

    def add_segment_to_memory(self, segment):
        start = segment.origin
        end = (start + len(segment)) & 0xffff
        count = end - start
        log.debug(f"Copying {segment} to memory: {start:#04x}-{end:#04x}")
        self.main_memory[start:end] = segment.data[:count]

    ##### Machine boot

    def find_default_boot_segment(self, segments):
        for segment in segments:
            if segment.origin > 0:
                return segment
        return None

    def boot_from_segment(self, boot_segment, all_segments):
        if self.bootfile is not None:
            try:
                os.remove(self.bootfile)
                self.bootfile = None
            except:  # MSW raises WindowsError, but that's not defined cross-platform
                log.warning("Unable to remove temporary boot file %s." % self.bootfile)
        if boot_segment is not None:
            fd, self.bootfile = tempfile.mkstemp(".atari_boot_segment")
            fh = os.fdopen(fd, "wb")
            fh.write(boot_segment.data.tobytes())
            fh.close()
            log.debug(f"Created temporary file {self.bootfile} to use as boot disk image")
            self.boot_from_file(self.bootfile)
        else:
            self.bootfile = None

    def boot_from_file(self, filename):
        parser = find_diskimage(filename, True)
        print(f"diskimage: filename={filename} image={parser.image}")
        run_addr = None
        for s in parser.image.segments:
            print(f"segment: {s}")
            try:
                run_addr = s.run_address()
            except AttributeError:
                if run_addr is None:
                    run_addr = s.origin
            self.add_segment_to_memory(s)
        print(f"running at: {hex(run_addr)}")
        self.program_counter = run_addr
        self.last_boot_state = self.calc_current_state()
        self.coldstart()

    def parse_state(self):
        base = np.byte_bounds(self.output_raw)[0]
        self.state_start_offset = np.byte_bounds(self.state_array)[0] - base

        memaccess_offset = np.byte_bounds(self.memory_access_array)[0] - base
        memtype_offset = np.byte_bounds(self.access_type_array)[0] - base
        video_offset = np.byte_bounds(self.video_array)[0] - base
        audio_offset = np.byte_bounds(self.audio_array)[0] - base
        self.save_state_memory_blocks = [
            (memaccess_offset, self.memory_access_array.nbytes, 0, "Memory Access"),
            (memtype_offset, self.access_type_array.nbytes, 0, "Access Type"),
            (video_offset, self.video_array.nbytes, 0, "Video Frame"),
            (audio_offset, self.audio_array.nbytes, 0, "Audio Data"),
        ]

    def generate_save_state_memory_blocks(self):
        pass

    def next_frame(self):
        self.process_key_state()
        if not self.is_frame_finished:
            print(f"next_frame: continuing frame from cycle {self.current_cycle_in_frame} of frame {self.current_frame_number}")
        self.low_level_interface.next_frame(self.input, self.output_raw, self.debug_cmd)
        if self.is_frame_finished:
            self.frame_count += 1
            self.process_frame_events()
            self.save_history()
        return self.break_condition

    def process_frame_events(self):
        still_waiting = []
        for count, callback in self.frame_event:
            if self.frame_count >= count:
                log.debug("processing %s", callback)
                callback()
            else:
                still_waiting.append((count, callback))
        self.frame_event = still_waiting

    def end_emulation(self):
        pass

    def debug_video(self):
        """Return text based view of portion of video array, for debugging
        purposes only so it doesn't have to be fast.
        """
        pass

    def debug_state(self):
        """Show CPU status registers
        """
        print(self.current_cpu_status)

    # Emulator user input functions

    def coldstart(self):
        """Simulate an initial power-on startup.
        """
        pass

    def warmstart(self):
        """Simulate a warm start; i.e. pressing the system reset button
        """
        pass

    def keypress(self, ascii_char):
        """Pass an ascii char to the emulator
        """
        self.send_char(ord(ascii_char))

    def joystick(self, stick_num, direction_value, trigger_pressed=False):
        """Pass a joystick/trigger value to the emulator
        """
        pass

    def paddle(self, paddle_num, paddle_percentage):
        """Pass a paddle value to the emulator
        """
        pass

    def process_key_state(self):
        """Read keyboard and compute any values that should be sent to the
        emulator.
        """
        pass

    ##### Input routines

    def send_char(self, key_char):
        print(f"sending char: {key_char}")
        self.input['keychar'] = key_char
        self.input['keycode'] = 0
        self.input['special'] = 0

    def send_keycode(self, keycode):
        self.input['keychar'] = 0
        self.input['keycode'] = keycode
        self.input['special'] = 0

    def send_special_key(self, key_id):
        self.input['keychar'] = 0
        self.input['keycode'] = 0
        self.input['special'] = key_id

    def clear_keys(self):
        self.input['keychar'] = 0
        self.input['keycode'] = 0
        self.input['special'] = 0

    # Utility functions

    def load_disk(self, drive_num, pathname):
        self.low_level_interface.load_disk(drive_num, pathname)

    def calc_current_state(self):
        return self.output_raw.copy()

    def save_history(self, force=False):
        # History is saved in a big list, which will waste space for empty
        # entries but makes things extremely easy to manage. Simply delete
        # a history entry by setting it to NONE.
        frame_number = int(self.status['frame_number'][0])
        if force or self.frame_count % 10 == 0:
            print(f"Saving history at {frame_number}")
            d = self.calc_current_state()
            self.history[frame_number] = d
            self.print_history(frame_number)

    def get_history(self, frame_number):
        frame_number = int(frame_number)
        raw = self.history[frame_number]
        status = raw[0:FRAME_STATUS_DTYPE.itemsize].view(dtype=FRAME_STATUS_DTYPE)
        output = raw[FRAME_STATUS_DTYPE.itemsize:].view(dtype=self.output_array_dtype)
        return status, output

    def restore_history(self, frame_number):
        print(("restoring state from frame %d" % frame_number))
        frame_number = int(frame_number)
        if frame_number < 0:
            return
        try:
            d = self.history[frame_number]
        except KeyError:
            log.error(f"{frame_number} not in history")
            pass
        else:
            self.low_level_interface.restore_state(d)
            self.output_raw[:] = d
            # self.history[(frame_number + 1):] = []  # remove frames newer than this
            # print(("  %d items remain in history" % len(self.history)))
            # self.frame_event = []

    def print_history(self, frame_number):
        d = self.history[frame_number]
        status = d[:FRAME_STATUS_DTYPE.itemsize].view(dtype=FRAME_STATUS_DTYPE)
        output = d[FRAME_STATUS_DTYPE.itemsize:].view(dtype=self.output_array_dtype)
        print("history[%d] of %d: %d %s" % (status['frame_number'], len(self.history), len(d), output['state'][0][0:8]))

    def get_previous_history(self, frame_cursor):
        n = frame_cursor - 1
        while n > 0:
            if n in self.history:
                return n
            n -= 1
        raise IndexError("No previous frame")

    def get_next_history(self, frame_cursor):
        n = frame_cursor + 1
        largest = max(self.history.keys())
        while n < largest:
            if n in self.history:
                return n
            n += 1
        raise IndexError("No next frame")

    def get_color_indexed_screen(self, frame_number=-1):
        """Return color indexed screen in whatever native format this
        emulator supports
        """
        pass

    def get_frame_rgb(self, frame_number=-1):
        """Return RGB image of the current screen
        """

    def get_frame_rgba(self, frame_number=-1):
        """Return RGBA image of the current screen
        """

    def get_frame_rgba_opengl(self, frame_number=-1):
        """Return RGBA image of the current screen, suitable for use with
        OpenGL (flipped vertically)
        """
