import os, sys, shlex
from task import Task
from more import More
from errors import CommandNotFoundError, InvalidArgumentsError, InvalidCommandError
import readline 

'''

Sean Fradl
Dublin City University
Student No 17460674 
As part of CA216

This shell runs in Python 3.

Note about readline import:

readline is imported to support ctrl+l (clear screen) keyboard shortcut functionality as well as up and down arrow key support for repeating commands. 
Inbuilts of this module are never actually used explicitly. 

'''

class Shell(object):

    def __init__(self, batch=False):
        '''
        Setups the shell environ, runs the main shell loop and stores a dictionary of strings to commands.
        '''

        self.environ = {
            'SHELL': os.getcwd()+'/'+sys.argv[0],
            'PWD': os.getcwd(),
            'HOME': os.environ.get('HOME', '  ####  '),
            'PATH': os.environ.get('PATH', ""),
            'HELP': os.getcwd()+'/readme'
        }

        self.commands = {
            'quit': self.quit,
            'cd': self.cd,
            'pwd': self.pwd, 
            'clr': self.clr, 
            'dir':  self.dir, 
            'pause': self.pause, 
            'help': self.help, 
            'echo': self.echo, 
            'environ': self.display_environ,
        }
        
        if batch:
            self.batch_loop()
        else:
            self.main_loop()


    '''
    Loop and Input Parsing Section
    '''

    def main_loop(self):
        '''
        The loop for the shell when running from user input.
        '''
        while True:
            try:
                unparsed_input = self.get_input() #Get input from user
                if unparsed_input != '': 
                    command, args = self.parse_input(unparsed_input) #Parse input into the command and command arguments
                    task = self.make_task(command, args) #Make a task object
                    task.run() #Run the task
            except (CommandNotFoundError, InvalidArgumentsError, InvalidCommandError) as e:
                print('myshell error: ' + e.message)
            #except:
             #   print('myshell error: ' + unparsed_input + ' is not a valid command or a unknown error occured.')
    
    def batch_loop(self):
        '''
        The loop for the shell when running a script from a file.
        '''
        with open(sys.argv[1], 'r') as f:
            for unparsed_input in f:
                try:
                    if unparsed_input != '':
                        command, args = self.parse_input(unparsed_input)
                        task = self.make_task(command, args)
                        task.run()
                except (CommandNotFoundError, InvalidArgumentsError) as e:
                    print('myshell error: ' + e.message)
                    exit(0)
                except:
                    #print('myshell error: `' + unparsed_input + '` is not a valid command or a unknown error occured.')
                    exit(0)


    def get_input(self):
        '''
        Obtains the input from the user and returns it.
        '''
        try:
            user_input = input('['+self.input_prefix() + '] $ ')
        except (KeyboardInterrupt, EOFError, SystemExit): # If user presses ctrl + d (EOF) or when running batch commands and reach EOF exit the shell.
            exit(1)
        return user_input
    
    def input_prefix(self):
        '''
        Makes an nice prefix for when collecting input. 
        '''
        HOME = self.environ.get('HOME', None)
        if self.environ['PWD'] == HOME:
            return '~'
        if HOME and self.environ['PWD'].startswith(HOME):
            return self.environ['PWD'].replace(HOME, "~")
        return self.environ['PWD']
    
    @staticmethod
    def parse_input(unparsed_input):
        '''
        Parses the input using shlex. This allows for commands such as 'echo "     hello    world"' to be parsed correctly.
        '''
        tokenised_input = shlex.split(unparsed_input.strip())
        try:
            command = tokenised_input[0]
            args = tokenised_input[1:]
        except IndexError:
            raise InvalidCommandError
            
        return command, args
            
    
    def make_task(self, command, args):
        '''
        Returns a Task object that can carry out the command with args (see task.py).
        '''
        is_internal_command = self.is_internal_command(command) #Check if internal command 
        _input, output, args, background_execution = self.parse_args(args) #Check for IO and background execution

        if is_internal_command:
            return Task(self.commands[command], _input, output, args, background_execution, is_internal_command) #Internal task
        else:
            # Search for executable 
            fpath_environ = self.command_in_path_environ(command)
            if self.is_exe(command):
                return Task(command, _input, output, args, background_execution, is_internal_command) #Direct path given task
            elif fpath_environ:
                return Task(fpath_environ, _input, output, args, background_execution, is_internal_command) #Path found in path environ task
            else:
                raise CommandNotFoundError # Raise an error as nothing was found
    
    def is_internal_command(self, command):
        '''
        Checks if a given string is in the command dictionary for the shell.
        '''
        return command in self.commands.keys()
    
    @staticmethod
    def parse_args(args):
        '''
        seperates arguements ino input, output, whether or not there's background execution and any remaining arguments. 
        '''
        
        # Set defaults 
        
        _input = sys.stdin
        output = sys.stdout
        background_execution = False 

        # Check for background execution
        
        if len(args) > 0:
            if args[-1] == '&':
                background_execution = True
                args.pop()
    

        #Check for IO redirection and other arguments 

        if len(args) > 0:
            parsed_args = []
            i = 0
            try:
                while i < len(args):
                    if args[i] == '>':
                        output = open(args[i+1], 'a') #Append
                        i += 2
                    elif args[i] == '>>':
                        output = open(args[i+1], 'w') #Write
                        i += 2
                    elif args[i] == '<':
                        _input = open(args[i+1], 'r') #Read
                        i += 2
                    elif args[i] == '<<':
                        _input = open(args[i+1], 'r') #Read
                        i += 2
                    else:
                        parsed_args.append(args[i])
                        i += 1
                args = parsed_args
            except IndexError:
                raise InvalidArgumentsError #Index error usually means there was a IO redirection symbol but nothing followed
                
        return _input, output, args, background_execution

    '''
    Inbuilt Shell Commands Section
    '''

    def cd(self, args=[], out=None):
        '''
        Changes the current working directory.
        If no directory is supplied then prints the current working directory.
        '''
        if not args:
            self.pwd(args, out)
        else:
            try:
                directory = args[0]
                os.chdir(directory)
                self.environ['PWD'] = os.getcwd()
            except (NotADirectoryError, FileNotFoundError) as e:
                print('myshell error: ' + e.strerror)

        
    
    def pwd(self, args, out):
        ''' 
        Print's the current working directory
        '''
        print(os.getcwd(), file=out)
    
    def clr(self, args, out):
        '''
        Clear's the screen.
        '''
        clear = "\x1b\x5b\x48\x1b\x5b\x32\x4a" # Special unicode for clearing screen on linux distros
        print(clear, file=out)
    
    def dir(self, args, out):
        '''
        Prints out files and directories within the current working directory.
        '''
        curr = os.listdir()
        s = ""
        for f in curr:
            s += f + "\n"
        print(s, file=out)
    
    def pause(self, args, out):
        '''
        Pause's the shell until enter is struck.
        '''
        input()
    
    def help(self, args, out):
        help_fpath = self.environ['HELP']
        try:
            if out == sys.stdout:
                More(help_fpath)
            else:
                contents = open(help_fpath, 'r').readlines()
                for line in contents:
                    print(line, file=out, end='')
        except (FileNotFoundError):
            print("Can't find shell help file at " + help_fpath)
    
    def echo(self, args, out):
        '''
        Print's out the arguments after echo separated by spaces.
        '''
        print(" ".join(args), file=out)
    
    def quit(self, args, out):
        '''
        Exits the shell
        '''
        exit()

    def display_environ(self, args, out):
        '''
        Prints out the environment variables that have been set in the shell.
        '''
        s = ""
        for k,v in self.environ.items():
            s += k + "\t" + v + "\n"
        print(s, file=out)


    @staticmethod
    def is_exe(fpath):
        '''
        Checks if a file is executable.
        '''
        return os.access(fpath, os.X_OK) and os.path.isfile(fpath)


    def command_in_path_environ(self, fname):
        '''
        Check's if a file is in any of the PATH directories.
        '''
        paths = self.environ['PATH'].split(":") #Each path is divided by a ':' hence the split. 
        for path in paths:
            for f in os.listdir(path):
                if f == fname:
                    return path+'/'+fname
        return ""




if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        Shell(True)
    else:
        Shell()
        