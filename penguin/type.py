from globals import variables, errors
from arithmetic_eval import evaluate
from boolrule import BoolRule
import random
import string
import regex

class DataType:
    """
    Определяет тип данных или приводит данные к определенному типу
    """
    def __init__(self, data: str):
        self.type = None
        self.data_regex = {
            # Строки в кавычках (одинарных или двойных)
            r'^(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')$': {
                "type": str,
                "act": lambda data: data[1:-1] # Строка без кавычек
            },
            # Строки в кавычках с возможностью подстановки значений
            r'^\$(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')$': {
                "type": str,
                "act": self.format_string
            },
            # Булевое значение
            r"^(True|False)$": {
                "act": lambda data: True if data == "True" else False
            },
            # Переменная
            r"^[a-zA-Z_][a-zA-Z0-9_]*$": {
                "act": self.get_var_val
            },
            # Число с плавающей точкой
            r'[-+]?\d+\.\d+(?:[eE][-+]?\d+)?': {
                "type": float,
                "act": lambda data: float(data)
            },
            # Целое число
            r'^[-+]?\d+$': {
                "type": int,
                "act": lambda data: int(data)
            },
            # Функция как значение для чего либо
            r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(((?:[^()]*(?:\((?2)\)[^()]*)*))\)$': {
                "act": self.func_execute
            },
            # Булевая операция 
            r"^\s*"
            r"(?P<left>.+?)\s*"          # левая часть – всё до оператора (лениво)
            r"(?P<operator>==|!=|>=|<=|>|<)\s*"
            r"(?P<right>.+?)\s*"         # правая часть – всё после оператора (лениво)
            r"$": {
                "act": self.operation_execute
            },
            # Математическое выражение (вставка переменных доступна)
            r'(?:"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[a-zA-Z_]\w*\s*\((?R)\)|\d+(?:\.\d+)?|[a-zA-Z_]\w*)(?:\s*[+\-*/%]\s*(?R))?': {
                "act": self.math_execute
            }
        }
        self.original_data = data
        self.data = self.select_data_type(data)


    def get_var_val(self, data):
        var = variables.get(data)
        if var:
            return var.data

        else:
            print(errors["var_is_underfined"])
            exit(1)

        return lambda data: variables[data].data if variables.get(data) else None

    def select_data_type(self, data: str):
        for rgx, value in self.data_regex.items():
            matches = regex.findall(rgx, data)

            if matches:
                data = data if not value.get("act") else value.get("act")(data)
                self.type = value["type"] if value.get("type") else type(data)

                return data

        else:
            print(errors["data_not_valid"])
            exit(1)

    def format_string(self, data):
        pure_string = data[2:-1]
        
        values_in_string = regex.findall(r':([^:]*):', pure_string)

        for value in values_in_string:
            pure_string =pure_string.replace(f":{value}:", str(DataType(value).data))

        return pure_string
            
    def math_execute(self, example):
        """
        ДА математика потребовала больше логики, мне как то нужно было
        обрабатывать переменные в выражениях
        """
        try:
            exmp = ""
            tokenize = self.arifmetic_tokenize(example)
            vars = {}
            for token in tokenize:
                #exmp += str(DataType(token).data) if not token in ("+", "-", "/", "*", "%") else token
                if token in ("+", "-", "/", "*", "%"):
                    exmp += token

                elif token[0] == "-":
                    indetefy = "".join(random.choices(string.ascii_letters, k=10))
                    exmp += indetefy
                    vars[indetefy] = DataType(token).data


                else:
                    new_token = DataType(token)
                    exmp += f"'{new_token.data}'" if new_token.type == str else str(new_token.data)

            result = evaluate(exmp, vars)

            return result

        except TypeError:
            print(errors["type_error"])
            exit(1)

        except:
            print(errors["arifmetic_error"])
            exit(1)
                

    def operation_execute(self, operation):
        try:
            match = regex.match(
            r"^\s*"
            r"(?P<left>.+?)\s*"          # левая часть – всё до оператора (лениво)
            r"(?P<operator>==|!=|>=|<=|>|<)\s*"
            r"(?P<right>.+?)\s*"         # правая часть – всё после оператора (лениво)
            r"$",
                operation
            )

            if match:
                left, operator, right = match.groups()

                left = DataType(left).data if not variables.get(left) else variables[left].data
                right = DataType(right).data if not variables.get(right) else variables[right].data

                
                rule_with_context = BoolRule(f'left {operator} right')
                return (rule_with_context.test({"left": left, "right": right}))  

        except Exception as e:  # Может сработать если операция не корректная
            print(e)
            return None


    def func_execute(self, func):
        from interpreter import Interpreter
        from globals import global_interpretter
        from parser import Parser
        parse = Parser([func]).parse()
        
        interpreter = Interpreter(parse)
        interpreter.functions = global_interpretter[0].functions

        value = interpreter.function_search(*parse[0][0])

        return value.data


    def arifmetic_tokenize(self, expression):
        # Паттерн для всех токенов, включая отрицательные числа
        pattern = r'''
            (?:
                # Отрицательные числа (минус с пробелами или без)
                -\s*\d+(?:\.\d+)? |
                # Строки
                "(?:\\.|[^"\\])*" |
                '(?:\\.|[^\'\\])*' |
                # Положительные числа
                \d+(?:\.\d+)? |
                # Вызовы функций
                [a-zA-Z_]\w*\s*\((?:(?R)|[^()]*)\) |
                # Идентификаторы
                [a-zA-Z_]\w* |
                # Операторы (включая минус, но он будет перехвачен только если не является частью отрицательного числа)
                [+\-*/%]
            )
        '''
        
        regex_obj = regex.compile(pattern, regex.VERBOSE | regex.DOTALL)
        
        # Находим все совпадения
        matches = regex_obj.findall(expression)
        
        # Фильтруем пустые строки и пробелы
        tokens = [m for m in matches if m.strip()]
        
        return tokens