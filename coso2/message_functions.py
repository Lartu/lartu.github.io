# Message functions for Coso

import sys

def show(message):
    '''Shows a message.
    '''
    print("\033[93m->\033[0m", message)


def warning(message):
    '''Shows a warning message.
    '''
    print("\033[43m WARNING \033[0m ", message)


def error(message):
    '''Shows an error message and stops execution.
    '''
    print("\033[41m ERROR \033[0m ", message)
    sys.exit(1)