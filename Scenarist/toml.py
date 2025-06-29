# file wrapper for more convinient workflow with TOML
from typing import Mapping, Any, IO, BinaryIO, TextIO


def load(fp: TextIO, /, *, parse_float=float):
    import tomllib
    content = fp.read()
    return tomllib.loads(content, parse_float=parse_float)


def loads(string: str, /, *, parse_float=float):
    import tomllib
    return tomllib.loads(string, parse_float=parse_float)


def dump(obj: Mapping[str, Any], fp: TextIO, /, *, multiline_strings: bool = False, indent: int = 4):
    import tomli_w
    content = tomli_w.dumps(obj, multiline_strings=multiline_strings, indent=indent)
    fp.write(content)


def dumps(obj: Mapping[str, Any], /, *, multiline_strings: bool = False, indent: int = 4):
    import tomli_w
    tomli_w.dumps(obj, multiline_strings=multiline_strings, indent=indent)
