VERSION = "0.0.3"
STANDART_LITERAL_ADDITION = 4  # На сколько в структурах литерал будет убавлятся или прибавлятся
global_interpretter = [None]  # Первым аргументом всегда первый обьект интерпритатора, для наследования созданных функций в коде 
variables = {}
errors = {
    "file_not_found": f"\x1b[31m[ ! ] An error occurred while attempting to read the file.\x1b[0m",
    "var_is_underfined": f"\x1b[31m[ ! ] Variable is undefined\x1b[0m",
    "instruction_not_found": f"\x1b[31m[ ! ] Instruction not found\x1b[0m",
    "strange_command": f"\x1b[31m[ ! ] The string is not recognized as a command or structure.\x1b[0m",
    "data_not_valid": f"\x1b[31m[ ! ] Data is not valid, can't figure out the type. \x1b[0m",
    "function_not_found": f"\x1b[31m[ ! ] Function not found, check the spelling.\x1b[0m",
    "structure_not_found": f"\x1b[31m[ ! ] Structure not found, check the spelling.\x1b[0m",
    "arguments_not_valid": f"\x1b[31m[ ! ] The arguments provided are invalid or do not meet the standards.\x1b[0m",
    "type_error": f"\x1b[31m[ ! ] Cannot perform an operation on the types.\x1b[0m",
    "invalid_literal": f"\x1b[31m[ ! ] Invalid literal for structure, maybe you not open structure?.\x1b[0m",
    "arifmetic_error": f"\x1b[31m[ ! ] The specified arithmetic expression is incorrect.\x1b[0m",
    "return_outside": f"\x1b[31m[ ! ] We are not in function, you can't return value\x1b[0m",
    "include_error": f"\x1b[31m[ ! ] Can't include file, something went wrong.\x1b[0m"
}