class ModelException(Exception):
    pass


class ValidationError(Exception):
    pass


class SentinelValue(object):

    def __bool__(self):
        return False

UNDEFINED = SentinelValue()
