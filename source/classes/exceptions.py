class AlreadyEnrolledError(BaseException):
    pass


class FullFireteamError(BaseException):
    pass


class CogNotFoundError(BaseException):
    """ Should be raised if one cog can't find another cog, which is necessary for it's operating, inside the bot. """
    pass