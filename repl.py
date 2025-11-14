from interpreter import Lexer, Parser

namespace = {}


def repl(prompt="zlang>>> "):
    print("Welcome to zlang REPL.")
    print("Type 'exit()' to exit the program.")
    print("Type 'help()' for help.")
    print()
    while True:
        raw_input = input(prompt).strip()
        if raw_input == "exit()":
            print("Good bye.")
            break
        elif raw_input == "help()":
            print("Type 'exit()' to exit the program.")
            print("Type 'help()' for help.")
        elif not raw_input:
            continue
        try:
            if raw_input.startswith("Lexer("):
                lexer = Lexer(raw_input[6:-1])
                for token in lexer:
                    print(token)
            if raw_input.startswith("Parser("):
                lexer = Lexer(raw_input[7:-1])
                program = Parser(lexer).parse()
                for stmt in program:
                    print(f"{stmt!s}")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    repl()
