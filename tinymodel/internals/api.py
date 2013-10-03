import inflection
import json
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


def render_response(cls, response, return_type='json'):
    """
    Translates the given response into one or more TinyModel isntances
    based on the expected type of response.

    :param tinymodel.TinyModel cls: The base class to translate the response to.
    :param [json|tinymodel.TinyModel|foreign_model] response: The response to translates
    :param string return_type: The expected type of the response. Must be one of [tinymodel|foreign_model|json]
            These are meant to be ignored by this function and returned as is.

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    from tinymodel import TinyModel, TinyModelList
    if return_type == 'tinymodel':
        if isinstance(response, TinyModel) and not isinstance(response, TinyModelList):
            response = TinyModelList(klass=cls, data=[response.to_json(return_dict=True)])
        elif not isinstance(response, TinyModelList):
            raise TypeError('Response is a %s but we expected a TinyModel or TinyModelList' % type(response))
    elif return_type == 'foreign_model':
        if not isinstance(response, (list, tuple, set)):
            response = [response]
        response = TinyModelList(klass=cls, data=[resp.__dict__ for resp in response])
    elif return_type == 'json':
        if isinstance(response, (str, unicode)):
            response = json.loads(response)
        if not isinstance(response, list):
            response = [response]
        response = TinyModelList(klass=cls, data=response)
    else:
        raise ValueError("'%s' is not a valid return type descriptor.\n"
                         "Allowed values are 'tinymodel', 'foreign_model' and 'json'" % return_type)

    return response


def __call_service_method(cls, service, method_name, endpoint_name=None,
                      set_model_defaults=False, **kwargs):
    """
    Calls a generic method from the given class using the given params.

    :param tinymodel.TinyModel cls: The class needed to perform class-level operations.
    :param tinymodel.service.Service: An initialized Service containing the service-specific methods meant to use.
    :param str method_name: The exact name of the method to call.
    :param dict kwargs: The params to validate and send to the service-specific method.

    :rtype [tinymodel.TinyModel|list(tinymodel.TinyModel)]: The translated response.

    """
    # find special params
    extra_params = {}
    if method_name == 'find':
        extra_params['limit'] = kwargs.pop('limit')
        extra_params['offset'] = kwargs.pop('offset')
        extra_params['order_by'] = kwargs.pop('order_by')

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
    response = getattr(service, method_name)(endpoint_name=endpoint_name, **kwargs)
    return render_response(cls, response, service.return_type)


def find(cls, service, endpoint_name=None, limit=None, offset=None, order_by={},
         fuzzy=[], fuzzy_match_exclude=[], **kwargs):
    """ Performs a search operation given the passed arguments. """
    kwargs = remove_has_many_values(cls, **kwargs)
    kwargs = remove_datetime_values(cls, **kwargs)
    kwargs = remove_float_values(cls, **kwargs)
    validate_order_by(cls, order_by)
    kwargs.update({
        'offset': offset,
        'limit': limit,
        'order_by': order_by,
        'fuzzy': fuzzy,
        'fuzzy_match_exclude': fuzzy_match_exclude,
    })
    response = __call_service_method(cls, service, 'find', endpoint_name, False, **kwargs)
    return response


def create(cls, service, endpoint_name=None, **kwargs):
    """ Performs a create operation given the passed arguments, ignoring default values. """
    return __call_service_method(cls, service, 'create', endpoint_name, True, **kwargs)[0]


def delete(cls, service, endpoint_name=None, **kwargs):
    """Performs a delete operation given the passed arguments, ignoring default values."""
    kwargs = remove_has_many_values(cls, **kwargs)
    kwargs = remove_datetime_values(cls, **kwargs)
    kwargs = remove_float_values(cls, **kwargs)
    return __call_service_method(cls, service, 'delete', endpoint_name, **kwargs)[0]


def get_or_create(cls, service, endpoint_name=None, **kwargs):
    """
    Performs a get_or_create operation.

    """
    found = find(cls, service, endpoint_name, **kwargs)
    if found:
        return found[0], False
    return create(cls, service, endpoint_name, **kwargs), True


def update(cls, service, endpoint_name=None, **kwargs):
    """ Performs an update matching the given arguments. """
    return __call_service_method(cls, service, 'update', endpoint_name, False, **kwargs)[0]


def create_or_update_by(cls, service, by=[], endpoint_name=None, **kwargs):
    kwargs_find = filter(lambda (k, v): k in by, kwargs.iteritems())
    if not kwargs_find:
        raise ValueError("Missing values for 'by' parameter.")
    found_objects = find(cls=cls, service=service, endpoint_name=endpoint_name, **dict(kwargs_find))
    if found_objects:
        kwargs_update = filter(lambda (k, v): k not in by, kwargs.iteritems())
        kwargs_update.append(('id', found_objects[0].id))
        return update(cls, service, endpoint_name, **dict(kwargs_update)), False
    return create(cls, service, endpoint_name, **kwargs), True
