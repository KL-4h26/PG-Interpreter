from globals import variables, errors, STANDART_LITERAL_ADDITION
from type import DataType
import sys


class Interpreter:
    """
    - Предназначен для выполнения кода 
    Важно что бы код был "пережёван" с использованием класса Parser
    """
    def __init__(self, code: list):
        self.return_value = None  # Меняется только через инструкцию return
        self.we_are_in_custom_function = False

        self.code = code
        self.code_line = 0
        self.commands = {
            "VAR_OPERATION": self.var_operation,
            "FUNCTION": self.function_search,
            "STRUCTURE_OPEN": self.structure_search,
            "STRUCTURE_ALTERNATIVE": self.structure_search,
            "STRUCTURE_CLOSE": self.structure_close,  # Вообще вызыватся не должен (не будет),
            "DEFINE_FUNCTION": self.define_function,
            "CONDT_INSTRUCT": self.conditional_instruction
        }
        self.conditional_instructions = {
            "echo": self.echo,
            "return": self.return_instr,
            "include": self.include_instr
        }
        self.functions = {
            "show": self.show_func,
            "type": self.type_func,
            "input": self.input,
            "lenght": self.len_func,
            "stop": self.stop_func,
            "python": self.python_func,

            # Функции приведения типов
            "tostr": self.str_func,
            "toint": self.int_func,
            "tofloat": self.float_func,
            "tobool": self.bool_func
        }
        self.structures = {
            "if": self.if_struct,
            "else": self.else_struct,
            "elif": self.if_struct,
            "while": self.while_struct
        }
        

    def run(self):
        """
        - Выполняет код построчно (интерпритирует)
        """
        while self.code_line != len(self.code):
            instruction = self.code[self.code_line][1]
            parts = self.code[self.code_line][0]

            command = self.commands.get(instruction)
            
            if not command:
                print(errors["strange_command"])
                sys.exit(1)

            command(*parts)

            self.code_line += 1

            if self.return_value:
                return self.return_value


    #=== КОММАНД МЕТОДЫ ===#
    # Комманд-методы:  методы которые срабатывают при 
    # нахождении определенных указаний команд в линии
    # ВСЕГДА принимают аргументы
    
    def conditional_instruction(self, *args):
        """
        - Находит инструкцию и вызывает её метод
        аргументы формата: ('command', 'value')
        Третий аргумент будет преобразован в DataType
        """
        name = args[0]
        value = DataType(args[1])

        ci = self.conditional_instructions.get(name)

        if not ci:
            print(errors["instruction_not_found"])
            sys.exit(1)

        ci(value)


    def structure_search(self, *args):
        """
        - Выполняет структуру находя нужную по имени
        аргументы формата: ('func_name', [arg1, arg2, agr3 ...], 4) последнее литерал
        Все аргументы проме первого и третьего будут преобразованы в DataType
        """
        struct_name = args[0]
        structure = self.structures.get(struct_name)

        if not structure:
            print(errors["structure_not_found"])
            sys.exit(1)

        attrs = [DataType(attr) for attr in args[1][0:-1]]  # Последнее литерал, не учитываем
        ltrl = args[1][-1]

        code_to_struct_alter = []
        code_to_struct_end = []

        for line in self.code[self.code_line + 1:]:
            if line[1] == "STRUCTURE_ALTERNATIVE" and line[0][1][-1] == ltrl:
                break

            elif line[1] == "STRUCTURE_CLOSE" and line[0][-1] == ltrl - STANDART_LITERAL_ADDITION:
                break

            code_to_struct_alter.append(line)

        for line in self.code[self.code_line + 1:]:
            if line[1] == "STRUCTURE_CLOSE" and line[0][-1] == ltrl - STANDART_LITERAL_ADDITION:
                break

            code_to_struct_end.append(line)

        # Структура выполняется (типо)
        result = structure(code_to_struct_alter, *attrs)

        # Скипаем отрезок (если структура не сработала (вернула False), она переходит К АЛЬТЕРНАТИВУ, инчае фулл скип)
        self.code_line += len(code_to_struct_end) + 1 if result else len(code_to_struct_alter)
    

    def structure_close(self, *args):
        pass  # Ему не нужно ничего выполнять :)


    def define_function(self, *args):
        """
        ДОБАВИТЬ ВАЛИДАЦИЮ ИМЕНИ И АРГУМЕНТОВ (аргументы все должны соответствовать регексу переменных, как и имя)
        """

        func_name = args[0]
        attrs = [attr for attr in args[1][0:-1]]  # Последнее литерал, не учитываем

        ltrl = args[1][-1]

        code_to_struct = []

        for line in self.code[self.code_line + 1:]:
            if line[1] == "STRUCTURE_CLOSE" and line[0][-1] == ltrl - STANDART_LITERAL_ADDITION:
                break

            code_to_struct.append(line)


        # Создаем функцию
        func_exec = f"""
def {func_name}(*args):
    if len(args) != {len(attrs)}:
        print(errors["arguments_not_valid"])
        exit(1)

    attrs = {attrs}

    i = 0

    vars_before = variables.copy()
    while (i != len(attrs)):
        variables[attrs[i]] = args[i]
        i += 1

    interpreter = Interpreter({code_to_struct})
    interpreter.we_are_in_custom_function = True
    result = interpreter.run()

    vars_after = variables.copy()

    for key in vars_before.keys():
        del vars_after[key]

    if vars_after:
        for key in vars_after.keys():
            del variables[key]

    return result


self.functions["{func_name}"] = {func_name}
"""
        exec(func_exec)


        # Скипаем отрезок
        self.code_line += len(code_to_struct) + 1



    def var_operation(self, *args):
        """
        - Выполняет действия над переменной
        аргументы формата: ('num', ':=', '5')
        Третий аргумент будет преобразован в DataType
        """
        var_name = args[0]
        var_operation = args[1]
        var_value = DataType(args[2])

        # Проверка на присутствие переменной (только в случае если знак не присваивания)
        if not variables.get(var_name) and var_operation != ":=":
            print(errors["var_is_underfined"])
            sys.exit(1)

        try:
            match var_operation:
                case ":=":
                    variables[var_name] = var_value

                case "+=":
                    variables[var_name].data += var_value.data

                case "-=":
                    variables[var_name].data -= var_value.data

                case "*=":
                    variables[var_name].data *= var_value.data

                case "/=":
                    variables[var_name].data /= var_value.data

        except TypeError:
            print(errors["type_error"])
            sys.exit(1)



    def function_search(self, *args):
        """
        - Выполняет функцию находя нужную по имени
        аргументы формата: ('func_name', 'arg1, arg2,agr3...')
        Все аргументы проме первого будут преобразованы в DataType
        """
        func_name = args[0]
        attrs = [DataType(attr) for attr in args[1]]
        func = self.functions.get(func_name)

        if not func:
            print(errors["function_not_found"])
            sys.exit(1)

        result = func(*attrs)
        result = f'"{result}"' if type(result) == str else result

        # if result != None нельзя заменить на if result, False так же являетс
        # Допустимым значением
        return DataType(str(result)) if result != None else DataType("0")

    #=== Условные инструкции (упрощенные функции) ===#
    # ВСЕГДА принимают один аргумент

    def include_instr(self, value: DataType):
        """
        Вставка кода из файла
        """
        from parser import Parser
        try:
            with open(value.data, "r") as file:
                parser = Parser(file.read().split("\n")).parse()
                parser.reverse()

                for line in parser:
                    self.code.insert(self.code_line + 1, line)

        except Exception as e:
            print(errors["include_error"])
            exit(1)

    def return_instr(self, value: DataType):
        """
        Возврат значения из функции (если мы в функции)
        """
        if not self.we_are_in_custom_function:
            print(errors["return_outside"])
            sys.exit(1)

        #print(value, value.data)
        self.return_value = value.data


    def echo(self, value: DataType):
        """
        Инструкция для простого вывода
        """
        print(value.data)

    #=== Функции (глобального вида) ===#
    # Принимают любое колличество аргументов, могут возвращать значения DataType

    def python_func(self, *args):
        if len(args) != 1 or not args[0].type in (str,):
            print(errors["arguments_not_valid"])
            sys.exit(1)

        exec(args[0].data)


    def stop_func(self, *args):
        """
        Функция выхода из программы
        """
        exit(0)


    def len_func(self, *args):
        """
        Функция подсчета символов значения, принимает один аргумент
        """
        if len(args) != 1 or not args[0].type in (str,):
            print(errors["arguments_not_valid"])
            sys.exit(1)

        return len(args[0].data)


    def input(self, *args):
        """
        Функция ввода, принимает один опциональный аргумент, text
        """
        return f"'{input(args[0].data if len(args) > 0 else '')}'"


    def show_func(self, *args):
        """
        Функция вывода, принимает любое количество аргументов для вывода
        """
        for arg in args:
            print(arg.data, end=" ")
        print("")


    def type_func(self, *args):
        """
        функция возврата типа значения, принимает один аргумент
        Вернет тип значения
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        types = {
            int: "int",
            str: "str",
            bool: "bool",
            float: "float"
        }

        return f'"{types[args[0].type]}"'  # Оборачиваю в скобки для DataType

    def str_func(self, *args):
        """
        функция преобразует значение DataType в тип str, принимает один аргумент
        Вернет значение с новым типом
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        return str(args[0].data)


    def int_func(self, *args):
        """
        функция преобразует значение DataType в тип int, принимает один аргумент
        Вернет значение с новым типом
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        try:
            return int(args[0].data) if args[0].type != str else int(args[0].data[1:-1])

        except:
            print(errors["type_error"])
            sys.exit(1)


    def float_func(self, *args):
        """
        функция преобразует значение DataType в тип float, принимает один аргумент
        Вернет значение с новым типом
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        try:
            return float(args[0].data) if args[0].type != str else float(args[0].data[1:-1])

        except:
            print(errors["type_error"])
            sys.exit(1)


    def bool_func(self, *args):
        """
        функция преобразует значение DataType в тип float, принимает один аргумент
        Вернет значение с новым типом
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            exit(1)

        try:
            return bool(args[0].data)

        except:
            print(errors["type_error"])
            sys.exit(1)


    #=== Структуры (глобального вида) ===#
    # Принимают любое колличество аргументов, выполняют код с добавлением логики

    def if_struct(self, code, *args):
        """
        - Выполняет код если условие истино
        ПРИНИМАЕТ АРГУМЕНТЫ:
        1. условие
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        elif args[0].type != bool:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        if args[0].data == True:
            interpreter = Interpreter(code)
            interpreter.we_are_in_custom_function = True if self.we_are_in_custom_function else False

            result = interpreter.run()
            if self.we_are_in_custom_function:
                self.return_value = DataType(str(result)).data
                
            return True  # Скипаем

        return False  # Перейти к альтернативу

    def else_struct(self, code, *args):
        interpreter = Interpreter(code)
        interpreter.we_are_in_custom_function = True if self.we_are_in_custom_function else False

        result = interpreter.run()
        if self.we_are_in_custom_function:
            self.return_value = DataType(str(result)).data
            
        return True


    def while_struct(self, code, *args):
        """
        - Выполняет код пока условие истино
        ПРИНИМАЕТ АРГУМЕНТЫ:
        1. условие
        """
        if len(args) != 1:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        elif args[0].type != bool:
            print(errors["arguments_not_valid"])
            sys.exit(1)

        while DataType(args[0].original_data).data == True:
            interpreter = Interpreter(code)
            interpreter.we_are_in_custom_function = True if self.we_are_in_custom_function else False
            result = interpreter.run()
            if self.we_are_in_custom_function:
                self.return_value = DataType(str(result)).data

        return True