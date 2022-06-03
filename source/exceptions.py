class CogNotFoundError(Exception):
    """ Should be raised if one cog can't find another cog, which is necessary for it's operating, inside the bot. """
    pass