class Channel(object):
    """An IRC channel"""
    def __init__(self, name):
        self.userdict = {}
        self.modes = {}
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return {"self.userdict": self.userdict,
                "self.modes": self.modes,
                "self.name": self.name}

    def users(self):
        """
        Returns an unsorted list of the userhosts of users in this channel.
        """
        return self.userdict.keys()

    def has_user(self, userhost):
        """
        Returns true or false based on whether the specified userhost is in the
        channel.
        """
        return userhost in self.userdict.keys()

    def add_user(self, obj):
        """
        Adds a user object to the user object dictionary.
        """
        userhost = obj.userhost()
        self.userdict[userhost] = obj

    def remove_user(self, obj):
        """
        Removes a user object from the user object dictionary
        """
        userhost = obj.userhost()
        self.userdict.pop(userhost)

    def get_user(self, userhost):
        """
        Returns a user object with the specified userhost.
        """
        return self.userdict[userhost]

    def set_mode(self, mode, value=None):
        """
        Set a mode on the channel.
        `mode` -> A single-char string with the mode abbreviation
        `value` -> The value to set the mode to
        """
        try:
            self.modes[mode] = value
        except KeyError:
            raise ChannelError("Cannot set mode %s: Does not exist" % mode)

    def clear_mode(self, mode):
        """
        Clear a mode on the channel.
        `mode` -> A single-char string with the mode abbreviation
        """
        try:
            del self.modes[mode]
        except KeyError:
            raise ChannelError("Cannot clear mode %s: Does not exist" % mode)

    def has_mode(self, mode):
        return mode in self.modes

    def is_moderated(self):
        return self.has_mode("m")

    def is_secret(self):
        return self.has_mode("s")

    def is_protected(self):
        return self.has_mode("p")

    def has_topic_lock(self):
        return self.has_mode("t")

    def is_invite_only(self):
        return self.has_mode("i")

    def has_allow_external_messages(self):
        return self.has_mode("n")

    def has_limit(self):
        return self.has_mode("l")

    def limit(self):
        if self.has_limit():
            return self.modes["l"]
        else:
            return None

    def has_key(self):
        return self.has_mode("k")


class ChannelError(Exception):
    """An error when using a channel object"""
    def __init__(self, message):
        self.message = message
