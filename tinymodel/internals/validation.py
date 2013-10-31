import datetime
from dateutil import parser as date_parser
import inspect
import warnings
from tinymodel.internals.field_def_validation import __substitute_class_refs
from tinymodel.utils import ValidationError


def __validate_field_value(tinymodel, this_field, original_value, allowed_types, value):
    """
    A field-level validation method that checks the value of the field against the field's allowed_types

    :param Field this_field: The field whose validity we are checking
    :param original_value: The data we are validating. This is so we can keep its structure across recursive calls
    :param [class | {class: class} | [class] | (class,) | {class,}] allowed_types: The allowed data types, as an array of Python class definitions
    :param object value: The value of the field
    :rtype bool: True indicates the field's value is valid, False indicates that it is not

    """

    valid = False

    if type(value) in tinymodel.COLLECTION_TYPES:
        valid_allowed_types = [x for x in allowed_types if isinstance(x, type(value))]
        if valid_allowed_types:
            if value and isinstance(value, dict):
                key_valid = __validate_field_value(tinymodel, this_field, original_value, map(lambda x: x.keys()[0], valid_allowed_types), value.keys()[0])
                value_valid = __validate_field_value(tinymodel, this_field, original_value, map(lambda x: x.values()[0], valid_allowed_types), value.values()[0])
                valid = key_valid and value_valid
            elif value:
                valid = __validate_field_value(tinymodel, this_field, original_value, map(lambda x: iter(x).next(), valid_allowed_types), iter(value).next())
            else:
                # value is an empty collection type, but this is allowed
                valid = True
    else:
        if type(value) in allowed_types:
            valid = True
    if valid:
        this_field.last_validated_value = original_value

    this_field.was_validated = valid
    return valid


def validate(tinymodel, prior_errors=[], warning_only=False):
    """
    A model-level validation function which checks the following:
        1) The model contains no fields that are not explicitly defined in the FIELDS array
        2) All fields defined with required=True exist
        3) All existing fields contain valid values

    Exceptions are raised if any of the above is not true.

    :param [str] prior_errors: Optional list of prior errors to append to any validation errors generated
    :param bool warning_only: If True, this validation will raise only warnings instead of Exceptions

    """
    data_validation_errors = []

    # Test missing required fields
    for field_def in tinymodel.FIELD_DEFS:
        if field_def.required and not hasattr(tinymodel, field_def.title):
            data_validation_errors.append("Missing required field: " + field_def.title)

    # Test invalid field values
    for field in tinymodel.FIELDS:
        if field.field_def.validate and not field.is_valid():
            if not __validate_field_value(tinymodel, this_field=field, original_value=field.value, allowed_types=field.field_def.allowed_types, value=field.value):
                data_validation_errors.append("Invalid field: " + field.field_def.title + " has value of type " + str(type(field.value)) + " but allowed types are " + str(field.field_def.allowed_types))

    errors = prior_errors + data_validation_errors
    if errors:
        if warning_only:
            warnings.warn("Validation Errors on " + str(tinymodel) + ":\n" + "\n".join(errors))
        else:
            raise ValidationError("Validation Errors on " + str(tinymodel) + ":\n" + "\n".join(errors))


def __match_field_value(cls, name, value):
    from tinymodel import TinyModel
    def new_validation_error(value, field_name, allowed_types):
        error = '<%s %r> is not a valid value for "%s". Allowed types are: %r'
        return ValidationError(error % (type(value).__name__, value, field_name, allowed_types))

    value_type = type(value)
    if value_type in cls.COLLECTION_TYPES:
        if name.endswith('_ids') and value_type in (list, tuple, set):
            for v in value:
                if type(v) not in (long, int, str, unicode):
                    raise new_validation_error(value, name, '[list(int|long,str|unicode), tuple(int|long,str|unicode)], set(int|long,str|unicode)')
                if type(v) in (str, unicode):
                    try:
                        long(v)
                    except ValueError:
                        raise new_validation_error(value, name, '[list(int|long,str|unicode), tuple(int|long,str|unicode)], set(int|long,str|unicode)')

        else:
            try:
                field_def = filter(lambda f: f.title == name, cls.FIELD_DEFS)[0]
            except IndexError:
                # name can be fk with '_id' at the end
                field_def = filter(lambda f: f.title == name[:-3], cls.FIELD_DEFS)[0]

            for index, allowed_type in enumerate(field_def.allowed_types):
                field_def.allowed_types[index] = __substitute_class_refs(cls, field_name=field_def.title, required=field_def.required, field_type=allowed_type)

            if value and isinstance(value, dict):
                if is_lookup_dict(value):
                    validate_range_lookup(value, field_def.allowed_types)
                else:
                    key_valid = __match_field_value(cls, map(lambda x: x.keys()[0], field_def.allowed_types), value.keys()[0])
                    value_valid = __match_field_value(cls, map(lambda x: x.values()[0], field_def.allowed_types), value.values()[0])
                    if not (key_valid and value_valid):
                        raise new_validation_error(value, name, field_def.allowed_types)
            elif value:
                for v in value:
                    valid = False
                    for allowed_type in field_def.allowed_types:
                        if allowed_type in (list, tuple, set):
                            if type(v) == allowed_type:
                                valid = True
                        elif type(allowed_type) in (list, tuple, set):
                            if type(v) in allowed_type:
                                valid = True
                        elif inspect.isclass(allowed_type) and \
                            issubclass(allowed_type, TinyModel):
                            if type(v) in (long, int, unicode, str):
                                valid = True
                        elif isinstance(v, allowed_type):
                            valid = True
                    if not valid:
                        raise new_validation_error(value, name, field_def.allowed_types)
    else:
        try:
            field_def = filter(lambda f: f.title == name, cls.FIELD_DEFS)[0]
        except IndexError:  # the id is expanded with _id, remove _id
            field_def = filter(lambda f: f.title == name[:-3], cls.FIELD_DEFS)[0]

        if name.endswith('_id') and field_def.relationship != 'attribute':
            if value_type not in set(field_def.allowed_types[1:] + [long, int, str, unicode]):
                raise new_validation_error(value, name, [long, int, str, unicode])
            if value_type in (str, unicode) and not value == None:
                try:
                    long(value)
                except ValueError:
                    raise new_validation_error(value, name, [long, int, str, unicode])
        else:
            field_def = filter(lambda f: f.title == name, cls.FIELD_DEFS)[0]
            for index, allowed_type in enumerate(field_def.allowed_types):
                field_def.allowed_types[index] = __substitute_class_refs(cls, field_name=field_def.title, required=field_def.required, field_type=allowed_type)
            if value_type not in field_def.allowed_types:
                raise new_validation_error(value, name, field_def.allowed_types)


def match_field_values(cls, **kwargs):
    for name, value in kwargs.iteritems():
        __match_field_value(cls, name, value)


def __remove_values(cls, condition, **kwargs):
    keys = set(kwargs.keys())
    for field_def in cls.FIELD_DEFS:
        field_names = set([field_def.title, field_def.alias])
        if condition(field_def) and (field_names & keys):
            del kwargs[(field_names & keys).pop()]
    return kwargs


def validate_order_by(cls, order_by):
    ORDER_BY_VALUES = ['ascending', 'descending', None]
    for key, value in order_by.items():
        if key not in [title for title in [field_def.title for field_def in cls.FIELD_DEFS]]:
            raise ValidationError(str(key) + " is not valid searchable field")
        if value not in ORDER_BY_VALUES:
            raise ValidationError(str(value) + " is not a valid ordering option, valid options are: " + str(ORDER_BY_VALUES))


def validate_fuzzy_fields(cls, fields=[]):
    fuzzy_fields = filter(lambda f: f.title in fields, cls.FIELD_DEFS)
    if not fuzzy_fields:
        raise ValidationError('One or more fields indicated for fuzzy search, is not a field of %r' % cls)
    allowed_types = set([unicode, str])
    for field_def in fuzzy_fields:
        if not set(field_def.allowed_types) & allowed_types:
            raise ValidationError('%r is not a text field. Field not compatible with fuzzy search!' % field_def.title)


def validate_range_lookup(lookup_dict, allowed_types):
    """
    Validates the contents of a dictionary meant for looking up objects by a range of values.

    :param dict lookup_dict: The dictionary containing the ranges to look up by.
    :param list allowed_types: The list of types that are allowed for the field being validated.

    """
    lt_lookups = set(['lt', 'lte'])
    gt_lookups = set(['gt', 'gte'])
    lookup_keys = lt_lookups | gt_lookups

    if set(lookup_dict.keys()) - lookup_keys:
        raise ValidationError('Invalid lookup keys: %s' % (set(lookup_dict.keys()) - lookup_keys))
    if (set(lookup_dict.keys()) & lt_lookups) == lt_lookups:
        raise ValidationError('"lt" and "lte" cannot be used together:\n%s' % lookup_dict)
    if (set(lookup_dict.keys()) & gt_lookups) == gt_lookups:
        raise ValidationError('"gt" and "gte" cannot be used together:\n%s' % lookup_dict)

    for key in lookup_dict.keys():
        if type(lookup_dict[key]) == datetime.date:
            lookup_dict[key] = datetime.datetime.combine(lookup_dict[key], datetime.time())
        elif isinstance(lookup_dict[key], str):
            try:
                lookup_dict[key] = date_parser.parse(lookup_dict[key])
            except:
                pass
        if type(lookup_dict[key]) not in allowed_types:
            raise ValidationError('%r is not a valid value for this field. '
                'Valid types are: %r\n%s' % (lookup_dict[key], allowed_types, lookup_dict))

    gt_key = next(iter(set(lookup_dict.keys()) & gt_lookups), None)
    lt_key = next(iter(set(lookup_dict.keys()) & lt_lookups), None)

    if lt_key and gt_key:
        if lookup_dict[gt_key] > lookup_dict[lt_key]:
            raise ValidationError(
                '"%s" value (%s) must be less than "%s" value (%s).' % (
                    lt_key, lookup_dict[lt_key], gt_key, lookup_dict[gt_key]
                )
            )


remove_calculated_values = lambda cls, **kwargs: __remove_values(cls, lambda f: f.calculated, **kwargs)
remove_has_many_values = lambda cls, **kwargs: __remove_values(cls, lambda f: f.relationship == 'has_many', **kwargs)
remove_datetime_values = lambda cls, **kwargs: __remove_values(cls, lambda f: datetime.datetime in f.allowed_types, **kwargs)
remove_float_values = lambda cls, **kwargs: __remove_values(cls, lambda f: float in f.allowed_types, **kwargs)
is_lookup_dict = lambda dict_obj: set(['lt', 'gt', 'lte', 'gte']) & set(dict_obj.keys())
