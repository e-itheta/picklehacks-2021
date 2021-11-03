"""
Usage: client
"""

import curses
import docopt

def start():

    args = docopt.docopt(__doc__)


    # Unlike most decorators which returns a wrapped function, curses.wrapper
    # will call main. So even though we're not 'using' main, we're using main.
    @curses.wrapper
    def main(stdscr: curses.window):
        pass


if __name__ == "__main__":
    start()
