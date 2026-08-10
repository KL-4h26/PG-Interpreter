#from token import Token
from globals import errors, STANDART_LITERAL_ADDITION
import regex
import re

class Parser:
    """
    - Переводит код в удобо читаемый формат для класса Interpreter
    """
    def __init__(self, code: list[str]):
        self.code = code
        self.translated = [
            # Данные формата ([аттрибуты], "общее определение команды", литерал (опционально))
        ]

        # Для структур
        self.literal = 0  # Прибавляется всегда на 4
        
        self.commands_regex = {  # Ожидаемые команды
            # Данные формата РЕГЕКС: функция
            lambda literal=self.literal: fr'^{" " * literal}([a-zA-Z_][a-zA-Z0-9_]*)\s*(:=|\+=|-=|\*=|\/=|%=|\+\+|--|=)\s*(.+?)(?:\s*//.*)?\s*$': self.variable_match,
            lambda literal=self.literal: fr'^{" " * literal}([a-zA-Z_][a-zA-Z0-9_]*)\s*\(((?:[^()]*(?:\((?2)\)[^()]*)*))\)(?:\s*//.*)?\s*$': self.function,
            lambda literal=self.literal: fr'^{" " * literal}([a-zA-Z_][a-zA-Z0-9_]*)\s*\(((?:[^()]*(?:\((?2)\)[^()]*)*))\)\s*\{"{"}(?:\s*//.*)?\s*$': self.structure_open,  # Предназначен для открытия структуры
            lambda literal=self.literal: fr'^{" " * literal}(?:function\s+)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\((?P<args>(?:[^()]*(?:\((?2)\)[^()]*)*))\)\s*\{"{"}(?:\s*//.*)?\s*$': lambda match: self.structure_open(match, True),
            lambda literal=self.literal: fr'^{" " * (literal - 4)}\{"}"}\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(((?:[^()]*(?:\((?2)\)[^()]*)*))\)\s*\{"{"}$': self.structure_alternative,
            lambda literal=self.literal: fr'^{" " * (literal - 4)}{"}"}(?:\s*//.*)?\s*$': self.structure_close,  # Предназначен для закрытия структуры
            lambda literal=self.literal: fr'^{" " * (literal)}([a-zA-Z_][a-zA-Z0-9_]*)\s+(.+?)(?:\s*//.*)?\s*$': self.conditional_instruction,
            lambda literal=self.literal: fr'^{" " * literal}//.*$': lambda mtch: 0  # Заглушка, это комментарий
        }


    def parse(self):
        """
        Парсит каждую строку в коде переводя её в удобочитаемый для интерпритатора формат
        ((.., .., .., ...), "COMMAND_NAME")
        """
        for line in self.code:
            if not line or line.isspace():
                continue  # Что бы не тратить лишнее время 

            for rgx, mthd in self.commands_regex.items():
                match = regex.match(rgx(self.literal), line.rstrip())
                if match:
                    mthd(match)
                    break

            else:
                #print("strng", line, self.literal)
                print(errors["strange_command"])
                exit(1)

        return self.translated


    #=== МАТЧ МЕТОДЫ ===#
    # Матч-методы:  методы которые срабатывают при 
    # нахождении определенных структур команд в линии
    # ВСЕГДА принимают матч

    def conditional_instruction(self, match: re.Match):
        """
        - ОЖИДАЕТСЯ МАТЧ С ДВУМЯ ГРУППАМИ
        1 - имя инструкции
        2 - данные

        Общее определение команды: CONDT_INSTRUCT
        """
        self.translated.append(
            ([grp.strip() for grp in match.groups()], "CONDT_INSTRUCT")
        )
        

    def structure_open(self, match: re.Match = None, define_func: bool = False):
        """
        - Открывает структуру, увеличивает литерал
        - ОЖИДАЕТСЯ МАТЧ С ДВУМЯ ГРУППАМИ
        1 - имя
        2 - Аттрибуты
        
        Опционально в начале может быть function, обозначающий функцию
        При добавлении в translated в конец аттрсов будет добавлен литерал, это требуется для интерпритатора

        Общее определение команды: "STRUCTURE_OPEN"
        """
        self.literal += STANDART_LITERAL_ADDITION

        line = [grp.strip() for grp in match.groups()]

        line[1] = self.attrs_parse(line[1])
        line[1].append(self.literal)

        self.translated.append(
            (line, "STRUCTURE_OPEN" if not define_func else "DEFINE_FUNCTION")
        )


    def structure_alternative(self, match: re.Match):

        line = [grp.strip() for grp in match.groups()]

        line[1] = self.attrs_parse(line[1])
        line[1].append(self.literal)

        self.translated.append(
            (line, "STRUCTURE_ALTERNATIVE")
        )


    def structure_close(self, match: re.Match):
        """
        - Закрывает структуру, уменьшает литерал, в аргументах не требуется

        Общее определение команды: "STRUCTURE_CLOSE"
        """
        if self.literal <= 0:
            print(errors["invalid_literal"])
            exit(1)

        self.literal -= STANDART_LITERAL_ADDITION

        self.translated.append(
            ([self.literal], "STRUCTURE_CLOSE")
        )


    def variable_match(self, match: re.Match):
        """
        - ОЖИДАЕТСЯ МАТЧ С ТРЕМЯ ГРУППАМИ
        1 - имя
        2 - операция
        3 - значение
        
        Общее определение команды: "VAR_OPERATION"
        """
        self.translated.append(
            ([grp.strip() for grp in match.groups()], "VAR_OPERATION")
        )


    def function(self, match: re.Match):
        """
        - ОЖИДАЕТСЯ МАТЧ С МИНИМУМ 1 ГРУППОЙ
        1 - имя функции
        2 - аргументы функции

        Общее определение команды: FUNCTION
        """
        line = [grp.strip() for grp in match.groups()]

        line[1] = self.attrs_parse(line[1])
        self.translated.append(
            (line, "FUNCTION")
        )


    def attrs_parse(self, s):
        """
        Разбивает строку по запятым, игнорируя запятые внутри:
        - одинарных кавычек (')
        - двойных кавычек (")
        - круглых скобок ( )

        Из за большого обилия кода было вынесено в отдельную функцию
        """
        parts = []
        current = []
        in_single = False
        in_double = False
        paren_depth = 0
        i = 0
        n = len(s)

        while i < n:
            ch = s[i]
            # Обработка экранированных кавычек (опционально)
            if ch == '\\' and i + 1 < n and s[i + 1] in ('"', "'"):
                current.append(ch + s[i + 1])
                i += 2
                continue

            # Переключение состояния кавычек
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            # Скобки учитываем только вне кавычек
            elif ch == '(' and not in_single and not in_double:
                paren_depth += 1
            elif ch == ')' and not in_single and not in_double and paren_depth > 0:
                paren_depth -= 1
            # Разделитель - запятая вне кавычек и скобок
            elif ch == ',' and paren_depth == 0 and not in_single and not in_double:
                parts.append(''.join(current).strip())
                current = []
                i += 1
                continue

            current.append(ch)
            i += 1

        if current:
            parts.append(''.join(current).strip())

        return parts

