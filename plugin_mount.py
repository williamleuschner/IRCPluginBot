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
