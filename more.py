import os
import tty
import sys
import termios

class More(object):

    def __init__(self, file):
        try:
            self.file = open(file, 'r')
        except FileNotFoundError:
            print('More: File not found.')
        
        orig_settings = termios.tcgetattr(sys.stdin) #make a copy of current terminal settings
        tty.setcbreak(sys.stdin) #enable cbreak mode
        lines = self.file.readlines() #Read file lines 
        terminal_lines = os.get_terminal_size()[1] #Get terminal size in terms of lines 
        self.read(lines, terminal_lines) 
        print()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings) #Restore original settings to terminal


    def read(self, lines, terminal_size):
        i = 0 
        #Fill the screen terminal size and then wait for input 
        while i < terminal_size and i < len(lines):
            print(lines[i], end='')
            i += 1
        key = 0 
        #Fill in the rest only when the user enters space
        while i < len(lines):
            if key == chr(32):
                print(lines[i], end='')
                i += 1
                key = 0
            else:
                while key != chr(32):
                    key = sys.stdin.read(1)[0]