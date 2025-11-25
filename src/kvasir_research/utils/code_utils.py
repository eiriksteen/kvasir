import re
from pathlib import Path

from kvasir_research.secrets import READABLE_EXTENSIONS


def parse_code(python_code: str) -> str:
    matches = re.findall(r'```(?:\w+\n)?(.*?)```', python_code, re.DOTALL)
    if matches:
        return "\n\n".join(matches).strip()

    return python_code.strip()


def add_line_numbers_to_script(script: str) -> str:
    script = script.strip()
    lines = [line for line in script.splitlines()]
    max_width = len(str(len(lines)))
    return "\n".join(f"{str(i+1).rjust(max_width)}. {line}" for i, line in enumerate(lines))


def remove_line_numbers_from_script(script: str) -> str:
    lines = [line for line in script.splitlines()]
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(re.sub(r'^\d+\.\s?', '', line.strip()))

    return "\n".join(cleaned_lines)


def replace_lines_in_script(
        script: str,
        line_number_start: int,
        line_number_end: int,
        new_code: str,
        script_has_line_numbers: bool = False
) -> str:

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    lines = [line for line in script.splitlines()]
    new_lines = [line for line in new_code.splitlines()]

    lines[line_number_start-1:line_number_end] = new_lines
    updated_script = "\n".join(lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def add_lines_to_script_at_line(
        script: str,
        new_code: str,
        start_line: int,
        script_has_line_numbers: bool = False) -> str:

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    script_lines = [line for line in script.splitlines()]
    lines_to_add = [line for line in new_code.splitlines()]
    start_line_idx = max(0, min(start_line - 1, len(script_lines)))

    updated_lines = script_lines[:start_line_idx] + \
        lines_to_add + script_lines[start_line_idx:]
    updated_script = "\n".join(updated_lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def delete_lines_from_script(
        script: str,
        line_number_start: int,
        line_number_end: int,
        script_has_line_numbers: bool = False) -> str:

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    lines = [line for line in script.splitlines()]
    line_number_start_idx = max(0, min(line_number_start - 1, len(lines) - 1))
    line_number_end_idx = max(line_number_start_idx, min(
        line_number_end - 1, len(lines) - 1))

    updated_lines = lines[:line_number_start_idx] + \
        lines[line_number_end_idx + 1:]
    updated_script = "\n".join(updated_lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def remove_print_statements_from_code(code: str) -> str:
    """Remove print statements, replacing with pass if they're the only statement in a block."""
    lines = code.split('\n')
    cleaned_lines = []

    for line in lines:
        original_line = line
        cleaned_line = line

        while True:
            match = re.search(r'\bprint\s*\(', cleaned_line)
            if not match:
                break

            start_pos = match.end() - 1
            paren_count = 1
            pos = start_pos + 1
            in_string = False
            string_char = None
            escape_next = False

            while pos < len(cleaned_line) and paren_count > 0:
                char = cleaned_line[pos]

                if escape_next:
                    escape_next = False
                    pos += 1
                    continue

                if char == '\\':
                    escape_next = True
                    pos += 1
                    continue

                if char in ('"', "'"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None

                if not in_string:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1

                pos += 1

            cleaned_line = cleaned_line[:match.start()] + cleaned_line[pos:]

        if original_line.strip() == '':
            cleaned_lines.append(original_line)
        elif cleaned_line.strip() != '':
            cleaned_lines.append(cleaned_line)
        else:
            needs_pass = False
            for j in range(len(cleaned_lines) - 1, -1, -1):
                prev_line = cleaned_lines[j]
                if prev_line.strip():
                    if prev_line.rstrip().endswith(':'):
                        needs_pass = True
                    break

            if needs_pass:
                indent = len(original_line) - len(original_line.lstrip())
                cleaned_lines.append(' ' * indent + 'pass')

    return '\n'.join(cleaned_lines)


def is_readable_extension(file_path: str | Path) -> bool:
    file_path_str = str(file_path).lower()
    return any(file_path_str.endswith(ext) for ext in READABLE_EXTENSIONS)


def filter_content_by_extension(file_path: str | Path, content: str, placeholder: str = "content too long for display") -> str:
    if is_readable_extension(file_path):
        return content
    return placeholder
