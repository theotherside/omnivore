import numpy as np

from traits.api import HasTraits, provides

from atrcopy import SegmentData, SegmentParser, errors, ObjSegment, get_style_bits

from omnivore_framework.file_type.i_file_recognizer import IFileRecognizer
from ..document import SegmentedDocument

try:
    from pyatari800 import parse_atari800
except ImportError:
    parse_atari800 = None


@provides(IFileRecognizer)
class Atari800Recognizer(HasTraits):
    name = "Atari800 Emulator Save State"

    id = "application/vnd.atari800.savestate"

    before = "application/vnd.atrcopy"

    def identify(self, guess):
        r = SegmentData(guess.numpy)
        try:
            parser = Atari800Parser(r)
        except errors.InvalidSegmentParser:
            return
        guess.parser = parser
        return self.id

    def load(self, guess):
        doc = SegmentedDocument(metadata=guess.metadata, raw_bytes=guess.numpy)
        doc.load_metadata_before_editor(guess)
        return doc

Atari800_MACHINE_XLXE = 1

class Atari800Parser(SegmentParser):
    menu_name = "Atari800 Save State"

    format = np.dtype([
        ('magic', 'S8'),
        ('version', 'u1'),
        ('verbose', 'u1'),
        ])

    def parse(self):
        d = self.segment_data.data
        values = d[0:10].view(self.format)[0]
        if values[0] == "ATARI800":
            if values[1] == 8 and (values[2] == 0 or values[2] == 1):
                self.parse_segments()
                return
        raise errors.InvalidSegmentParser("Not Atari800 save state")

    def parse_segments(self):
        r = self.segment_data
        self.container = self.container_segment(r, 0, name=self.menu_name)
        self.segments.append(self.container)
        d = r.get_data()
        s = r.get_style()
        s[:] = get_style_bits(data=True)
        segment = ObjSegment(r[0:10], 0, 0, 0, name="Header")
        segment.set_comment_at(0x00, "Magic")
        segment.set_comment_at(0x08, "Version")
        segment.set_comment_at(0x09, "Verbose")
        self.segments.append(segment)

        self.version = d[8]
        self.verbose = d[9]
        if self.version == 8:
            comments, segments = parse_atari800(d)
            self.set_comments(comments)
            for start, end, origin, name in segments:
                segment = ObjSegment(r[start:end], 0, 0, origin, name=name)
                self.segments.append(segment)

        else:
            raise errors.InvalidSegmentParser("Unsupported Atari800 save state file version: %d" % version)

    def set_comments(self, comments):
        for loc, text in comments.items():
            self.container.set_comment_at(loc, text)
