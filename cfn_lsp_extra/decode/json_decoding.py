# type: ignore
# flake8: noqa
"""
Utilities for parsing json document strings.
"""
import bisect
import json
from json import JSONDecodeError
from json import scanner
from json.decoder import WHITESPACE
from json.decoder import WHITESPACE_STR
from json.decoder import JSONDecoder
from json.decoder import scanstring
from json.scanner import py_make_scanner
from typing import Any
from typing import List

from .yaml_decoding import POSITION_PREFIX
from .yaml_decoding import VALUES_POSITION_PREFIX


# This is a slightly modified version of json.decoder.JSONObject
# added lines have comments starting with 'EDIT:'
def cfn_json_object(
    s_and_end,
    strict,
    scan_once,
    object_hook,
    object_pairs_hook,
    memo=None,
    _w=WHITESPACE.match,
    _ws=WHITESPACE_STR,
):  # pragma: no cover
    s, end = s_and_end
    init = end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end : end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end : end + 1]
        # Trivial empty object
        if nextchar == "}":
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end
            )
    end += 1
    while True:
        key_start = end  # EDIT: gets start position of key
        key, end = scanstring(s, end, strict)
        key_end = end  # EDIT: gets end position of key
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end : end + 1] != ":":
            end = _w(s, end).end()
            if s[end : end + 1] != ":":
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            value_start = end
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs_append((key, value))
        # EDIT: adds positional data to result
        if isinstance(value, str):
            if VALUES_POSITION_PREFIX not in {k for k, _ in pairs}:
                values_lst = []
                pairs_append((VALUES_POSITION_PREFIX, values_lst))
            else:
                values_lst = next(v for k, v in pairs if k == VALUES_POSITION_PREFIX)
            values_lst.append({POSITION_PREFIX + value: [value_start + 1, end + 1]})
        # END EDIT
        pairs_append((POSITION_PREFIX + key, [key_start, key_end]))
        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ""
        end += 1

        if nextchar == "}":
            break
        elif nextchar != ",":
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        end = _w(s, end).end()
        nextchar = s[end : end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1
            )
    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    return pairs, end


class CfnJSONDecoder(JSONDecoder):
    """A json decoder which saves positional information of elements."""

    def __init__(self):
        super().__init__()
        self.parse_object = cfn_json_object
        self.scan_once = py_make_scanner(self)

    def raw_decode(self, s: str, idx: int = 0):
        dct, end = super().raw_decode(s, idx)
        line_starts = [0]
        cnt = 0
        for line in s.splitlines():
            cnt += len(line) + 1  # + 1 for the newline character
            line_starts.append(cnt)
        self._convert_abs_char_to_line_char(dct, line_starts)
        return dct, end

    def _convert_abs_char_to_line_char(self, d: Any, line_starts: List[int]):
        for key, value in d.items():
            if key.startswith(POSITION_PREFIX):
                c_start, _ = value
                line = bisect.bisect_left(line_starts, c_start)
                char = (
                    0
                    if c_start == line_starts[line]
                    else c_start - line_starts[line - 1]
                )
                d[key] = [line - 1, char]
            elif isinstance(value, dict):
                self._convert_abs_char_to_line_char(value, line_starts)
            elif isinstance(value, list):
                for e in value:
                    if isinstance(e, dict):
                        self._convert_abs_char_to_line_char(e, line_starts)
