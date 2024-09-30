from pathlib import Path


__ALL__ = [
    'ParseException', 'RuntimeException',' InvalidObject',
    'InvalidInstruction', 'UnexpectedEnd', 'UnclosedBlock',
    'InvalidName', 'InvalidArgumentCount'
]


class ParseException(Exception):
    def __init__(self, *args: object, file: Path, position: tuple[int, int]) -> None:
        super().__init__(*args)
        self.position = position
        self.file = file


class RuntimeException(Exception):
    pass


class InvalidObject(ParseException):
    pass


class InvalidInstruction(ParseException):
    pass


class UnexpectedEnd(ParseException):
    pass


class UnclosedBlock(ParseException):
    pass


class UnresolvedImport(ParseException):
    pass


class InvalidName(RuntimeException):
    pass


class InvalidArgumentCount(RuntimeException):
    pass


class InvalidArgumentType(RuntimeException):
    pass
