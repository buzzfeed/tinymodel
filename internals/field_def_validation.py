import warnings
import collections

from importlib import import_module


def validate_builtin_method_support(tinymodel):
    """
    Checks that all of the builtins defined in SUPPORTED_BUILTINS support all of methods defined in SUPPORTED_METHODS
    Raises an Exception if support is missing for any method, on any builtin

    """
    for method in tinymodel.SUPPORTED_METHODS:
        for (builtin, builtin_supported_methods) in tinymodel.SUPPORTED_BUILTINS.items():
            if method not in builtin_supported_methods:
                tinymodel.VALIDATION_FAILURES.append(method + " not supported by builtin type: " + str(builtin))
    if tinymodel.VALIDATION_FAILURES:
        raise ValidationError("Supported methods validation failed on TinyModel of class " + str(type(tinymodel)) + "\nUnsupported methods:\n" + "\n".join(tinymodel.VALIDATION_FAILURES))


def validate_field_types(tinymodel):
    """
    Checks that all of the type definitions fields defined in the FIELD_DEFS array are structured correctly,
    and that they contain valid builtins and user-defined classes. Classes defined with input strings are evaluated and replaced.

    Raises an Exception if any invalid fields are found.

    """
    if getattr(tinymodel, 'FIELD_DEFS', False):
        duplicate_field_titles = [x for x, y in collections.Counter([field.title for field in tinymodel.FIELD_DEFS]).items() if y > 1]
        if duplicate_field_titles:
            raise ValidationError("Duplicate field titles in FIELD_DEFS for TinyModel " + str(tinymodel) + ": " + " ".join(duplicate_field_titles))
        for field in tinymodel.FIELD_DEFS:
            if not field.title:
                raise ValidationError("Field validation failed on TinyModel of class " + str(type(tinymodel)) + ". Field name cannot be empty!")
            for index, field_type in enumerate(field.allowed_types):
                field.allowed_types[index] = __substitute_class_refs(field_name=field.title, required=field.required, field_type=field_type)

        new_fields_list = []
        for key, val in enumerate(tinymodel.FIELD_DEFS):
            if val.title in tinymodel.REMOVED_FIELDS:
                del tinymodel.FIELD_DEFS[key]

        for field_def in tinymodel.FIELD_DEFS:
            for field_type in field_def.allowed_types:
                if field_def.validate:
                    __validate_type(field_name=field_def.title, field_type=field_type)
        if tinymodel.VALIDATION_FAILURES:
            raise ValidationError("Field types validation failed on TinyModel of class " + str(type(tinymodel)) + "\nInvalid types:\n" + "\n".join(tinymodel.VALIDATION_FAILURES))
    else:
        raise ValidationError("FIELD_DEFS list is missing or empty on TinyModel of class " + str(type(tinymodel)))


def __validate_type(tinymodel, field_name, field_type):
    """
    Checks the validity of a field type. Collection types (i.e. dict, list, tuple and set) are handled recursively.
    Any failures encountered are added to the private attribute VALIDATION_FAILURES

    :param str field_name: The name of the field we are validating
    :param class | {class: class} | [class] | (class,) | {class,} field_type: The field type, as a Python class definition

    """

    if type(field_type) in (list, tuple, set):
        for element in field_type:
            __validate_type(field_name=field_name, field_type=element)
    elif isinstance(field_type, dict):
        for key, value in field_type.iteritems():
            __validate_type(field_name=field_name, field_type=key)
            __validate_type(field_name=field_name, field_type=value)
    elif isinstance(field_type, type):
        if field_type not in tinymodel.SUPPORTED_BUILTINS:
            for required_method in tinymodel.SUPPORTED_METHODS:
                if required_method not in dir(field_type):
                    tinymodel.VALIDATION_FAILURES.append(field_name + ": " + str(field_type) + " missing required method " + required_method)
    else:
        tinymodel.VALIDATION_FAILURES.append(field_name + ": " + str(type(field_type)) + " not a recognized type")


def __substitute_class_refs(tinymodel, field_name, required, field_type):
    """
    Recurses through field_type and replaces references to classes with the actual class definitions.
    An error is raised if the class module cannot be found. In the case of an optional FIELD_DEF, a warning is raised
    instead of an error, and the field is removed from the Model.

    :param str field_name: The name of the field
    :param bool required: True indicates a required field. False indicates and optional field
    :param class | {class: class} | [class] | (class,) | {class,} field_type: The field type, as a Python class definition

    """
    if type(field_type) in tinymodel.COLLECTION_TYPES and len(field_type) > 1:
        raise Exception(str(type(field_type)) + " field types can only have one element: " + field_name + " on TinyModel " + str(type(tinymodel)))
    elif isinstance(field_type, list):
        return [__substitute_class_refs(field_name=field_name, required=required, field_type=field_type[0])]
    elif isinstance(field_type, tuple):
        return tuple([__substitute_class_refs(field_name=field_name, required=required, field_type=field_type[0])])
    elif isinstance(field_type, set):
        return set([__substitute_class_refs(field_name=field_name, required=required, field_type=iter(field_type).next())])
    elif isinstance(field_type, dict):
        key, value = field_type.items()[0]
        return_key = __substitute_class_refs(field_name=field_name, required=required, field_type=key)
        return_value = __substitute_class_refs(field_name=field_name, required=required, field_type=value)
        return {return_key: return_value}
    elif isinstance(field_type, str):
        this_module_name = ""
        this_class_name = ""
        try:
            this_module_name, this_class_name = field_type.rsplit(".", 1)
            this_module = import_module(this_module_name)
            return getattr(this_module, this_class_name)
        except ImportError:
            if required:
                raise Exception("Tried to import non-existent module " + this_module_name + " on field " + field_name + " of TinyModel " + str(type(tinymodel)))
            else:
                warnings.warn("Tried to import non-existent module " + this_module_name + " on field " + field_name + " of TinyModel " + str(type(tinymodel)) + "\nThis field will be removed from the model.")
                tinymodel.REMOVED_FIELDS.append(field_name)
                return field_type
        except AttributeError:
            if required:
                raise Exception("Tried to access non-existent class " + field_type + " on field " + field_name + " of TinyModel " + str(type(tinymodel)))
            else:
                warnings.warn("Tried to access non-existent class " + field_type + " on field " + field_name + " of TinyModel " + str(type(tinymodel)) + "\nThis field will be removed from the model.")
                tinymodel.REMOVED_FIELDS.append(field_name)
                return field_type
        except Exception as e:
            raise e
    else:
        return field_type
