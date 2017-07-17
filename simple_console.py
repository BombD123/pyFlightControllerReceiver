# Logic to this class derived from:
# https://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
# Basically, it allows the invoker to request the next character typed from the user, and
# to immediately return without waiting for a newline to be encountered.

class SimpleConsole:
    def __init__(self):
        import tty, sys

    @staticmethod
    def get_next_character():
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
