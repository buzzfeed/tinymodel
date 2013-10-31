class ModelException(Exception):
    def __init__(self, message):
        self.message = message


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
