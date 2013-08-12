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
