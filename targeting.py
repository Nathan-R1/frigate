import sys
import termios
import tty
import select

from display import render_board, render_ship_status, hex_to_pos, SCALE
from utils import HEX_RADIUS, hex_distance


class TargetSelector:
    def __init__(self, board, start_q, start_r, max_range, action_name, players):
        self.board = board
        self.q = start_q
        self.r = start_r
        self.max_range = max_range
        self.action_name = action_name
        self.players = players
        self._start_q = start_q
        self._start_r = start_r
        self._offset_x = HEX_RADIUS * SCALE

    def select(self):
        old = self._set_raw_mode()
        try:
            while True:
                self._draw()
                key = self._read_key()

                if key == 'ENTER':
                    return (self.q, self.r)

                if key in ('ESC',):
                    return None

                if key == 'UP':
                    nq, nr = self.q, self.r - 1
                    if self.board.is_valid(nq, nr):
                        self.q, self.r = nq, nr

                elif key == 'DOWN':
                    nq, nr = self.q, self.r + 1
                    if self.board.is_valid(nq, nr):
                        self.q, self.r = nq, nr

                elif key == 'LEFT':
                    nq, nr = self.q - 1, self.r
                    if self.board.is_valid(nq, nr):
                        self.q, self.r = nq, nr

                elif key == 'RIGHT':
                    nq, nr = self.q + 1, self.r
                    if self.board.is_valid(nq, nr):
                        self.q, self.r = nq, nr
        finally:
            self._restore_terminal(old)

    def _line_y(self, r):
        return (r + HEX_RADIUS) * 2

    def _ix(self, q, r):
        x = hex_to_pos(q, r)
        return int(round(x)) + self._offset_x

    def _board_lines_with_selection(self):
        lines = render_board(self.board)

        ly = self._line_y(self.r)
        ix = self._ix(self.q, self.r)
        if ly < len(lines) and 0 <= ix < len(lines[ly]):
            line = lines[ly]
            left = ix - 1 if ix - 1 >= 0 else ix
            right = ix + 1 if ix + 1 < len(line) else ix
            chars = list(line)
            chars[left] = "["
            chars[ix] = line[ix]
            chars[right] = "]"
            lines[ly] = "".join(chars)

        return lines

    def _draw(self):
        lines = self._board_lines_with_selection()

        dist = hex_distance((self._start_q, self._start_r), (self.q, self.r))
        out_of_range = dist > self.max_range

        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(f"Select target for {self.action_name} (max range {self.max_range})\r\n")
        for line in lines:
            sys.stdout.write(line + "\r\n")
        for p in self.players:
            sys.stdout.write(render_ship_status(p) + "\r\n")
        status = f"Selected: {self.q},{self.r}  (distance: {dist})"
        if out_of_range:
            status += "  OUT OF RANGE!"
        sys.stdout.write(status + "\r\n")
        sys.stdout.flush()

    def _set_raw_mode(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setraw(fd)
        return old

    def _restore_terminal(self, old):
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\r\n")
        sys.stdout.flush()

    def _read_key(self):
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            r, _, _ = select.select([sys.stdin], [], [], 0.15)
            if r:
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
                return 'ESC'
            return 'ESC'
        elif ch in ('\r', '\n'):
            return 'ENTER'
        return None
