class User(object):
    """
    An IRC user
    Setting one mode flag disables the others, as they are mutually exclusive.
    """
    def __init__(self, nick, userhost, is_admin=False):
        self.nick = nick
        self.userhost = userhost
        self.admin = is_admin
        self.modes = {"o": False, "h": False, "q": False, "v": False}

    def __str__(self,):
        return self.userhost

    def __repr__(self,):
        return {"self.nick": self.nick,
                "self.userhost": self.userhost,
                "self.admin": self.admin,
                "self.modes": self.modes}

    # Getters
    def is_op(self):
        return self.modes['o']

    def is_halfop(self):
        return self.modes['h']

    def is_owner(self):
        return self.modes['q']

    def is_voiced(self):
        return self.modes['v']

    def is_admin(self):
        return self.admin

    # Setters
    def set_op(self, new_state):
        if type(new_state) is not bool:
            raise UserError("Cannot set op to a non-boolean value")
        else:
            for mode in self.modes:
                self.modes[mode] = False
            self.modes['o'] = new_state

    def set_halfop(self, new_state):
        if type(new_state) is not bool:
            raise UserError("Cannot set halfop to a non-boolean value")
        else:
            for mode in self.modes:
                self.modes[mode] = False
            self.modes['h'] = new_state

    def set_owner(self, new_state):
        if type(new_state) is not bool:
            raise UserError("Cannot set owner to a non-boolean value")
        else:
            for mode in self.modes:
                self.modes[mode] = False
            self.modes['q'] = new_state

    def set_voiced(self, new_state):
        if type(new_state) is not bool:
            raise UserError("Cannot set voiced to a non-boolean value")
        else:
            for mode in self.modes:
                self.modes[mode] = False
            self.modes['v'] = new_state

    def set_admin(self, new_state):
        if type(new_state) is not bool:
            raise UserError("Cannot set admin to a non-boolean value")
        else:
            self.is_admin = new_state


class UserError(Exception):
    """An error when using a User object"""
    def __init__(self, message):
        self.message = message
