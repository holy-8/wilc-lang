import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from .exceptions import InvalidObject


__ALL__ = ['Type', 'Object', 'get_object_list']


class Type(Enum):
    NAME = auto()
    INTEGER = auto()
    STRING = auto()
    LIST = auto()
    ANY = auto()


@dataclass
class Object[T]:
    type: Type
    value: T


def _convert_to_object(string: str, file: Path, position: tuple[int, int]) -> Object:
    if match := re.fullmatch(r'-?\d+', string):
        return Object[int](Type.INTEGER, int(match.string))

    if match := re.search(r'(?<=").*(?=")', string):
        if len(match.group()) == len(string) - 2:
            return Object[str](Type.STRING, match.group())

    if match := re.search(r'(?<=\[)(\d+\s*,\s*)*\d+(?=\])', string):
        if len(match.group()) == len(string) - 2:
            return Object[list](Type.LIST, [int(elem) for elem in match.group().split(',')])

    if match := re.fullmatch(r'\[\s*\]', string):
        return Object[list](Type.LIST, [])

    if match := re.fullmatch(r'\w+', string):
        return Object[str](Type.NAME, match.string)

    raise InvalidObject(f'Failed to convert {string} into Object', file=file, position=position)


def get_object_list(string: str, file: Path,position: tuple[int, int]) -> list[Object]:
    object_list: list[Object] = []
    current_object: str = ''
    skip_until: str | None = None

    for char in string:
        if skip_until:
            current_object += char
            if char == skip_until: skip_until = None
        elif char in ' \t':
            if current_object: object_list.append(_convert_to_object(current_object, file=file, position=position))
            current_object = ''
        elif char == ';':
            break
        else:
            if char == '"': skip_until = '"'
            if char == '[': skip_until = ']'
            current_object += char

    if current_object: object_list.append(_convert_to_object(current_object, file=file, position=position))
    return object_list
