import inflection
from tinymodel.internals import defaults
from tinymodel.internals.validation import (
    match_field_values,
    remove_calculated_values,
    remove_has_many_values,
    remove_float_values,
    remove_datetime_values,
    validate_order_by,
    validate_fuzzy_fields,
)


def render_to_response(cls, response, return_type='json', *alien_params):
    """
    Translates the given response into one or more TinyModel isntances
    based on the expected type of response.

    :param tinymodel.TinyModel cls: The base class to translate the response to.
    :param [json|tinymodel.TinyModel|foreign_model] response: The response to translates
    :param string return_type: The expected type of the response. Must be one of [tinymodel|foreign_model|json]
    :param list alien_params: A list of params that need to be carried from the initial response to the final response.
            These are meant to be ignored by this function and returned as is.

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    from tinymodel.service import Service
    if return_type not in Service.ALLOWED_RETURN_TYPES:
        raise ValueError('"%r" is not a valid return type for services. '
            'Allowed types are: %s' % Service.ALLOWED_RETURN_TYPES)

    is_list = True
    if return_type == 'tinymodel':
        if not isinstance(response, (list, tuple, set)):
            is_list = False
            response = [response]
        for o in response:
            if not isinstance(o, cls):
                raise TypeError('%r does not match the expected response type "tinymodel"' % o)

    elif return_type == 'foreign_model':
        if not isinstance(response, (list, tuple, set)):
            is_list = False
            response = [response]
        for o in response:
            if type(o) in (defaults.SUPPORTED_BUILTINS.keys() + list(defaults.COLLECTION_TYPES)):
                raise TypeError('Response is not a foreign model, it is of built-in type %r' % type(o))
            elif issubclass(type(o), cls.__bases__[0]):
                raise TypeError('Response is not a foreign model, it is of type %r' % cls.__bases__[0])
        response = [cls(from_foreign_model=o) for o in response]

    elif return_type == 'json':
        if isinstance(response, (list, tuple, set)):
            response = [cls(from_json=o) for o in response]
        else:
            is_list = False
            response = [cls(from_json=response)]

    response = [response] if is_list else response
    response.extend(alien_params)
    return response


def __get_resp_with_alien_params(response):
    alien_params = []
    if response and isinstance(response, (list, tuple, set)):
        response = list(response)
        response, extra = response[:1], response[1:]
        part_of_response = []

        if extra:
            resptype = type(response[0])
            for o in extra:
                if isinstance(o, resptype):
                    part_of_response.append(o)
                else:
                    alien_params.append(o)
        response.extend(part_of_response)

    return response, alien_params


def __call_api_method(cls, service, method_name, endpoint_name=None,
                      set_model_defaults=False, return_fields=[], **kwargs):
    """
    Calls a generic method from the given class using the given params.

    :param tinymodel.TinyModel cls: The class needed to perform class-level operations.
    :param tinymodel.service.Service: An initialized Service containing the service-specific methods meant to use.
    :param str method_name: The exact name of the method to call.
    :param str endpoint_name: The name of endpoint to communicate with storage.
    :param boolean set_model_defaults: True and kwargs can contain calculated values.
    :params list(str) return_fields: List of fields used in aggregation
    :param dict kwargs: The params to validate and send to the service-specific method.

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    # find special params
    extra_params = {}
    if method_name == 'find':
        extra_params['limit'] = kwargs.pop('limit')
        extra_params['offset'] = kwargs.pop('offset')
        extra_params['order_by'] = kwargs.pop('order_by')
        extra_params['expand_related'] = kwargs.pop('expand_related')

    if method_name in ('find', 'get_or_create'):
        if kwargs.get('fuzzy'):
            validate_fuzzy_fields(cls, kwargs.get('fuzzy'))
        if 'fuzzy' in kwargs:
            extra_params['fuzzy'] = kwargs.pop('fuzzy')
        if 'fuzzy_match_exclude' in kwargs:
            extra_params['fuzzy_match_exclude'] = kwargs.pop('fuzzy_match_exclude')

    kwargs = cls(set_defaults=set_model_defaults, **kwargs).to_json(return_raw=True)
    kwargs = remove_calculated_values(cls, **kwargs)
    match_field_values(cls, **kwargs)

    if not hasattr(service, method_name):
        raise AttributeError('The given service need a "%s" method!' % method_name)

    if endpoint_name is None:
        endpoint_name = inflection.underscore(cls.__name__)
    kwargs.update(extra_params)
    if method_name == 'sum':
        response = getattr(service, method_name)(endpoint_name=endpoint_name, return_fields=return_fields, **kwargs)
    else:
        response = getattr(service, method_name)(endpoint_name=endpoint_name, **kwargs)
    response, alien_params = __get_resp_with_alien_params(response)
    return render_to_response(cls, response, service.return_type, *alien_params)


def find(cls, service, endpoint_name=None, limit=None, offset=None, order_by={},
         fuzzy=[], fuzzy_match_exclude=[], expand_related=False, **kwargs):
    """ Performs a search operation given the passed arguments. """
    kwargs = remove_has_many_values(cls, **kwargs)
    kwargs = remove_float_values(cls, **kwargs)
    validate_order_by(cls, order_by)
    kwargs.update({
        'offset': offset,
        'limit': limit,
        'order_by': order_by,
        'fuzzy': fuzzy,
        'fuzzy_match_exclude': fuzzy_match_exclude,
        'expand_related': expand_related,
    })
    return __call_api_method(cls, service, 'find', endpoint_name, False, **kwargs)[0]


def create(cls, service, endpoint_name=None, **kwargs):
    """ Performs a create operation given the passed arguments, ignoring default values. """
    return __call_api_method(cls, service, 'create', endpoint_name, True, **kwargs)[0]


def delete(cls, service, endpoint_name=None, **kwargs):
    """Performs a delete operation given the passed arguments, ignoring default values."""
    kwargs = remove_has_many_values(cls, **kwargs)
    kwargs = remove_datetime_values(cls, **kwargs)
    kwargs = remove_float_values(cls, **kwargs)
    return __call_api_method(cls, service, 'delete', endpoint_name, **kwargs)[0]


def get_or_create(cls, service, endpoint_name=None, **kwargs):
    """
    Performs a <get_or_create> operation. Optionally <find> and <create> service
    methods may be used instead of a service-specific <get_or_create>
    """
    if hasattr(service, 'find') and hasattr(service, 'create') and not hasattr(service, 'get_or_create'):
        found = find(cls, service, endpoint_name, **kwargs)
        if found:
            return found[0], False
        return create(cls, service, endpoint_name, **kwargs), True
    else:
        obj, created = __call_api_method(cls, service, 'get_or_create', endpoint_name, True, **kwargs)
        assert isinstance(created, bool), '%r did not return a boolean for param "created"' % service.get_or_create
        return obj[0], created


def update(cls, service, endpoint_name=None, **kwargs):
    """ Performs an update matching the given arguments. """
    return __call_api_method(cls, service, 'update', endpoint_name, False, **kwargs)[0]


def create_or_update_by(cls, service, by=[], endpoint_name=None, **kwargs):
    kwargs_find = filter(lambda (k, v): k in by, kwargs.items())
    if not kwargs_find:
        raise ValueError("Missing values for 'by' parameter.")
    found_objects = find(cls=cls, service=service, endpoint_name=endpoint_name, **dict(kwargs_find))
    if found_objects:
        kwargs_update = filter(lambda (k, v): k not in by, kwargs.items())
        kwargs_update.append(('id', found_objects[0].id))
        return update(cls, service, endpoint_name, **dict(kwargs_update)), False
    return create(cls, service, endpoint_name, **kwargs), True


def sum(cls, service, endpoint_name=None, return_fields=[], **kwargs):
    """
    Performs a sum aggregation over return_fields matching the given arguments.
    """
    if not return_fields:
        raise ValueError("Missing values for 'return_fields' parameter.")

    kwargs = remove_has_many_values(cls, **kwargs)
    kwargs = remove_datetime_values(cls, **kwargs)
    kwargs = remove_float_values(cls, **kwargs)
    return __call_api_method(cls, service, 'sum', endpoint_name,
                             return_fields=return_fields, **kwargs)[0]
