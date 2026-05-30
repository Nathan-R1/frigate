import sys


class Screen:
    def __init__(self):
        self._line_count = 0

    def render(self, lines):
        sys.stdout.write("\033[H\033[J")
        for line in lines:
            sys.stdout.write(line)
            sys.stdout.write("\n")
        sys.stdout.flush()
        self._line_count = len(lines)

    def input(self, prompt=""):
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        try:
            s = sys.stdin.readline()
        except (EOFError, KeyboardInterrupt):
            return "q"
        return s.strip().lower()
