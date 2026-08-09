from argparse import ArgumentParser
from interpreter import Interpreter
from globals import VERSION, errors, global_interpretter
from parser import Parser

def start(data: list[str]):
    parser = Parser(data)
    translated = parser.parse()
    #print(translated)
    interpreter = Interpreter(translated)
    global_interpretter[0] = interpreter
    interpreter.run()


argument_parser = ArgumentParser(
    f"Penguin Interpreter {VERSION}"
)

argument_parser.add_argument("-f", "--file")

args = argument_parser.parse_args()

if args.file:
    try:
        with open(args.file, "r") as file:
            data = file.read()

    except Exception as e:
        print(errors["file_not_found"])
        exit(1)

    start(data.split("\n"))


