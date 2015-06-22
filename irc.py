# Program: IRC Interface Class
# Developer: William Leuschner
# Creation Date: 2015-06-21
# Purpose: To provide an IRC interface class using Python

"""An IRC interface class"""
# Import requried libraries
import socket
import threading
import ssl
import time


class IRCInputBuffer():
    """
    Buffered Input for an IRC connection
    """
    def __init__(self, socket):
        # Incomplete lines
        self.buffer = ""
        # The socket to interface with
        self.socket = socket
        # Data from the IRC server, split at \r\n
        self.lines = []

    def __recieve(self):
        """Pull more data from the IRC socket"""
        try:
            # Try to pull more data from the socket and decode it as UTF-8
            latest = self.socket.recv(4096).decode('UTF-8')
            # Stick it on to any previous data
            data = "%s%s" % (self.buffer, latest)
        except socket.error as e:
            # The socket broke. Fail, and let something above me handle it
            raise socket.error(e)
        except UnicodeDecodeError:
            # The unicode decoder failed. Assume that there was no data.
            data = ''
        # Split the data at \r\n and add it to lines
        self.lines += data.split('\r\n')
        # Pull off the last, presumably incomplete line to keep in buffer
        self.buffer = self.lines[-1]
        self.lines = self.lines[:-1]

    def next_line(self):
        """API-exposed function to get the next line"""
        # Stop execution until a line is recieved
        while len(self.lines == 0):
            # Try to get another line
            try:
                self.__recieve()
            except socket.error as e:
                # Rethrow the exception up the chain
                raise socket.error(e)
            # Pull the first line off the stack of lines
            first_line = self.lines[0]
            self.lines = self.lines[1:]
            # Return the first line
            return first_line


class IRCOutputBuffer():
    """
    Buffered Output for an IRC connection
    """
    def __init__(self, socket, max_messages, time_limit):
        self.is_in_error = False
        # Are there lines in the queue?
        self.hasqueue = False
        self.socket = socket
        self.queue = []
        # Used to avoid triggering channel floods
        self.consecutive_messages = 0
        # IRC channel floods are created as 'messages per unit of time'.
        # max_messages is messages,
        self.max_messages = max_messages
        # time_limit is unit of time.
        self.time_limit = time_limit

    def __send(self):
        """Private function to send a message."""
        if self.consecutive_messages >= (self.max_messages - 1):
            # If we've sent one less than the max number of messages per
            # time unit, wait until the time interval expires before allowing
            # message sending to resume.
            time.sleep(self.time_limit - self.max_messages)
            self.consecutive_messages = 0
        if len(self.queue) == 0:
            # If there are no messages in the queue, record that and set
            # consecutive_messages to 0.
            self.hasqueue = False
        else:
            # If there are messages in the queue,
            # Send one now
            self.send_now(self.queue[0])
            # Remove it from the queue
            self.queue = self.queue[1:]
            # And queue the next message to be sent.
            self.__start_send_timer()

    def __start_send_timer(self):
        """Private function to start a recursive timer for __send"""
        # Create a 1-second timer that recursively calls __send
        self.send_timer = threading.Timer(1, self.__send)
        # Start the timer
        self.send_timer.start()

    def send(self, string):
        """
        Sends `string` to the IRC server, buffered to avoid channel floods.
        Example:
        >>> O = IRCOutputBuffer() # doctest +SKIP
        >>> O.send("Hello, IRC!") # doctest +SKIP
        """
        if self.hasqueue:
            # If there is a queue, append string to it.
            self.queue.append(string)
        else:
            # Otherwise, set hasqueue to true,
            self.hasqueue = True
            # Send this message now,
            self.send_now(string)
            # Start the timer,
            self.__start_send_timer()
            # And increment the consecutive message counter.
            self.consecutive_messages += 1

    def send_now(self, string):
        """
        Sends `string` to the IRC server immediately.
        Example:
        >>> O = IRCOutputBuffer() # doctest +SKIP
        >>> O.send_now("Hello, IRC!") # doctest +SKIP
        """
        if not self.is_in_error:
            try:
                self.socket.send(("%s\r\n" % string).encode('UTF-8'))
            except socket.error as e:
                raise socket.error(e)
                print("Output error:", e)
                print("Occurred during sending of string \"", string, "\".")

    def is_in_error(self):
        """
        Returns `self.is_in_error`
        Example:
        >>> O = IRCOutputBuffer() # doctest +SKIP
        >>> O.is_in_error() # doctest +SKIP
        True
        """
        return self.is_in_error


class IRC(threading.Thread):
    """
    Main IRC interface
    """
    def __init__(
        self,
        hostname,
        port,
        nick,
        realname,
        password=None,
        ssl=False
    ):
        pass
