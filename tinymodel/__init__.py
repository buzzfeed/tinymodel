import copy
import inflection
from datetime import datetime
from dateutil import parser as date_parser
from pprint import pformat
from collections import Iterable

from tinymodel.internals import(
    api,
    defaults,
    field_def_validation,
    json_object,
    random_object,
    foreign_object,
    validation,
)

from utils import ModelException


class FieldDef(object):

    """
    This class is an abstract representation of a field on a TinyModel.
    Instantiated objects of this class hold class-level about the FIELD_DEFS tuple on a TinyModel definition.
    This meta-data is used for field validation, and allows us to generalize field-level operations such as
    serialization, deserialization, etc.

    """

    def __init__(self, title, required=True, validate=True, allowed_types=None,
                 relationship='attribute', calculated=None, default_value=None, choices=[]):
        """
        Creates an instance of a FieldDef object

        :param str title: The title of the field
        :param bool required: True indicates a required field, False indicates an optional field
        :param bool validate: Indicates that a field is validated during Model initialization.
        :param [ class | {class: class} | [class] | (class,) | {class,} ] allowed_types: An array of allowed types for the field
        :param str relationship: Specifies the type of relationship, for related model fields.
                                 Must be one of ['has_one' | 'has_many' | 'attribute']
        :param function calculated: A function to calculate the default value of a field.
                                 This function should take a single argument of type TinyModel

        Allowed types are represented by Python class definitions. Valid classes include
        all Python built-in types listed in TinyModel.SUPPORTED_BUILTINS. Also valid are
        nested collections of supported types, structured as dicts, lists, tuples, or sets.
        For example (int,), [[str]], and {str: float} are all valid types.

        User-defined classes are also allowed as valid types, as long as they support all
        of the methods listed in TinyModel.SUPPORTED_METHODS. If you want to use your own class
        as a field type but don't want to bother validating it, then just pass validated=False.
        Unvalidated FIELD_DEFS are allowed but are not guaranteed to work with the
        generalized field-level functionality provided in TinyModel. Use caution.

        User-defined classes may also be represented as fully-qualified import strings
        (i.e. 'models.my_model.MyClass') rather than class definitions. In this case, the
        import string is evaluated and replaced with the actual class definition when your model is initialized.
        Import errors on optional FIELD_DEFS are treated instead as warnings, and the field is removed from the model.

        This functionality allows you to use other models as foreign keys without necessarily coupling the models together.

        """
        if relationship not in ('has_one', 'has_many', 'attribute'):
            raise AttributeError("Bad value for field relationship: " + str(relationship) +
                                 "\nMust be one of the following: 'has_one', 'has_many', 'attribute'")
        self.title = title
        self.required = required
        self.validate = validate
        self.allowed_types = allowed_types
        self.relationship = relationship
        self.calculated = calculated
        self.default_value = default_value
        self.choices = choices

    def __repr__(self):
        return unicode('<tinymodel.FieldDef "%s">' % self.title)

    def has_valid_default_value(self):
        return type(self.default_value) in self.allowed_types


class Field(object):

    """
    This class is an instance-level representation of a field on a TinyModel.
    Instantiated objects of this class hold validation data about the FIELDS tuple on a TinyModel.

    """

    def __init__(self, field_def, value, is_id_field=False):
        """
        Creates an instance of a Field object

        :param str title: The title of the field

        """
        self.field_def = field_def
        self.value = value
        self.is_id_field = is_id_field
        self.was_validated = False
        self.last_validated_value = None

    def __repr__(self):
        return unicode('<tinymodel.Field "%s">' % self.field_def.title)

    def is_valid(self):
        """
        Determines whether or not a field is valid, given the current value of the field.
        Fields start as invalid, and previously validated fields become invalidated when their values change.

        :param object current_value: The current value of the field.
        :rtype bool: Flag indicating whether the field is currently valid or not.
        """
        return bool(self.was_validated and self.value == self.last_validated_value)


class TinyModel(object):

    """
    Extends the rose.model.Model class to include datatypes and related functionality

    A subset of the standard Python built-in types are supported by this class. These are listed as keys of the SUPPORTED_BUILTINS attribute.
    Each supported built-in requires some corresponding meta-data which describes how these built-ins are used by the methods listed in SUPPORTED_METHODS.
    This meta-data is expressed in the form of lambda functions, listes as values of each SUPPORTED_BUILTINS entry.

    Either or both of the SUPPORTED_BUILTINS or the SUPPORTED_METHODS attributes can be extended or overwritten.
    But be careful! Extending the SUPPORTED_METHODS attribute will also require you to extend the SUPPORTED_BUILTINS attribute as well.
    If you add support for any new types OR methods, and neglect to define new lambda functions in SUPPORTED_BUILTINS then a fatal error will be raised on validation.
    It's recommended that any new SUPPORTED_METHODS that you define accept **kwargs in the method definition, to avoid parameter errors.

    """
    VALIDATED_CLASSES = []
    COLLECTION_TYPES = defaults.COLLECTION_TYPES
    find = classmethod(api.find)
    create = classmethod(api.create)
    get_or_create = classmethod(api.get_or_create)
    update = classmethod(api.update)

    def __str__(self):
        """
        Override print method for model

        """
        return str(self.__class__) + "\nFIELDS:\n" + pformat(dict([(f.field_def.title, f.value) for f in self.FIELDS])) + "\n"

    def __setattr__(self, key, value):
        """
        Overrides __setattr__ to set the field value

        Creates and sets a field on the model, given a key and value.
        Also creates and sets _id and _ids fields for dependency fields.

        If the key does not exist in FIELD_DEFS then an error is raised.

        """
        valid_field_titles = set([key, key.rsplit("_id")[0], inflection.pluralize(key.rsplit("_ids")[0])])
        this_field_def = next((f for f in self.FIELD_DEFS if f.title in valid_field_titles), False)
        if this_field_def:
            if key == this_field_def.title:
                if type(value) in [str, unicode] and datetime in this_field_def.allowed_types:
                    try:
                        value = date_parser.parse(value)
                    except ValueError:
                        pass
                this_field = next((f for f in self.FIELDS if f.field_def.title == this_field_def.title), None)
                if not this_field:
                    self.FIELDS.append(Field(field_def=this_field_def, value=value))
                else:
                    this_field.value = value
            else:
                this_field = next((f for f in self.FIELDS if f.field_def.title == this_field_def.title and f.is_id_field), None)
                if not this_field:
                    self.FIELDS.append(Field(field_def=this_field_def, value=value, is_id_field=True))
                else:
                    this_field.value = value
        else:
            raise ModelException("Tried to set undefined field " + str(key) + " on model " + str(type(self)) + "\n" +
                                 "Available fields are: " + str([f.field_def.title for f in self.FIELDS]))

        # recalculate defaults
        for field_def in filter(lambda f: f.calculated, self.FIELD_DEFS):
            try:
                value = field_def.calculated(self)
                default_field = next((f for f in self.FIELDS if f.field_def == field_def), None)
                if not default_field:
                    self.FIELDS.append(Field(field_def=field_def, value=value))
                else:
                    default_field.value = value
            except AttributeError:
                pass

    def __getattr__(self, name):
        """
        Overrides __getattr__ to get the field value

        """
        self_fields = super(TinyModel, self).__getattribute__('FIELDS')
        valid_field_titles = set([name, name.rsplit("_id")[0], inflection.pluralize(name.rsplit("_ids")[0])])
        this_field = next((f for f in self_fields if f.field_def.title in valid_field_titles), None)
        if this_field:
            if this_field.field_def.title == name or this_field.is_id_field:
                return this_field.value
            elif "_id" in name and this_field.field_def.relationship == 'has_one' and hasattr(this_field.value, 'id'):
                return this_field.value.id
            elif "_ids" in name and this_field.field_def.relationship == 'has_many' and isinstance(this_field.value, Iterable) and all(hasattr(v, 'id') for v in this_field.value):
                return [v.id for v in this_field.value]
            else:
                raise AttributeError(str(self) + "is missing id attribute on field " + this_field.field_def.title)
        else:
            raise AttributeError(str(self) + " has no field " + name)

    def __delattr__(self, name):
        """
        Overrides __delattr__ to remove the field

        """
        self_fields = super(TinyModel, self).__getattribute__('FIELDS')
        this_field = next((f for f in self_fields if f.field_def.title == name), None)
        if this_field:
            self.FIELDS.remove(this_field)
        else:
            raise AttributeError(str(type(self)) + " has no field " + name)

    def __init__(self, from_json=False, from_foreign_model=False, random=False,
                 model_recursion_depth=1, preprocessed=False, set_defaults=True, **kwargs):
        """
        Checks validity of type definitions and initializes the Model

        :param str from_json: A json representation of the model, to initialize from json if desired
        :param object from_foreign_model: Another type of model class (Django model for example) that has attributes whose titles match the keys of FIELD_DEFS.
        :param bool random: A flag indicating whether the model properties should be initialized to random values.
        :param int model_recursion_depth: Used in conjunction with random. Determines how many times to recurse when generating parents and children.
        :param bool preprocessed: A flag indicating whether from_json has already been through a JSON preprocessor
        :param objects **kwargs: The initial values of each field can be passed in as a keyword parameter.
                               Values are not validated until you call Model.validate()

        """
        super(TinyModel, self).__setattr__('FIELDS', [])
        super(TinyModel, self).__setattr__('VALIDATION_FAILURES', [])
        super(TinyModel, self).__setattr__('JSON_FAILURES', [])
        super(TinyModel, self).__setattr__('REMOVED_FIELDS', [])

        # set supported methods and builtins
        if not getattr(self, 'SUPPORTED_METHODS', False):
            super(TinyModel, self).__setattr__('SUPPORTED_METHODS', defaults.SUPPORTED_METHODS)
        if not getattr(self, 'SUPPORTED_BUILTINS', False):
            super(TinyModel, self).__setattr__('SUPPORTED_BUILTINS', defaults.SUPPORTED_BUILTINS)

        # validate model definition if it hasn't been already
        if type(self) not in self.VALIDATED_CLASSES:
            field_def_validation.validate_builtin_method_support(self)
            field_def_validation.validate_field_types(self)
            self.VALIDATED_CLASSES.append(type(self))

        # set initial values
        if from_json:
            initial_attributes = self.__from_json(from_json, preprocessed=preprocessed)
        elif from_foreign_model:
            initial_attributes = self.__from_foreign_model(from_foreign_model)
        elif random:
            initial_attributes = self.__from_random(model_recursion_depth=model_recursion_depth)
        else:
            initial_attributes = kwargs

        # add fields for initial values, and set them. including relationship support fields
        for (key, value) in initial_attributes.items():
            setattr(self, key, value)
        if set_defaults:
            # set default values for fields not passed
            for this_field_def in set(self.FIELD_DEFS) - set(f.field_def for f in self.FIELDS):
                if this_field_def.has_valid_default_value() and not this_field_def.title in ['id']:  # if not, let it raise an Exception, warning about missing data
                    setattr(self, this_field_def.title, this_field_def.default_value)

    __from_json = json_object.from_json
    __from_foreign_model = foreign_object.from_foreign_model
    __from_random = random_object.random
    to_json = json_object.to_json
    validate = validation.validate

    def from_json(self, model_as_json, preprocessed=False):
        return self.__from_json(self, model_as_json, preprocessed)

    def random(self, model_recursion_depth=1):
        return self.__from_random(self, model_recursion_depth)

    def replace_refs_with_ids(self, return_copy=True):
        """
        If the model has foreign key references, replace them with id fields

        :param bool return_copy: If True, returns a copy of self. If False, mutes self.

        :rtype TinyModel: The TinyModel, with refs to other models replaced by ids.

        """
        if return_copy:
            copy_of_self = copy.deepcopy(self)
        else:
            copy_of_self = self
        fields_to_remove = []
        for field in copy_of_self.FIELDS:
            try:
                if field.field_def.relationship == 'has_one' and not field.is_id_field:
                    setattr(copy_of_self, field.field_def.title + "_id", field.value.id)
                    fields_to_remove.append(field.field_def.title)
                if field.field_def.relationship == 'has_many' and not field.is_id_field:
                    setattr(copy_of_self, inflection.singularize(field.field_def.title) + "_ids", [o.id for o in field.value])
                    fields_to_remove.append(field.field_def.title)
            except AttributeError:
                if field.field_def.relationship == 'has_one' and not field.is_id_field and field.value:
                    setattr(copy_of_self, field.field_def.title + "_id", field.value)
                    fields_to_remove.append(field.field_def.title)

        for field in fields_to_remove:
            delattr(copy_of_self, field)

        return copy_of_self
