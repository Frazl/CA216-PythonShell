#/usr/bin/env python3
import os, subprocess, shlex, threading
from sys import argv, stdout, stdin
from datetime import datetime
import readline 
#readline is imported to support ctrl+l (clear screen) keyboard shortcut functionality as well as
#up and down arrow key support for repeating commands. Inbuilts of this module are never actually used explicitly. 

class Shell(object):

    def __init__(self, custom_input=""):
        self.environ = {
            'SHELL': os.getcwd()+'/'+argv[0],
            'PWD': os.getcwd(),
            'HOME': os.environ.get('HOME', os.getcwd())
        }
        self.commands = {
            'exit': exit,
            'cd': self.cd,
            'pwd': self.pwd, 
            'clr': self.clr, 
            'dir': self.dir, 
            'pause': self.pause, 
            'help': self.help, 
            'echo': self.echo, 
            'environ': self.display_environ,
        }
        if custom_input:
            self.run_with_custom_input(custom_input)
        else:
            self.run()
    
    def run(self):
        '''
        Continually takes in input and processes and runs commands.
        '''
        while True:
            try:
                s = input('['+self.get_prefix() + '] $ ')
            except EOFError: # If user presses ctrl + d (EOF) exit the shell
                exit()

            if s == 'xd':
                self.background_run_internal('echo', ['1234','>>','testinternalbackground'])
                print('hit')
                continue

            # Using shell lexer module below allows for things such as 'echo "something      somethingelse" more'
            # If normal split would be used then something such as 'something somethingelse more ' would be returned 
            # instead of the full string supplied along with the whitespace. 

            raw = shlex.split(s)
            if raw:
                command = raw[0]
                tokens = raw[1:]
                if command in self.commands:
                    out_file, contains_io, cut = Shell.get_output(tokens)
                    if contains_io:
                        tokens = tokens[0:cut-1] + tokens[cut+1:]
                    #If the command is inbuilt run it on a separate thread. 
                    threading.Thread(target = self.commands[command], args=(out_file, *tokens,)).run()
                else:
                    #Try find a binary for the command or see if it's a binary in the current directory itself. 
                    fpath = self.program_find(raw)
                    if self.is_exe(command):
                            fpath = command
                    if not fpath:
                            print(f'myshell: The command "%s" cannot be found.' % s)
                    else:
                        self.program_run(fpath, raw)

    def run_with_custom_input(self, custom_input):
        '''
        Takes input for the shell from a file and parses and runs the commands. 
        Commands should be separated by newline characters.
        '''
        pass
    
    def cd(self, dir=None, out=stdout):
        '''
        Changes the current working directory.
        If no directory is supplied then the working directory will change to HOME env variable if set. 
        '''
        try:
            if not dir:
                dir = self.environ.get('HOME')
            os.chdir(dir)
            self.environ['PWD'] = os.getcwd()
        except (FileNotFoundError, NotADirectoryError):
            print(f'myshell: No such directory "%s" exists...' % dir)
        print("", file=stdout)
        
    def pwd(self, out=stdout):
        ''' 
        Print'zs the current working directory
        '''
        print(self.environ['PWD']+'\n', file=stdout)
    
    def display_environ(self, out=stdout):
        '''
        Prints out the environment variables that have been set in the shell.
        '''
        s = ""
        for k,v in self.environ.items():
            s += k + "\t" + v + "\n"
        print(s, file=out)

    def clr(self, out=stdout):
        '''
        Clear's the screen.
        '''
        clear = "\x1b\x5b\x48\x1b\x5b\x32\x4a" # Special unicode for clearing screen on linux distros
        print(clear, file=out)
    
    def help(self, out=stdout):
        '''
        Display's myshell's readme.
        '''
        os.system('more ' + "/".join(self.environ['SHELL'].split('/')[:-1])+'/readme')
        print("", file=out)

    def dir(self, out=stdout):
        '''
        Prints out files and directories within the current working directory.
        '''
        curr = os.listdir()
        s = ""
        for f in curr:
            s += f + "\n"
        print(s, file=out)
        
    
    def pause(self):
        '''
        Pause's the shell until enter is struck.
        '''
        input()
        print("", file=out)
    
    def echo(self, out=stdout, *args):
        '''
        Print's out the arguments after echo separated by spaces.
        '''
        if out == stdout:
            print('\n')
        print(" ".join(args), file=out)
        if out:
            out.close()
    
    def get_prefix(self):
        '''
        Get's the prefix for the shell input line. 

        If the home directory is set then it is displayed as a '~'
        '''
        HOME = self.environ.get('HOME', None)
        if self.environ['PWD'] == HOME:
            return '~'
        if HOME and self.environ['PWD'].startswith(HOME):
            return self.environ['PWD'].replace(HOME, "~")
        return self.environ['PWD']
    
    def program_find(self, tokens):
        '''
        Searches for the program first in the current working directory followed by the OS 'PATH' environ. 
        '''
        #First we must check if there is a program with the name in the current working directory...
        fname = tokens[0]
        if Shell.in_wd(fname):
            if Shell.is_exe(fname):
                return fname
        #If no program is in the CWD we must check outside in the PATH environment directories...
        elif Shell.in_path_environ(fname):
            fpath = Shell.in_path_environ(fname)
            if Shell.is_exe(fpath):
                return fpath
        return ""
    
    def command_run(self, command, tokens):
        threading.Thread(target=command, args=tuple(tokens)).run()
    
    def background_run_internal(self, command, tokens):
        f = open('.buffer'+str(datetime.now()), 'w+')
        f.write (command + ' ' + ' '.join(tokens) + '\n')
        f.close()
        subprocess.Popen(executable='python3', args='test.py', stdout=stdout)

    def program_run(self, fpath, tokens):
        '''
        Run's a program with associated arguments. 
        
        Supports io redirection and background running
        '''
        process = {
            'stdin': stdin,
            'stdout': stdout,
            'args': [fpath],
        }
        fname = tokens[0]
        args = tokens[1:]
        process = Shell.parse_tokens(process, args)
        if args and args[-1] == '&':
            pin = subprocess.DEVNULL if process['stdin'] == stdin else process['stdin']
            pout = subprocess.DEVNULL if process['stdout'] == stdout else process['stdout']
            subprocess.run(process['args'], stdin=pin, stdout=pout)
        else:
            subprocess.run(process['args'], stdin=process['stdin'], stdout=process['stdout'])

    @staticmethod
    def parse_tokens(process, args):
        '''
        Parses IO redirection and additional arguments to be supplied to a subprocess.
        '''
        if len(args) > 1:
            i = 0
            while i < len(args):
                if args[i] == '>':
                    process['stdout'] = open(args[i+1], 'a') #Append
                    i += 2
                elif args[i] == '>>':
                    process['stdout'] = open(args[i+1], 'w') #Write
                    i += 2
                elif args[i] == '<':
                    process['stdin'] = open(args[i+1], 'r') #Read
                    i += 2
                elif args[i] == '<<':
                    process['stdin'] = open(args[i+1], 'r') #Read
                    i += 2
                else:
                    process['args'].append(args[i])
                    i += 1
        return process
    
    @staticmethod
    def get_output(args):
        '''
        Checks for > and >> IO Redirection used for internal/inbuilt commands.
        '''
        out = None
        i = 0 
        if len(args) > 1:
            j = i 
            while i < len(args):
                if args[i] == '>':
                    out = open(args[i+1], 'a') #Append
                    i += 2
                    break
                elif args[i] == '>>':
                    out = open(args[i+1], 'w') #Write
                    i += 2
                    break
                else:
                    i += 1
        return out, i == len(args), i


    @staticmethod
    def is_exe(fpath):
        '''
        Checks if a file is executable.
        '''
        return os.access(fpath, os.X_OK) and os.path.isfile(fpath)
    
    @staticmethod
    def in_path_environ(fname):
        '''
        Check's if a file is in any of the PATH directories.
        '''
        paths = os.environ.get('PATH', "").split(":") #Each path is divided by a ':' hence the split. 
        for path in paths:
            for f in os.listdir(path):
                if f == fname:
                    return path+'/'+fname
        return ""
    
    @staticmethod
    def in_wd(fname):
        '''
        Check's if a file is in the current working directory.
        '''
        for f in os.listdir():
            if f == fname:
                return fname
        return ""



if __name__ == '__main__':
    if len(argv) > 1:
        try:
            with open(argv[1]) as f:
                custom_input = f.read()
        except FileNotFoundError:
            print(f'The file %s can not be found.' % argv[1])

        sh = Shell(custom_input)
    else:
        sh = Shell()