import re

import numpy as np

from omnivore_framework.utils.parseutil import NumpyIntExpression, ParseException

import logging
log = logging.getLogger(__name__)


class BaseSearcher(object):
    pretty_name = "<base class>"

    def __init__(self, editor, search_text, **kwargs):
        self.search_text = self.get_search_text(search_text)
        if len(self.search_text) > 0:
            self.matches = self.get_matches(editor)
            self.set_style(editor)
        else:
            self.matches = []

    def get_search_text(self, text):
        return bytearray(text, "utf-8")

    def get_matches(self, editor):
        text = editor.segment.search_copy
        rs = re.escape(str(self.search_text))
        matches = [(i.start(), i.end()) for i in re.finditer(rs, text)]
        return matches

    def set_style(self, editor):
        editor.segment.set_style_ranges(self.matches, match=True)


class HexSearcher(BaseSearcher):
    pretty_name = "hex"

    def __str__(self):
        return "hex matches: %s" % str(self.matches)

    def get_search_text(self, text):
        try:
            return bytearray.fromhex(text)
        except ValueError:
            log.debug("%s: fromhex failed on: %s")
            return ""


class CharSearcher(BaseSearcher):
    pretty_name = "text"

    def __str__(self):
        return "char matches: %s" % str(self.matches)


class CommentSearcher(BaseSearcher):
    pretty_name = "comments"

    def __str__(self):
        return "comment matches: %s" % str(self.matches)

    def get_search_text(self, text):
        return text

    def get_matches(self, editor):
        segment = editor.segment
        s = segment.origin
        matches = []
        if editor.last_search_settings.get('match_case', False):
            search_text = self.search_text
            for index, comment in segment.iter_comments_in_segment():
                if search_text in comment:
                    matches.append((index, index + 1))
        else:
            search_text = self.search_text.lower()
            for index, comment in segment.iter_comments_in_segment():
                if search_text in comment.lower():
                    matches.append((index, index + 1))
        return matches


class AlgorithmSearcher(BaseSearcher):
    def __str__(self):
        return "pyparsing matches: %s" % str(self.matches)

    def get_search_text(self, text):
        return text

    def get_matches(self, editor):
        s = editor.segment
        a = np.arange(s.origin, s.origin + len(s))
        b = np.copy(s.data)
        v = {
            'a': np.arange(s.origin, s.origin + len(s)),
            'b': np.copy(s.data),
            }
        expression = NumpyIntExpression(v)
        try:
            result = expression.eval(self.search_text)
            matches = s.bool_to_ranges(result)
            return matches
        except ParseException as e:
            raise ValueError(e)


known_searchers = [
    HexSearcher,
#    CharSearcher,
#    DisassemblySearcher,
#    CommentSearcher,
    ]
