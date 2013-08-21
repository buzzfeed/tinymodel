from tinymodel.internals import defaults
from tinymodel.internals.validation import (
    match_model_names,
    match_field_values,
    remove_default_values,
)


def __call_api_method(cls, service, method_name, **kwargs):
    """
    Calls a generic method from the given class using the given params.

    :param tinymodel.TinyModel cls: The class needed to perform class-level operations.
    :param tinymodel.service.Service: An initialized Service containing the service-specific methods meant to use.
    :param str method_name: The exact name of the method to call.
    :param dict kwargs: The params to validate and send to the service-specific method.

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    match_model_names(cls, **kwargs)
    match_field_values(cls, **kwargs)
    if not hasattr(service, method_name):
        raise AttributeError('The given service need a "%s" method!' % method_name)
    response = getattr(service, method_name)(**kwargs)
    return render_to_response(cls, response, service.return_type)


def render_to_response(cls, response, return_type='json'):
    """
    Translates the given response into one or more TinyModel isntances
    based on the expected type of response.

    :param tinymodel.TinyModel cls: The base class to translate the response to.
    :param [json|tinymodel.TinyModel|foreign_model] response: The response to translates
    :param string return_type: The expected type of the response. Must be one of [tinymodel|foreign_model|json]

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    is_list = True
    if return_type == 'tinymodel':
        if not isinstance(response, (list, tuple, set)):
            is_list = False
            response = [response]
        for o in response:
            if not isinstance(o, cls):
                raise TypeError('%s does not match the expected response type "tinymodel"' % o)
        return response if is_list else response[0]

    elif return_type == 'foreign_model':
        if not isinstance(response, (list, tuple, set)):
            is_list = False
            response = [response]
        for o in response:
            if type(o) in (defaults.SUPPORTED_BUILTINS.keys() + list(defaults.COLLECTION_TYPES)):
                raise TypeError('Response is not a foreign model, it is of built-in type %s' % type(response))
            elif issubclass(type(o), cls.__bases__[0]):
                raise TypeError('Response is not a foreign model, it is of built-in type %s' % cls.__bases__[0])
        response = [cls(from_foreign_model=o) for o in response]
        return response if is_list else response[0]

    elif return_type == 'json':
        if isinstance(response, (list, tuple, set)):
            return [cls(from_json=o) for o in response]
        return cls(from_json=response)


def find(cls, service, **kwargs):
    """ Performs a search operation given the passed arguments. """
    return __call_api_method(cls, service, 'find', **kwargs)


def create(cls, service, **kwargs):
    """ Performs a create operation given the passed arguments, ignoring default values. """
    kwargs = remove_default_values(cls, **kwargs)
    return __call_api_method(cls, service, 'create', **kwargs)


def get_or_create(cls, service, **kwargs):
    """
    Performs a <get_or_create> operation. Optionally <find> and <create> service
    methods may be used instead of a service-specific <get_or_create>
    """
    if hasattr(service, 'find') and hasattr(service, 'create') and not hasattr(service, 'get_or_create'):
        found = find(cls, service, **kwargs)
        if found:
            return found[0]
        return create(cls, service, **kwargs)
    kwargs = remove_default_values(cls, **kwargs)
    return __call_api_method(cls, service, 'get_or_create', **kwargs)


def update(cls, service, **kwargs):
    """ Performs an update matching the given arguments. """
    kwargs = remove_default_values(cls, **kwargs)
    return __call_api_method(cls, service, 'update', **kwargs)
