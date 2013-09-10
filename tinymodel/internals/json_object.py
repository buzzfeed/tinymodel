import collections
import inflection
import json as j
from tinymodel.utils import ModelException

def __field_from_json(tinymodel, allowed_types, json_value, this_field_def=None):
    """
    Generates an instance of a specified type, with a value specified by a passed-in JSON object.

    :param [class | {class: class} | [class] | (class,) | {class,}] allowed_types: The allowed types of the object to generate, as an array of Python class definitions
    :param str | int | dict | list | bool | None json_value: Either a JSON-formatted string containing the value of the object we are generating,
                                                             or the value itself as an int, dict, list, bool or NoneType.
    :param FieldDef this_field_def: The field that we are generating a random value for

    :rtype object: An instance of this_type, with value specified by json_value

    """

    type_of_value = type(json_value)
    if this_field_def.relationship == "has_one":
        allowed_types += [long, int, unicode, str]
    elif this_field_def.relationship == "has_many":
        allowed_types += [[long], [int], [unicode], [str]]

    if type_of_value == dict:
        # Use first allowed dict type or user-defined type
        first_usable_type = next((t for t in allowed_types if (isinstance(t, dict) or t not in tinymodel.SUPPORTED_BUILTINS)), None)
        if isinstance(first_usable_type, dict):
            (key_type, value_type) = first_usable_type.items()[0]
            return tinymodel.SUPPORTED_BUILTINS[dict]['from_json'](tinymodel, key_type, value_type, json_value, this_field_def)
        elif first_usable_type:
            # Assume we are dealing with a valid user-defined type
            return first_usable_type(from_json=json_value, preprocessed=True)
        else:
            raise ModelException("from_json translation error in " + this_field_def.title + " field: JSON 'object' type not supported by FieldDef.allowed_types")
    elif type_of_value in tinymodel.COLLECTION_TYPES:
        # Use first allowed iterable type
        first_usable_type = next((t for t in allowed_types if (type(t) in (list, tuple, set))), None)
        if first_usable_type:
            element_type = iter(first_usable_type).next()
            return tinymodel.SUPPORTED_BUILTINS[type(first_usable_type)]['from_json'](tinymodel, element_type, json_value, this_field_def)
        else:
            raise ModelException("from_json translation error in " + this_field_def.title + " field: JSON 'array' type not supported by FieldDef.allowed_types")
    elif type_of_value == unicode:
        # Use first allowed non-collection type
        first_usable_type = next((t for t in allowed_types if (issubclass(t, type(tinymodel).__bases__[0]) or t in set(tinymodel.SUPPORTED_BUILTINS) - set(tinymodel.COLLECTION_TYPES))), None)
        if first_usable_type:
            if issubclass(first_usable_type, type(tinymodel).__bases__[0]):
                try:
                    return first_usable_type(from_json=json_value)
                except ValueError:
                    raise ModelException("from_json translation error in " + this_field_def.title + " field: JSON 'string | number | true | false | null' type not supported by ModelField.allowed_types")
                    return None
            json_value = '"' + json_value + '"'
            return tinymodel.SUPPORTED_BUILTINS[first_usable_type]['from_json'](json_value)
        else:
            raise ModelException("from_json translation error in " + this_field_def.title + " field: JSON 'string | number | true | false | null' type not supported by FieldDef.allowed_types")
    else:
        # No further translation necessary, but did we translate to an allowed type?
        if type_of_value in allowed_types:
            return json_value
        else:
            try:
                # Did not translate to an allowed type. Cast it back to JSON, find the allowed type, and translate to that.
                first_usable_type = next(iter([allowed_type for allowed_type in allowed_types]))
                return tinymodel.SUPPORTED_BUILTINS[first_usable_type]['from_json'](j.dumps(json_value))
            except KeyError:
                # Is an ids field. Just return the value.
                return json_value


def __field_to_json(tinymodel, this_value, raw=False):
    """
    Generates JSON-formatted string representation of a field value. Nested collection types are generated by recursion.

    :param object this_value: The current value of the field as a Python object.

    :rtype str: A JSON-formatted string representation of the field value

    """
    from tinymodel import TinyModel
    type_of_value = type(this_value)

    if type_of_value in tinymodel.SUPPORTED_BUILTINS:
        if type_of_value in tinymodel.COLLECTION_TYPES:
            if raw:
                if type_of_value in (list, tuple, set):
                    values = []
                    for v in this_value:
                        if isinstance(v, dict) and 'id' in v:
                            values.append(v['id'])
                        elif hasattr(v, 'id'):
                            values.append(v.id)
                        elif not isinstance(v, TinyModel):
                            values.append(v)
                return values
            return tinymodel.SUPPORTED_BUILTINS[type_of_value]['to_json'](tinymodel, this_value)
        else:
            return tinymodel.SUPPORTED_BUILTINS[type_of_value]['to_json'](this_value) if not raw else this_value
    else:
        # Assume we are dealing with a valid user-defined type
        if raw:
            if hasattr(this_value, 'id'):
                return this_value.id
        else:
            return this_value.to_json()


def from_json(tinymodel, model_as_json, preprocessed=False):
    """
    Creates an object from its JSON representation
    Simultaneously iterates over the FIELD_DEFS attribute and the passed-in JSON representation
    to translate each JSON field value into its corresponding Python FIELD_DEFS type.

    We also assume that model_as_json is formatted as a JSON dict,
    and that the keys of this dict exactly match the keys of the FIELD_DEFS attribute

    Please note that JSON supports ONLY STRINGS AS DICT KEYS!
    Dict-type fields with key types other than str are not guaranteed to work with this method.

    If multiple allowed_types are specified for a field, then the first usable type is the one used for JSON translation.

    :param str model_as_json: A representation of the model in JSON format
    :param bool preprocessed: A flag indicating whether model_as_json has already been through a JSON preprocessor

    :rtype dict: A dict of keys and values for the fields to set.

    """
    json_fields = {}
    fields_to_set = {}

    if not preprocessed:
        # Assume that the base JSON object is formatted as a dict.
        json_fields = j.loads(model_as_json)
    else:
        json_fields = model_as_json

    for (json_field_name, json_field_value) in json_fields.items():
        this_field_def = next((f for f in tinymodel.FIELD_DEFS if json_field_name in [f.title, f.title + "_id", inflection.singularize(f.title) + "_ids"]), None)
        if this_field_def:
            fields_to_set[json_field_name] = __field_from_json(tinymodel,
                                                               allowed_types=this_field_def.allowed_types,
                                                               json_value=json_field_value,
                                                               this_field_def=this_field_def)
    return fields_to_set


def to_json(tinymodel, return_dict=False, return_raw=False):
    """
    Creates a JSON representation of a model
    Iterates over the FIELD_DEFS attribute to translate each field value into its corresponding JSON representation.

    Please note that JSON supports ONLY STRINGS AS DICT KEYS!
    Dict-type fields with key types other than str are not guaranteed to work with this method.

    :rtype str: A JSON-formatted str representation of this model

    """
    json_fields = {}
    object_as_json = ''

    for field in tinymodel.FIELDS:
        if field.is_id_field:
            if isinstance(field.value, collections.Iterable):
                json_field_title = inflection.singularize(field.field_def.title) + "_ids"
            else:
                json_field_title = field.field_def.title + "_id"
        else:
            if return_raw and field.field_def.relationship == 'has_many':
                json_field_title = inflection.singularize(field.field_def.title) + "_ids"
            elif return_raw and field.field_def.relationship == 'has_one':
                json_field_title = field.field_def.title + "_id"
            else:
                json_field_title = field.field_def.title
        json_fields.update({json_field_title: __field_to_json(tinymodel, this_value=field.value, raw=return_raw)})

    if return_raw:
        return json_fields

    object_as_json = '{' + ','.join([('"' + key + '": ' + value) for (key, value) in json_fields.items()]) + '}'
    try:
        object_as_dict = j.loads(object_as_json)
    except:
        raise ModelException(str(tinymodel) + " could not be translated to a valid JSON object")
    else:
        if return_dict:
            return object_as_dict
        else:
            return object_as_json
