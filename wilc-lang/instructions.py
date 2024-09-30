from .type_system import *
from .virtual_machine import *


type Category = dict[str, type[Instruction]]

GENERIC: Category = {}
BLOCKS_START: Category = {}
BLOCKS_END: Category = {}
IMPORT: Category = {}


def categorize(category: Category, name: str | None = None):
    def deco(cls: type[Instruction]) -> type[Instruction]:
        if name is None:
            category[cls.__name__] = cls
        else:
            cls.name = name
            category[name] = cls
        return cls
    return deco


@categorize(category=GENERIC)
class Print(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.STRING])

        formatted = self.vm.try_format(resolved_args[0], self.local_vars)
        self.vm.stdout.write(formatted.value)


@categorize(category=GENERIC)
class PrintLine(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.STRING])

        formatted = self.vm.try_format(resolved_args[0], self.local_vars)
        self.vm.stdout.write(formatted.value + '\n')


@categorize(category=GENERIC, name='Global::Let')
class GlobalLet(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.args[:1] + self.resolve_args(self.args[1:])
        self.expect_types(resolved_args, [Type.NAME, Type.ANY])

        self.vm.global_vars[resolved_args[0].value] = resolved_args[1]


@categorize(category=GENERIC, name='Local::Let')
class LocalLet(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.args[:1] + self.resolve_args(self.args[1:])
        self.expect_types(resolved_args, [Type.NAME, Type.ANY])

        self.local_vars[resolved_args[0].value] = resolved_args[1]


@categorize(category=GENERIC)
class Del(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        self.resolve_args(self.args)
        self.expect_types(self.args, [Type.NAME])

        try:
            del self.local_vars[self.args[0].value]
        except KeyError:
            del self.vm.global_vars[self.args[0].value]


@categorize(category=BLOCKS_START)
class Label(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        self.expect_types(self.args, [Type.NAME])

        if self.args[0].value in self.local_vars:
            self.local_vars[self.args[0].value] = Object[int](Type.INTEGER, self.metadata.address)
        else:
            self.vm.global_vars[self.args[0].value] = Object[int](Type.INTEGER, self.metadata.address)
        self.vm.instruction_pointer = self.metadata.jump_address


@categorize(category=BLOCKS_START)
class IfEqual(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER])

        if resolved_args[0].value != resolved_args[1].value:
            self.vm.instruction_pointer = self.metadata.jump_address


@categorize(category=BLOCKS_START)
class IfLessThan(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER])

        if not(resolved_args[0].value < resolved_args[1].value):
            self.vm.instruction_pointer = self.metadata.jump_address


@categorize(category=BLOCKS_START)
class IfGreaterThan(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER])

        if not(resolved_args[0].value > resolved_args[1].value):
            self.vm.instruction_pointer = self.metadata.jump_address


@categorize(category=BLOCKS_END)
class End(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 0)


@categorize(category=GENERIC)
class Jump(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.INTEGER])

        self.vm.instruction_pointer = resolved_args[0].value


@categorize(category=GENERIC)
class Exit(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 0)
        self.vm.instruction_pointer = len(self.vm.instruction_list)


@categorize(category=GENERIC)
class Add(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args[:2]) + self.args[2:]
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER, Type.NAME])

        if resolved_args[2].value in self.local_vars:
            self.local_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value + resolved_args[1].value)
        else:
            self.vm.global_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value + resolved_args[1].value)


@categorize(category=GENERIC)
class Subtract(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args[:2]) + self.args[2:]
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER, Type.NAME])

        if resolved_args[2].value in self.local_vars:
            self.local_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value - resolved_args[1].value)
        else:
            self.vm.global_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value - resolved_args[1].value)


@categorize(category=GENERIC)
class And(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args[:2]) + self.args[2:]
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER, Type.NAME])

        if resolved_args[2].value in self.local_vars:
            self.local_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value & resolved_args[1].value)
        else:
            self.vm.global_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value & resolved_args[1].value)


@categorize(category=GENERIC)
class Or(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args[:2]) + self.args[2:]
        self.expect_types(resolved_args, [Type.INTEGER, Type.INTEGER, Type.NAME])

        if resolved_args[2].value in self.local_vars:
            self.local_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value | resolved_args[1].value)
        else:
            self.vm.global_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value | resolved_args[1].value)


@categorize(category=GENERIC)
class Not(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args[:1]) + self.args[1:]
        self.expect_types(resolved_args, [Type.INTEGER, Type.NAME])

        if resolved_args[1].value in self.local_vars:
            self.local_vars[resolved_args[1].value] = Object[int](Type.INTEGER, ~resolved_args[0].value)
        else:
            self.vm.global_vars[resolved_args[1].value] = Object[int](Type.INTEGER, ~resolved_args[0].value)


@categorize(category=GENERIC, name='List::GetItem')
class ListGetItem(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args[:2]) + self.args[2:]
        self.expect_types(resolved_args, [Type.LIST, Type.INTEGER, Type.NAME])

        if resolved_args[2].value in self.local_vars:
            self.local_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value[resolved_args[1].value])
        else:
            self.vm.global_vars[resolved_args[2].value] = Object[int](Type.INTEGER, resolved_args[0].value[resolved_args[1].value])


@categorize(category=GENERIC, name='List::SetItem')
class ListSetItem(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 3)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.LIST, Type.INTEGER, Type.INTEGER])

        resolved_args[0].value[resolved_args[1].value] = resolved_args[2].value


@categorize(category=GENERIC, name='List::Push')
class ListPush(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.LIST, Type.INTEGER])

        resolved_args[0].value.append(resolved_args[1].value)


@categorize(category=GENERIC, name='List::Remove')
class ListRemove(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args)
        self.expect_types(resolved_args, [Type.LIST, Type.INTEGER])

        resolved_args[0].value.pop(resolved_args[1].value)


@categorize(category=GENERIC, name='List::GetSize')
class ListGetSize(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args[:1]) + self.args[1:]
        self.expect_types(resolved_args, [Type.LIST, Type.NAME])

        if resolved_args[1].value in self.local_vars:
            self.local_vars[resolved_args[1].value] = Object[int](Type.INTEGER, len(resolved_args[0].value))
        else:
            self.vm.global_vars[resolved_args[1].value] = Object[int](Type.INTEGER, len(resolved_args[0].value))


@categorize(category=GENERIC, name='List::ToString')
class ListToString(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args[:1]) + self.args[1:]
        self.expect_types(resolved_args, [Type.LIST, Type.NAME])

        if resolved_args[1].value in self.local_vars:
            self.local_vars[resolved_args[1].value] = Object[str](Type.STRING, ''.join(chr(i) for i in resolved_args[0].value))
        else:
            self.vm.global_vars[resolved_args[1].value] = Object[str](Type.STRING, ''.join(chr(i) for i in resolved_args[0].value))


@categorize(category=GENERIC, name='String::ToList')
class StringToList(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 2)
        resolved_args = self.resolve_args(self.args[:1]) + self.args[1:]
        self.expect_types(resolved_args, [Type.STRING, Type.NAME])

        if resolved_args[1].value in self.local_vars:
            self.local_vars[resolved_args[1].value] = Object[list](Type.LIST, [ord(c) for c in resolved_args[0].value])
        else:
            self.vm.global_vars[resolved_args[1].value] = Object[list](Type.LIST, [ord(c) for c in resolved_args[0].value])


@categorize(category=IMPORT)
class Import(Instruction):
    def execute(self) -> None:
        self.expect_count(self.args, 1)
        self.expect_types(self.args, [Type.STRING])
