from sys import stdin, stdout, stderr, exit
import threading
import os
import subprocess

class Task(object):

    '''
    The Task class abstracts away the IO redirection, background execution and running of commands from the main shell. 
    '''

    def __init__(self, task, _input=stdin, output=stdout, args=None, background_execution=False, is_internal=True):

        self.task = task # The function to be ran or path to file .
        self.input = _input # open file for input.
        self.output = output # open file for output.
        self.args = args # list of arguments to pass to function.
        self.background_execution = background_execution # Boolean to execute in background or not. 
        self.is_internal = is_internal # Boolean to specify a command internal to the shell.

    def run(self):
        '''
        Begins execution of the task
        '''
        if self.background_execution:
            threading.Thread(target=self.execute_in_background).run()
        else:
            threading.Thread(target=self.execute).run()
        
    
    def execute(self):
        '''
        Executes tasks that do not involve background execution.
        '''
        if self.is_internal:
            # Internal commands we run on another thread to avoid blocking the main thread.
            t = threading.Thread(target=self.task, args=(self.args, ), kwargs={'out' : self.output})
            t.run()
            # We wait for the thread to finish but more commands are still able to be entered.
            while t.is_alive():
                continue
            self.close_io()
        else:
            #background processes just run with the subprocess module.
            subprocess.run([self.task] + self.args, stdin=self.input, stdout=self.output)
            self.close_io()


    def close_io(self):
        '''
        Closes input and ouput for the task unless it's stdin or stdout 
        '''
        if self.input != stdin:
            self.input.close()
        if self.output != stdout:
            self.output.close()
        return True
    
    def execute_in_background(self):
        '''
        Executes tasks that do involve background execution.
        '''

        #Fork a process for the child to run 

        process = os.fork()
        if process != 0: #If parent just return to main thread (back to shell get input)
            return 
        
        #Printing the PID of the background proccess is really useful in case user needs to kill it 

        print('\r\r[' + str(os.getpid()) + ']         ') 
        
        if self.is_internal:
            
            #If it's internal just run the command by calling the function.

            self.task(self.args, out=self.output)
            print('\r[' + str(os.getpid()) + '] done') #Let the user know proccess finished
            exit(0)
        else:
            
            secondary = os.fork() 

            # we fork a second process to monitor it's child which will run the program in the background.
            # this is essential as we have no way of knowing when the child process is done otherwise.
            
            if secondary != 0:
                self.wait_for_finish() #Wait for the child process to finish and notify user.
            else:

                #flush the standard input, output and error 

                stderr.flush()
                stdout.flush()
                stdin.flush()

                # we check for IO redirection streams other to stdin, stdout and if so duplicate the file handler below. 

                if self.input != stdin:
                    os.dup2(self.input.fileno(), stdin.fileno()) #stdin
                if self.output != stdout:
                    os.dup2(self.output.fileno(), stdout.fileno()) #stdout
                
                os.execv(self.task, [self.task] + self.args) #execute task
              
    def wait_for_finish(self):
        '''
        Waits for child process to finish and notifies the users.
        '''
        _, status = os.wait()
        print('\r[' + str(os.getpid()) + '] (' + self.task + ' ' + " ".join(self.args) + ') finished with exit code: ' + str(status)) 
        exit(0)