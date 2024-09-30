from . import instructions
from pathlib import Path
from .type_system import *
from .virtual_machine import *
from .exceptions import InvalidInstruction, ParseException, RuntimeException, UnclosedBlock, UnexpectedEnd, UnresolvedImport


def get_instruction(line: str) -> tuple[str, str]:
    instruction = ''
    index = 0

    for index, char in enumerate(line, start=1):
        if not instruction and char == ';': break
        if instruction and char in ' ;': break
        if char == ' ': continue
        instruction += char

    return instruction, line[index:]


def resolve_import(import_path: str, source_path: Path, libs_path: Path, position: tuple[int, int]) -> Path:
    if source_path.is_file(): source_path = source_path.parent
    path = Path(import_path)

    if not path.is_absolute():
        import_source = source_path / path
        import_lib = libs_path / path

        if import_lib.is_file(): path = import_lib
        if import_source.is_file(): path = import_source

    if path.is_file():
        return path
    else:
        raise UnresolvedImport(f'Import "{import_path}" could not be resolved', file=source_path, position=position)


def parse_source(source_path: Path, libs_path: Path, vm: VirtualMachine) -> None:
    source_file = source_path.open(encoding='utf-8')
    blocks: list[Instruction] = list()
    local_vars: dict[str, Object] = dict()
    current_line: int = -1

    while line := source_file.readline():
        if line.endswith('\n'): line = line[:-1]
        current_line += 1
        instruction, args_str = get_instruction(line)

        if not instruction: continue

        current_char = line.find(instruction)

        if instruction in instructions.GENERIC:
            metadata = Metadata(source_path, (current_line, current_char), len(vm.instruction_list), -1)
            args = get_object_list(args_str, file=source_path, position=metadata.position)
            vm.instruction_list.append(instructions.GENERIC[instruction](vm, local_vars, args, metadata))
            continue

        if instruction in instructions.BLOCKS_START:
            metadata = Metadata(source_path, (current_line, current_char), len(vm.instruction_list), -1)
            args = get_object_list(args_str, file=source_path, position=metadata.position)
            block_start = instructions.BLOCKS_START[instruction](vm, local_vars, args, metadata)
            vm.instruction_list.append(block_start)
            blocks.append(block_start)
            continue

        if instruction in instructions.BLOCKS_END:
            metadata = Metadata(source_path, (current_line, current_char), len(vm.instruction_list), -1)
            args = get_object_list(args_str, file=source_path, position=metadata.position)
            vm.instruction_list.append(instructions.BLOCKS_END[instruction](vm, local_vars, args, metadata))
            if not blocks:
                raise UnexpectedEnd('Unexpected End', file=source_path, position=metadata.position)
            blocks.pop().metadata.jump_address = metadata.address
            continue

        if instruction in instructions.IMPORT:
            offset = len(vm.instruction_list)
            metadata = Metadata(source_path, (current_line, current_char), len(vm.instruction_list), -1)
            args = get_object_list(args_str, file=source_path, position=metadata.position)
            instructions.IMPORT[instruction](vm, local_vars, args, metadata).execute()
            module_path = resolve_import(args[0].value, source_path, libs_path, metadata.position)
            module_vm = VirtualMachine()
            module_vm.stdout.close()
            parse_source(module_path, libs_path, module_vm)
            for instruction in module_vm.instruction_list:
                instruction.vm = vm
                instruction.metadata.address += offset
                instruction.metadata.jump_address += offset
                vm.instruction_list.append(instruction)
            continue

        raise InvalidInstruction(f'Instruction "{instruction}" does not exist', file=source_path,  position=(current_line, current_char))
    
    if blocks:
        raise UnclosedBlock(f'Block {blocks[-1]} was never closed', file=source_path, position=blocks[-1].metadata.position)


def execute_source(source_path: Path, libs_path: Path) -> None:
    vm = VirtualMachine()
    try:
        parse_source(source_path, libs_path, vm)
        while vm.is_running: vm.execute_next()
        print(vm.stdout.getvalue())
    except ParseException as err:
        print(f'ERROR DURING PARSING: {err}')
        print(f'IN FILE "{err.file}" ({err.position[0] + 1}:{err.position[1]})')
        with err.file.open(encoding='utf-8') as file:
            for _ in range(err.position[0]):
                file.readline()
            line = file.readline()
            if line.endswith('\n'):
                line = line[:-1]
            print(line)
            print(' ' * err.position[1] + '^' * (len(line) - err.position[1]))
    except RuntimeException as err:
        print(vm.stdout.getvalue())
        print(f'ERROR DURING RUNTIME: {err}')
        instruction = vm.instruction_list[vm.instruction_pointer]
        position = instruction.metadata.position
        print(f'IN FILE "{instruction.metadata.file}" ({position[0] + 1}:{position[1]}) AT "{instruction.name}"')
        with instruction.metadata.file.open(encoding='utf-8') as file:
            for _ in range(position[0]): file.readline()
            line = file.readline()
            if line.endswith('\n'):
                line = line[:-1]
            print(line)
            print(' ' * position[1] + '^' * (len(line) - position[1]))
    except Exception as err:
        print(vm.stdout.getvalue())
        print(f'OTHER ERROR: {err}')

    vm.stdout.close()
