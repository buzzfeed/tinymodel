def __validate_field_value(self, this_field, original_value, allowed_types, value):
    """
    A field-level validation method that checks the value of the field against the field's allowed_types

    :param Field this_field: The field whose validity we are checking
    :param original_value: The data we are validating. This is so we can keep its structure across recursive calls
    :param [class | {class: class} | [class] | (class,) | {class,}] allowed_types: The allowed data types, as an array of Python class definitions
    :param object value: The value of the field
    :rtype bool: True indicates the field's value is valid, False indicates that it is not

    """

    valid = False

    if type(value) in self.COLLECTION_TYPES:
        valid_allowed_types = [x for x in allowed_types if type(x) == type(value)]
        if valid_allowed_types:
            if value and type(value) == dict:
                key_valid = self.__validate_field_value(this_field, original_value, map(lambda x: x.keys()[0], valid_allowed_types), value.keys()[0])
                value_valid = self.__validate_field_value(this_field, original_value, map(lambda x: x.values()[0], valid_allowed_types), value.values()[0])
                valid = key_valid and value_valid
            elif value:
                valid = self.__validate_field_value(this_field, original_value, map(lambda x: iter(x).next(), valid_allowed_types), iter(value).next())
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

def validate(self, prior_errors=[], warning_only=False):
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
    instance_attributes = vars(self).copy()

    native_attributes = self.NATIVE_ATTRIBUTES

    for (key, value) in instance_attributes.items():
        if key in native_attributes:
            del instance_attributes[key]

    if not instance_attributes:
        raise ValidationError("Validation Error on " + str(self) + ": Field values do not exist!")
    if not getattr(self, 'FIELDS', False):
        raise ValidationError("Validation Error on " + str(self) + ": FIELDS array does not exist!")

    for (title, value) in instance_attributes.items():
        this_field = next((field for field in self.FIELDS if field.title == title), None)
        this_field_def = next((field_def for field_def in self.FIELD_DEFS if field_def.title == title), None)
        if (this_field_def and this_field_def.validate) and (not this_field.is_valid(value)):
            if not self.__validate_field_value(this_field=this_field, original_value=value, allowed_types=this_field_def.allowed_types, value=value):
                data_validation_errors.append("Invalid field: " + title + " has type " + str(type(value)) + " but allowed types are " + str(this_field_def.allowed_types))

    errors = prior_errors + data_validation_errors
    if errors:
        if warning_only:
            warnings.warn("Validation Errors on " + str(self) + ":\n" + "\n".join(errors))
        else:
            raise ValidationError("Validation Errors on " + str(self) + ":\n" + "\n".join(errors))
