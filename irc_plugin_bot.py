# Program: IRC Plugin Bot
# Developer: William Leuschner
# Creation Date: 2015-06-21
# Purpose: To provide an IRC bot that can be extended via plugins
"""A Plugin-Exensible IRC Bot"""

# Used for configuration files
import configparser
# Used for interacting with IRC
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import irc.connection
import ssl
import irc_db
# Plugins
from plugin_mount import ActionProvider
# Allow the bot to quit
import sys

config_file_loc = "config/irc_plugin_bot.ini"

config = configparser.ConfigParser()
config.read(config_file_loc)


class PluginBot(irc.bot.SingleServerIRCBot):
    """
    The main bot definition
    """
    def __init__(
        self,
        channel,
        nickname,
        realname,
        server,
        port=6697,
        **connect_params
    ):
        self.__connect_params = connect_params
        irc.bot.SingleServerIRCBot.__init__(
            self,
            [(server, port)],
            nickname,
            realname,
            **self.__connect_params
        )
        self.channel = channel
        self.plugin_cmd_prefixes = []
        self.plugin_cmds = []

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        print("e =", str(e))
        print("e.arguments =", str(e.arguments))
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        print("e =", str(e))
        print("e.arguments =", str(e.arguments))
        message = e.arguments[0]
        if (message.startswith("!")):
            self.do_command(e, message)
        return

    def on_dccmsg(self, c, e):
        # non-chat DCC messages are raw bytes; decode as text
        text = e.arguments[0].decode('utf-8')
        c.privmsg("You said: " + text)

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_quit(self, e, cmd):
        """
        Determine if a command to quit is valid, then execute said command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                self.connection.disconnect(
                    "I was politely told to leave by %s." % e.source.nick
                )
                sys.exit(0)

    def do_reconnect(self, e, cmd):
        """
        Determine if a command to reconnect is valid, then execute said
        command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                self.connection.disconnect(
                    "I was politely told to leave by %s. I'll be back soon!"
                    % e.source.nick
                )

    def do_join(self, e, cmd):
        """
        Determine if a command to join a channel is valid, then execute
        said command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                if len(cmd_array) > 2:
                    for chan in cmd_array[2:]:
                        self.connection.join(chan)
                else:
                    self.connection.notice(
                        e.source.nick,
                        "You didn't give me any channels to join."
                    )

    def do_part(self, e, cmd):
        """
        Determine if a command to part a channel is valid, then execute
        said command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                part_msg = "Goodbye!"
                if len(cmd_array) > 2:
                    if not cmd_array[-1:][0].startswith("#"):
                        part_msg = cmd_array[-1:][0]
                    for chan in cmd_array[2:-1]:
                        self.connection.part(chan, message=part_msg)
                else:
                    self.connection.notice(
                        e.source.nick,
                        "You didn't give me any channels to part."
                    )

    def do_kick(self, e, cmd):
        """
        Determine if a command to kick a user is valid, then execute said
        command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                kick_msg = "That behaviour is not tolerated here."
                if len(cmd_array) >= 4:
                    print("The command array was longer than 4 elements.")
                    if len(cmd_array) >= 5:
                        print("The command array was longer than 5 elements.")
                        kick_msg = " ".join(cmd_array[4:])
                    self.connection.kick(
                        cmd_array[2],
                        cmd_array[3],
                        comment=kick_msg
                    )
                else:
                    self.connection.notice(
                        e.source.nick,
                        "You gave me too few arguments."
                    )

    def do_ban(self, e, cmd):
        """
        Determine if a command to ban a user is valid, then execute said
        command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        ban_cmd = "MODE %s +b %s :%s"
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                ban_msg = "The banhammer has come down."
                if len(cmd_array) >= 4:
                    if len(cmd_array) >= 5:
                        ban_msg = " ".join(cmd_array[4:])
                    self.connection.send_raw(ban_cmd % (
                        cmd_array[2],
                        cmd_array[3],
                        ban_msg
                    ))
                else:
                    self.connection.notice(
                        e.source.nick,
                        "You gave me too few arguments."
                    )

    def do_unban(self, e, cmd):
        """
        Determine if a command to unban a user is valid, then execute said
        command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        ban_cmd = "MODE %s -b %s"
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                if len(cmd_array) == 4:
                    self.connection.send_raw(ban_cmd % (
                        cmd_array[2],
                        cmd_array[3],
                    ))
                else:
                    self.connection.notice(
                        e.source.nick,
                        "You gave me too few arguments."
                    )

    def do_kickban(self, e, cmd):
        """
        Determine if a command to kicban a user is valid, then execute said
        command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        self.do_kick(e, cmd)
        self.do_ban(e, cmd)

    def do_say(self, e, cmd):
        """
        Determine if a command to speak in a channel is valid, then execute
        said command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                if len(cmd_array) >= 4 and cmd_array[2].startswith("#"):
                    self.connection.privmsg(
                        cmd_array[2],
                        " ".join(cmd_array[3:])
                    )

    def do_do(self, e, cmd):
        """
        Determine if a command to ACTION in a channel is valid, then execute
        said command.
        `e` -> Event object
        `cmd` -> Text of message (also in e.arguments)
        """
        if e.source.userhost == config['admins'].get('primary'):
            print("e.source.userhost matched the one in the config")
            if not e.target.startswith("#"):
                print("The message target was not a channel")
                cmd_array = cmd.split(" ")
                if len(cmd_array) >= 4 and cmd_array[2].startswith("#"):
                    self.connection.action(
                        cmd_array[2],
                        " ".join(cmd_array[3:])
                    )

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        if cmd.startswith("!pb "):
            if cmd.startswith("!pb quit"):
                self.do_quit(e, cmd)
            elif cmd.startswith("!pb reconnect"):
                self.do_reconnect(e, cmd)
            elif cmd.startswith("!pb join"):
                self.do_join(e, cmd)
            elif cmd.startswith("!pb part"):
                self.do_part(e, cmd)
            elif cmd.startswith("!pb kick"):
                self.do_kick(e, cmd)
            elif cmd.startswith("!pb ban"):
                self.do_ban(e, cmd)
            elif cmd.startswith("!pb unban"):
                self.do_unban(e, cmd)
            elif cmd.startswith("!pb kickban"):
                self.do_kickban(e, cmd)
            elif cmd.startswith("!pb say"):
                self.do_say(e, cmd)
            elif cmd.startswith("!pb do"):
                self.do_do(e, cmd)
        elif cmd.startswith(tuple(self.plugin_cmd_prefixes)):
            pass
        elif cmd.startswith(tuple(self.plugin_cmds)):
            pass
        else:
            c.notice(nick, "Not understood: " + cmd)


def str2bool(to_test):
    """
    Convert a string into a boolean.
    Example:
    >>> str2bool("False")
    False
    >>> str2bool("True")
    True
    """
    if to_test == "True":
        return True
    elif to_test == "False":
        return False
    else:
        return None


# Main starter function.
def main():
    """
    Run the bot.
    doctest skips this one because I haven't figured out a way to cleanly
    make the bot quit after a connection is made.
    Example:
    >>> main() # doctest: +SKIP
    """
    # Pull out just the server configuration
    serverconf = config['server']
    # This IRC framework makes SSL really hard.
    if str2bool(serverconf.get("ssl", "False")):
        new_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
    else:
        new_factory = irc.connection.Factory()
    # Create an ircBot object to interface with the server
    bot = PluginBot(
        "#bots",
        serverconf.get("nick", "PluginBot"),
        serverconf.get("realname", "A plugin-exensible IRC bot"),
        serverconf.get("hostname", "irc.esper.net"),
        int(serverconf.get("port", "6697")),
        connect_factory=new_factory
    )
    bot.start()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
