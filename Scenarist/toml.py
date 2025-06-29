# file wrapper for more convinient workflow with TOML
from typing import BinaryIO, Mapping, Any, IO


def load(fp: IO[bytes], /, *, parse_float=float):
    import tomllib
    return tomllib.load(fp, parse_float=parse_float)


def loads(string: str, /, *, parse_float=float):
    import tomllib
    return tomllib.loads(string, parse_float=parse_float)


def dump(obj: Mapping[str, Any], fp: IO[bytes], /, *, multiline_strings: bool = False, indent: int = 4):
    import tomli_w
    return tomli_w.dump(obj, fp, multiline_strings=multiline_strings, indent=indent)


def dumps(obj: Mapping[str, Any], /, *, multiline_strings: bool = False, indent: int = 4):
    import tomli_w
    return tomli_w.dumps(obj, multiline_strings=multiline_strings, indent=indent)
