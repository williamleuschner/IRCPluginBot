# Program: IRC Plugin Bot
# Developer: William Leuschner
# Creation Date: 2015-06-21
# Purpose: To provide an IRC bot that can be extended via plugins
"""A Plugin-Exensible IRC Bot"""

# Used for configuration files
import configparser
# Used for interacting with IRC
from irc import IRC

config_file_loc = "config/irc_plugin_bot-debug.ini"

config = configparser.ConfigParser()
config.read(config_file_loc)


# Plugin Mount: Attachement for plugins
# Taken from http://martyalchin.com/2008/jan/10/simple-plugin-framework/
# On 2105-06-21
class PluginMount(type):
    """
    Class for implementing plugin support
    Use ActionProvider for implementation.
    """

    def __init__(self, cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = []
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.append(cls)


class ActionProvider:
    """
    Mount point for plugins which refer to actions that can be performed.

    Plugins implementing this class should provide the following attributes:

    ========  ========================================================
    title     The text to be displayed, describing the action

    url       The URL to the view where the action will be carried out

    selected  Boolean indicating whether the action is the one
              currently being performed
    ========  ========================================================
    """
    __metaclass__ = PluginMount


# Temporary testing function to handle the callback.
def temp_func(msg_obj):
    """Temporary!"""
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
    irc.register_callback(temp_func)
    irc.start()
    # Starts the console.
    run_console()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
