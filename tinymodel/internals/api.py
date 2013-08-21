from tinymodel.internals import defaults
from tinymodel.internals.validation import (
    match_model_names,
    match_field_values,
    remove_default_values,
)


def __call_api_method(cls, service, method_name, **kwargs):
    match_model_names(cls, **kwargs)
    match_field_values(cls, **kwargs)
    if not hasattr(service, method_name):
        raise AttributeError('The given service need a "%s" method!' % method_name)
    response = getattr(service, method_name)(**kwargs)
    return render_to_response(cls, response, service.return_type)


def render_to_response(cls, response, return_type='json'):
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
    return __call_api_method(cls, service, 'find', **kwargs)


def create(cls, service, **kwargs):
    kwargs = remove_default_values(cls, **kwargs)
    return __call_api_method(cls, service, 'create', **kwargs)


def update(cls, service, **kwargs):
    kwargs = remove_default_values(cls, **kwargs)
    return __call_api_method(cls, service, 'update', **kwargs)
