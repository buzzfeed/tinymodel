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
        elif this_field.is_id_field and type(value) in [int, long, unicode, str]:
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
        if field_def.required and not [f for f in tinymodel.FIELDS if f.field_def == field_def]:
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


def __extend_foreign_fields(field_defs_list):
    extended_model_names = []
    for field_def in field_defs_list:
        if field_def.relationship == 'has_one':
            extended_model_names.append(field_def.title + '_id')
        elif field_def.relationship == 'has_many':
            extended_model_names.append(field_def.title + '_ids')
    return extended_model_names


def match_model_names(cls, **kwargs):
    extended_rel_fields = __extend_foreign_fields(cls.FIELD_DEFS)
    model_names = [f.title for f in cls.FIELD_DEFS] + extended_rel_fields
    for name in kwargs.keys():
        if name not in model_names:
            raise ValidationError(
                '"{}" is not a valid parameter. Options are: {}'\
                .format(name, model_names))


def __match_field_value(cls, name, value):
    error = '"{}" is not a valid value for "{}". Allowed types are: {}'
    value_type = type(value)
    if value_type in cls.COLLECTION_TYPES:
        if name.endswith('_ids') and value_type in (list, tuple, set):
            for v in value:
                if type(v) not in (long, int, str, unicode):
                    raise ValidationError(error.format(value, name, '[list(int|long,str|unicode), tuple(int|long,str|unicode)], set(int|long,str|unicode)'))
                if type(v) in (str, unicode):
                    try:
                        long(v)
                    except ValueError:
                        raise ValidationError(error.format(value, name, '[list(int|long,str|unicode), tuple(int|long,str|unicode)], set(int|long,str|unicode)'))
        else:
            field_def = filter(lambda f: f.title == name, cls.FIELD_DEFS)[0]
            for index, allowed_type in enumerate(field_def.allowed_types):
                field_def.allowed_types[index] = __substitute_class_refs(cls, field_name=field_def.title, required=field_def.required, field_type=allowed_type)
            error = error.format(value, field_def.title, field_def.allowed_types)
            valid_allowed_types = [x for x in field_def.allowed_types if isinstance(x, value_type)]

            if valid_allowed_types:
                if value and isinstance(value, dict):
                    key_valid = __match_field_value(cls, map(lambda x: x.keys()[0], valid_allowed_types), value.keys()[0])
                    value_valid = __match_field_value(cls, map(lambda x: x.values()[0], valid_allowed_types), value.values()[0])
                    if not (key_valid and value_valid):
                        raise ValidationError(error.format(value, name, field_def.allowed_types))
                elif value:
                    for v in value:
                        valid = False
                        for allowed_type in valid_allowed_types:
                            if isinstance(allowed_type, (list, tuple, set)):
                                if type(v) in allowed_type:
                                    valid = True
                                    continue
                                else:
                                    if type(v) == allowed_type:
                                        valid = True
                                        continue
                        if not valid:
                            raise ValidationError(error.format(value, name, field_def.allowed_types))
    else:
        if name.endswith('_id'):
            if value_type not in (long, int, str, unicode):
                raise ValidationError(error.format(value, name, [long, int, str, unicode]))
            if value_type in (str, unicode):
                try:
                    long(value)
                except ValueError:
                    raise ValidationError(error.format(value, name, [long, int, str, unicode]))
        else:
            field_def = filter(lambda f: f.title == name, cls.FIELD_DEFS)[0]
            for index, allowed_type in enumerate(field_def.allowed_types):
                field_def.allowed_types[index] = __substitute_class_refs(cls, field_name=field_def.title, required=field_def.required, field_type=allowed_type)
            if value_type not in field_def.allowed_types:
                raise ValidationError(error.format(value, name, field_def.allowed_types))
            elif getattr(field_def, 'is_id_field', False) and value_type not in [int, long, unicode, str]:
                raise ValidationError(error.format(value, name, field_def.allowed_types))


def match_field_values(cls, **kwargs):
    for name, value in kwargs.iteritems():
        __match_field_value(cls, name, value)


def remove_default_values(cls, **kwargs):
    for field_def in cls.FIELD_DEFS:
        if field_def.default and field_def.title in kwargs:
            del kwargs[field_def.title]
    return kwargs
