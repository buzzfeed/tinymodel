from tinymodel.utils import ValidationError


class Service(object):
    """
    A service class provided to support CRUD or any operation using specific data
    services, it could be used to query any data storage.
    """
    ALLOWED_RETURN_TYPES = ['tinymodel', 'foreign_model', 'json']

    def __init__(self, return_type='json', **kwargs):
        """
        Make use of specific services to query any data storage.

        :params str return_type: whether to return json, foreign_model or tinymodel
        """
        if return_type not in self.ALLOWED_RETURN_TYPES:
            raise ValidationError('Service "%s" is not a valid return_type, valid options are: %s' % (str(return_type), str(self.ALLOWED_RETURN_TYPES)))
        self.return_type = return_type

        for key, value in kwargs.items():
            if not hasattr(value, '__call__'):
                raise ValidationError('"%s" param is not a callable' % str(key))
            setattr(self, key, value)
