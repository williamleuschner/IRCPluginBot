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
            data = self.buffer + latest
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
        while len(self.lines) == 0:
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
    def __init__(self, socket):
        self.is_in_error = False
        # Are there lines in the queue?
        self.hasqueue = False
        self.socket = socket
        self.queue = []
        # Used to avoid triggering channel floods
        self.consecutive_messages = 0
        # IRC channel floods are created as 'messages per unit of time'.
        # max_messages is messages,
        self.max_messages = 100
        # time_limit is unit of time.
        self.time_limit = 1

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

    def get_error_state(self):
        """
        Returns `self.is_in_error`
        Example:
        >>> O = IRCOutputBuffer() # doctest +SKIP
        >>> O.get_error_state() # doctest +SKIP
        True
        """
        return self.is_in_error

    def set_chan_flood_settings(self, max_messages, time_limit):
        """
        Sets the channel flood settings for the class.
        Example:
        >>> O = IRCOutputBuffer() # doctest +SKIP
        >>> O.set_chan_flood_settings(6, 10) # doctest +SKIP
        """
        self.max_messages = max_messages
        self.time_limit = time_limit


class Message():
    def __init__(
        self,
        msg_type,
        message,
        headers,
        nick=None,
        userhost=None,
        server_hostname=None
    ):
        self.type = msg_type
        self.message = message
        self.headers = headers
        if nick is None and userhost is None and server_hostname is None:
            raise AttributeError(
                "You must specify either nick and userhost or server_hostname."
            )
        elif nick is None and userhost is None and server_hostname is not None:
            self.server_hostname = server_hostname
            self.is_server_msg = True
        elif (
            nick is not None and
            userhost is not None and
            server_hostname is None
        ):
            self.nick = nick
            self.userhost = userhost
            self.is_server_msg = False
        else:
            raise AttributeError(
                (
                    "You must specify only either nick and userhost "
                    "or server_hostname."
                )
            )

    def __repr__(self):
        if self.is_server_msg is not True:
            repr_dict = {
                'type': self.type,
                'message': self.message,
                'headers': self.headers,
                'nick': self.nick,
                'userhost': self.userhost
            }
        else:
            repr_dict = {
                'type': self.type,
                'message': self.message,
                'headers': self.headers,
                'server_hostname': self.server_hostname
            }
        return repr(repr_dict)

    def __str__(self):
        str_str = ":%s :%s" % (" ".join(self.headers), self.message)
        return str_str


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
        threading.Thread.__init__(self)
        self.running = True
        self.hostname = hostname
        self.port = port
        self.nick = nick
        self.realname = realname
        self.password = password
        self.ssl = ssl
        self.debugging = False
        self.callback = None
        self.input_buffer = None
        self.output_buffer = None
        self.socket = None
        # Send messages that aren't likely to trigger flood protection
        # immediately, rather than queueing them.
        self.reduce_flood_protection = True

    ##########################################
    #           Private Functions            #
    ##########################################

    def __identify(self):
        """
        Authenticate the bot with NickServ.
        Example:
        >>> self.__identify() # doctest +SKIP
        NOTICE: You are now identified for PluginBot
        """
        pass

    def __connect(self):
        """
        Connect to the server, optionally using SSL.
        """
        # Debug print the hostname.
        self.__print("Connecting to %s" % self.hostname)
        # Create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("self.ssl =", self.ssl)
        if self.ssl is True:
            # If using SSL, secure the socket.
            self.socket = ssl.wrap_socket(self.socket)
        # Connect to the server
        self.socket.connect((self.hostname, self.port))
        # Give instances of the input and output buffers access to the socket.
        self.input_buffer = IRCInputBuffer(self.socket)
        self.output_buffer = IRCOutputBuffer(self.socket)
        if self.password is not None:
            # If a server password is set, send it.
            self.output_buffer.send("PASS %s" % self.password)
        # Send the nickname
        self.output_buffer.send("NICK %s" % self.nick)
        # Send the username and realname
        self.output_buffer.send(
            "USER %s 0 * :%s" % (self.nick, self.realname)
        )

    def __disconnect(self, quit_message="Goodbye!"):
        """
        Disconnect from the server.
        """
        self.__print("Disconnecting from", self.hostname)
        self.output_buffer.send("QUIT :%s" % quit_message)
        self.socket.close()

    def __print(self, message):
        """
        Print for debugging.
        """
        if self.debugging:
            print(message)

    def __message_factory(self, line):
        """
        Create a Message object for a given string `line`, assuming `line`
        contains a raw line from an IRC server.
        Example:
        >>> self.__message_factory("PRIVMSG #bottesting :The sky is falling!")
        PRIVMSG #bottesting :The sky is falling!
        """
        # :user!username@HostHash.net PRIVMSG #channel :Message
        # :irc.example.com 332 nick #channel :Topic
        line_list = line.split(":")
        line_list = line_list[1:]
        # This is now
        #  0                                1
        # ["sender MSGTYPE other_headers ", "Message"]
        # If there are 3 or more elements in the list after nixing the empty
        # one, make anything after the headers into one string
        if len(line_list) >= 3:
            # Cut off the headers
            message_split = line_list[1:]
            # Stick what's left back together with colons
            message = ":".join(message_split)
        elif len(line_list) == 2:
            message = line_list[1]
        elif len(line_list) < 2:
            message = ""
        # Split the headers string into a list
        headers = line_list[0].split(" ")
        # The nick!userhost of the sender is the first header
        nick_userhost = headers[0]
        if len(headers) < 2:
            self.__debugPrint("Only one header in message: \"%s\"" % (line,))
        else:
            if "!" in nick_userhost:
                nick, userhost = nick_userhost.split("!")
                message_type = headers[1]
                if message_type == 'PRIVMSG':
                    if (
                        message.startswith('\001ACTION ') and
                        message.endswith('\001')
                    ):
                        message_type = 'ACTION'
                        message = message[8:-1]
                # Make Message object
                msg_obj = Message(
                    message_type,
                    message,
                    headers,
                    nick=nick,
                    userhost=userhost
                )
            else:
                message_type = headers[1]
                # self.__print("[%s] %s" % (message_type, message))
                # Make Message object
                msg_obj = Message(
                    message_type,
                    message,
                    headers,
                    server_hostname=nick_userhost
                )
            return msg_obj

    ##########################################
    #            Public Functions            #
    ##########################################

    def send_raw(self, message):
        """
        Send a raw message to the server.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.send_raw("MODE +o ChanServ") # doctest +SKIP
        """
        self.__print("Sending \"%s\" to the server, raw." % message)
        self.output_buffer.send(message)

    def say(self, message, destination):
        """
        Speak a given message.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.say("Hello, world!", "#bottesting") # doctest +SKIP
        PluginBot in #bottesting: Hello, world!
        """
        message_string = "PRIVMSG %s :%s" % (destination, message)
        self.output_buffer.send(message_string)

    def do(self, action, destination):
        """
        Send an ACTION message.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.do("waves", "OtherBot") # doctest +SKIP
        * PluginBot waves
        """
        message_string = "PRIVMSG %s :\001ACTION %s \001" % (
            destination,
            action
        )
        self.output_buffer.send(message_string)

    def notice(self, message, destination):
        """
        Send a NOTICE.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.notice(
        ...     "You will be kicked if you do that again.",
        ...     "badguy"
        ... )
        NOTICE: You will be kicked if you do that again.
        """
        message_string = "NOTICE %s :%s" % (destination, message)
        if self.reduce_flood_protection:
            self.output_buffer.send_now(message_string)
        else:
            self.output_buffer.send(message_string)

    def start(self):
        """
        Start the bot.
        """
        self.__print("The bot is now running.")
        self.__connect()
        # While stop() has not been called,
        while self.running:
            # Set line to an empty string, then fill it.
            line = ""
            while len(line) == 0:
                # Whenever the line is empty, try to pull the next line from
                # the input buffer.
                try:
                    line = self.input_buffer.next_line()
                except socket.error as e:
                    # Should it fail, debug print an error and reconnect.
                    self.__print(
                        "Socket error (%s). Reconnecting..." % repr(e)
                    )
                    self.reconnect()
                # If it's a PING, respond immediately.
                if line.startswith("PING"):
                    self.output_buffer.send_now("PONG %s" % line.split()[1])
                else:
                    # Otherwise, send it to the function that builds Message
                    # objects.
                    message = self.__message_factory(line)
                    self.callback(message)
                # If the output buffer encounters an error, reconnect.
                if self.output_buffer.get_error_state():
                    self.__print(
                        "Output buffer encountered an error. Reconnecting..."
                    )
                    self.reconnect()
        # Exit the program after this loop ends.
        exit()

    def stop(self):
        """
        Stop the bot.
        """
        # Set the loop controller in run() to false
        self.running = False
        # Kill this thread too.
        exit()

    def reconnect(self):
        """
        Force the bot to reconnect to the server.
        """
        self.__disconnect(quit_message="Reconnecting...")
        time.sleep(4)
        self.__connect()

    def join_channel(self, channel):
        """
        Join a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.join_channel("#bottesting") # doctest +SKIP
        PluginBot has joined #bottesting
        """
        self.__print("Joining %s..." % channel)
        message = "JOIN %s" % channel
        self.output_buffer.send(message)

    def part_channel(self, channel):
        """
        Part a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.part_channel("#bottesting") # doctest +SKIP
        PluginBot has left #bottesting
        """
        self.__print("Parting %s..." % channel)
        message = "PART %s" % channel
        self.output_buffer.send(message)

    def ban(self, banmask, channel, reason):
        """
        Ban someone from a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.ban("*!badguy@example.com", "#bottesting", "Being a troll.")
        PluginBot sets mode +b *!badguy@example.com.
        """
        self.__print("Banning in %s with mask %s..." % (channel, banmask))
        message = "MODE +b %s %s :%s" % (channel, banmask, reason)
        self.output_buffer.send(message)

    def unban(self, banmask, channel):
        """
        Unban someone from a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.unban("*!badguy@example.com", "#bottesting")
        PluginBot sets mode -b *!badguy@example.com.
        """
        self.__print("Unbanning in %s with mask %s..." % (channel, banmask))
        message = "MODE -b %s %s" % (channel, banmask)
        self.output_buffer.send(message)

    def kick(self, nick_to_kick, channel, reason):
        """
        Kick someone from a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.kick("MrTroll", "#bottesting", "Stop trolling.")
        MrTroll left #bottesting (Stop trolling.)
        """
        self.__print("Kicking %s..." % nick_to_kick)
        message = "KICK %s %s :%s" % (channel, nick_to_kick, reason)
        self.output_buffer.send(message)

    def kickban(self, nick_to_kick, banmask, channel, reason):
        """
        Kick and ban someone from a channel.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.kickban(
        ...     "MrTroll",
        ...     "*!badguy@example.com",
        ...     "#bottesting",
        ...     "Stop trolling."
        ... ) # doctest +SKIP
        PluginBot sets mode +b *!badguy@example.com.
        MrTroll has left #bottesting (Stop trolling.)
        """
        self.__print(
            "Kickbanning %s with banmask %s from %s" % (
                nick_to_kick,
                banmask,
                channel
            )
        )
        self.ban(banmask, channel, reason)
        self.kick(nick_to_kick, channel, reason)

    def set_topic(self, channel, new_topic):
        """
        Set a channel's topic.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.set_topic("#bottesting", "Test your bots here!")
        PluginBot changed the topic to "Test your bots here!".
        """
        self.__print("Changing topic in %s to \"%s\"." % (channel, new_topic))
        message = "TOPIC %s :%s" % (channel, new_topic)
        self.output_buffer.send(message)

    def set_debugging(self, new_state):
        """
        Change the debugging mode of the bot.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.set_debugging(True)
        """
        self.__print("Setting debugging to %s" % str(new_state))
        self.debugging = new_state

    def update_chan_flood_settings(self, max_messages, time_limit):
        """
        Update the channel flood limits.
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.update_chan_flood_settings(6, 10)
        """
        self.output_buffer.set_chan_flood_settings(max_messages, time_limit)

    def register_callback(self, func):
        """
        Register the function that should recieve the Message objects
        Example:
        >>> I = IRC() # doctest +SKIP
        >>> I.register_callback(my_func)
        """
        self.callback = func
