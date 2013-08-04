def SentinelValue(object):
    def __bool__(self):
        return False

UNDEFINED = SentinelValue()
