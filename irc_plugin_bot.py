# Program: IRC Plugin Bot
# Developer: William Leuschner
# Creation Date: 2015-06-21
# Purpose: To provide an IRC bot that can be extended via plugins
"""A Plugin-Exensible IRC Bot"""

# Used for configuration files
import configparser
# Used for interacting with IRC
import irc
# Plugins
from plugin_mount import ActionProvider

config_file_loc = "config/irc_plugin_bot-debug.ini"

config = configparser.ConfigParser()
config.read(config_file_loc)


def quit_cmd(msg_obj):
    """
    Quit the bot
    """
    if msg_obj.is_user_msg():
        if msg_obj.userhost == config['admins'].get("primary"):
            pass


def privmsg(msg_obj):
    """
    Handle PRIVMSG messages from the server
    """
    # If the text of the message starts with an exclamation point,
    # it's a command.
    if msg_obj.text.startswith("!"):
        if msg_obj.text.startswith("!quit"):
            quit_cmd(msg_obj)
        elif msg_obj.text.startswith("!join "):
            join_cmd(msg_obj)
        elif msg_obj.text.startswith("!part "):
            part_cmd(msg_obj)
        elif msg_obj.text.startswith("!kick "):
            kick_cmd(msg_obj)
        elif msg_obj.text.startswith("!ban "):
            ban_cmd(msg_obj)
        elif msg_obj.text.startswith("!kickban "):
            kickban_cmd(msg_obj)

def action(msg_obj):
    """
    Handle ACTION messages from the server
    """
    pass


def part_msg(msg_obj):
    """
    Handle PART messages from the server
    """
    pass


def join_msg(msg_obj):
    """
    Handle JOIN messages from the server
    """
    pass


def unhandled_msg(msg_obj):
    """
    Handle messages that didn't get captured by any other
    function.
    """
    pass


def delegate_message(msg_obj):
    """
    Delegate the message object to the appropriate function based on the type.
    """
    # Switch on the type
    if msg_obj.type == "PRIVMSG":
        privmsg(msg_obj)
    elif msg_obj.type == "ACTION":
        action(msg_obj)
    elif msg_obj.type == "PART":
        part_msg(msg_obj)
    elif msg_obj.type == "JOIN":
        join_msg(msg_obj)
    else:
        unhandled_msg(msg_obj)
    if config['debug'].get("debug", "False"):
        print(str(msg_obj))


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


# Handles user input from the command line, in order to control the bot
# without being on IRC
def run_console():
    """
    Command-line interface to the bot.
    Example:
    >>> run_console()
    """
    pass


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
    # Testing
    print("Testing SSL thingy:", serverconf.get("ssl", "False"))
    # Create an ircBot object to interface with the server
    irc = IRC(
        serverconf.get("hostname", "irc.ircfox.net"),
        int(serverconf.get("port", "6697")),
        serverconf.get("nick", "FurBot"),
        serverconf.get("realname", "A plugin-exensible IRC bot"),
        ssl=str2bool(serverconf.get("ssl", "False"))
    )
    irc.set_debugging(bool(config['debug'].get("debug", "True")))
    irc.register_callback(delegate_message)
    irc.start()
    # Starts the console.
    run_console()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
