from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from .exceptions import InvalidArgumentCount, InvalidArgumentType, InvalidName
from .type_system import *


__ALL__ = ['VirtualMachine', 'Metadata', 'Instruction']


@dataclass
class VirtualMachine:
    instruction_pointer: int = field(default=0, init=False)
    instruction_list: list[Instruction] = field(default_factory=list, init=False)
    global_vars: dict[str, Object] = field(default_factory=dict, init=False)
    stdout: StringIO = field(default_factory=StringIO, init=False)

    @property
    def is_running(self) -> bool:
        if not self.instruction_list: return False
        return self.instruction_pointer < len(self.instruction_list)

    def append(self, instruction: Instruction) -> None:
        self.instruction_list.append(instruction)

    def get_variable(self, name: str, local_vars: dict[str, Object]) -> Object:
        if name in local_vars:
            return local_vars[name]
        if name in self.global_vars:
            return self.global_vars[name]

        raise InvalidName(f'Name {name} is not defined')

    def try_format(self, string: Object[str], local_vars: dict[str, Object]) -> Object[str]:
        new_string = Object[str](Type.STRING, string.value)

        for match in re.finditer(r'\{.+?\}', string.value):
            replacement = str(self.get_variable(match.group()[1:-1], local_vars).value)
            new_string.value = new_string.value.replace(match.group(), replacement, 1)

        new_string.value = new_string.value.replace(r'\n', '\n')
        new_string.value = new_string.value.replace(r'\r', '\r')
        new_string.value = new_string.value.replace(r'\t', '\t')

        return new_string

    def execute_next(self) -> None:
        self.instruction_list[self.instruction_pointer].execute()
        self.instruction_pointer += 1


@dataclass
class Metadata:
    file: Path
    position: tuple[int, int]
    address: int
    jump_address: int


@dataclass
class Instruction(ABC):
    vm: VirtualMachine
    local_vars: dict[str, Object]
    args: list[Object]
    metadata: Metadata
    _name: str | None = field(default=None, init=False)

    def __repr__(self) -> str:
        args = ' '.join(
            str(obj.value) if obj.type == Type.STRING else str(obj.value)
            for obj in self.args)
        return f'<{self.name} {args}>'

    @property
    def name(self) -> str:
        if self._name is None:
            return self.__class__.__name__
        else:
            return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def resolve_args(self, received: list[Object]) -> list[Object]:
        return [
            arg if arg.type != Type.NAME
            else self.vm.get_variable(arg.value, self.local_vars)
            for arg in received
        ]

    def expect_count(self, received: list[Object], expected: int) -> None:
        if len(received) != expected:
            raise InvalidArgumentCount(f'Expected {expected} arguments, received {len(received)}')

    def expect_types(self, received: list[Object], expected: list[Type]) -> None:
        for index, arg in enumerate(received):
            if expected[index] == Type.ANY:
                continue
            if arg.type != expected[index]:
                raise InvalidArgumentType(f'Argument {index} must have type {expected[index]}, received {arg.type}')

    @abstractmethod
    def execute(self) -> None:
        pass
