class Error(Exception):
    """Base class for exceptions."""
    pass

class CommandNotFoundError(Error):
    """
    Exception raised for when a command cannot be found from the input given.
    """

    def __init__(self, expression='CommandNotFoundError', message='The command entered is can not be found.'):
        self.expression = 'CommantNotFoundError'
        self.message = 'The command entered cannot be found.'

class InvalidArgumentsError(Error):
    """
    Exception raised for errors in the input of command arguments
    """

    def __init__(self, expression='InvalidArgumentsError', message='The command entered contains invalid arguments.'):
        self.expression = expression
        self.message = message

class InvalidCommandError(Error):
    """
    Exception raised for errors when parsing the command and arguemtns.
    """

    def __init__(self, expression='InvalidCommandError', message='The command entered is invalid.'):
        self.expression = expression
        self.message = message