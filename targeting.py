import fcntl
import os
import sys
import termios
import time
import tty

from display import get_tile_emoji, render_board, render_ship_status, hex_to_pos, SCALE
from utils import HEX_RADIUS, hex_distance


class TargetSelector:
    def __init__(self, board, start_q, start_r, max_range, action_name, players, round_num=0):
        self.board = board
        self.q = start_q
        self.r = start_r
        self.max_range = max_range
        self.action_name = action_name
        self.players = players
        self._start_q = start_q
        self._start_r = start_r
        self._offset_x = HEX_RADIUS * SCALE
        self._round_num = round_num

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
        lines = render_board(self.board, self.players, color=False)

        ly = self._line_y(self.r)
        ix = self._ix(self.q, self.r)
        if ly < len(lines) and 0 <= ix < len(lines[ly]):
            line = lines[ly]
            tile = self.board.get_tile(self.q, self.r)
            emoji = get_tile_emoji(tile, color=False) if tile else "\u00b7"
            emoji_len = len(emoji)

            left = ix - 1 if ix - 1 >= 0 else ix
            right = ix + emoji_len

            if right < len(line):
                chars = list(line)
                for i in range(left, right + 1):
                    chars[i] = " "
                chars[left] = "["
                for i, ch in enumerate(emoji):
                    chars[ix + i] = ch
                chars[right] = "]"
                lines[ly] = "".join(chars)

        return lines

    def _draw(self):
        lines = self._board_lines_with_selection()

        dist = hex_distance((self._start_q, self._start_r), (self.q, self.r))
        out_of_range = dist > self.max_range

        sys.stdout.write("\033[H\033[J")
        sys.stdout.write("=" * 60 + "\r\n")
        sys.stdout.write("FRIGATE \u2014 Hex Space Combat\r\n")
        sys.stdout.write("=" * 60 + "\r\n")
        sys.stdout.write(f"Select target for {self.action_name} (max range {self.max_range})\r\n")
        sys.stdout.write("\r\n")
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
        fd = sys.stdin.fileno()
        ch = os.read(fd, 1)
        if ch == b'\x1b':
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            try:
                time.sleep(0.05)
                seq = b'\x1b'
                while True:
                    try:
                        b = os.read(fd, 1)
                        if not b:
                            break
                        seq += b
                    except BlockingIOError:
                        break
            finally:
                fcntl.fcntl(fd, fcntl.F_SETFL, flags)
            if seq in (b'\x1b[A', b'\x1bOA'):
                return 'UP'
            if seq in (b'\x1b[B', b'\x1bOB'):
                return 'DOWN'
            if seq in (b'\x1b[C', b'\x1bOC'):
                return 'RIGHT'
            if seq in (b'\x1b[D', b'\x1bOD'):
                return 'LEFT'
            return 'ESC'
        if ch in (b'\r', b'\n'):
            return 'ENTER'
        return None
