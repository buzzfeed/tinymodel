import warnings
import pytz

from datetime import datetime, timedelta
from decimal import Decimal
from unittest import TestCase
from nose.tools import eq_, ok_, assert_raises

from tinymodel import(
    TinyModel,
    ValidationError,
    FieldDef,
)


class MyValidTypeClass(object):
    """
    An example of a user-defined class that would be valid as a TinyModel field type.

    """

    def __init__(self):
        pass

    def to_json(self, **kwargs):
        return '{"foo": "bar"}'

    def from_json(self, **kwargs):
        return self

    def random(self, **kwargs):
        return self


class MyOtherValidTypeClass(object):
    """
    An example of a user-defined class that would be valid as a TinyModel field type.

    """

    def __init__(self):
        pass

    def to_json(self, **kwargs):
        return '{"foo": "bar"}'

    def from_json(self, **kwargs):
        return self

    def random(self, **kwargs):
        return self


class MyInvalidTypeClass(object):
    """
    An example of a user-defined class that would be invalid as a TinyModel field type.

    """

    def __init__(self):
        pass


class MyValidTestModel(TinyModel):
    """
    A class used for testing. It has valid type definitions that includes a valid user-defined type
    as well as all supported builtin types and various nested collections of builtins.

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_bool', required=True, validate=True, allowed_types=[bool]),
                  FieldDef(title='my_float', required=True, validate=True, allowed_types=[float]),
                  FieldDef(title='my_datetime', required=True, validate=True, allowed_types=[datetime]),
                  FieldDef(title='my_none', required=True, validate=True, allowed_types=[type(None)]),
                  FieldDef(title='my_multiple_builtin_types', required=True, validate=True, allowed_types=[int, str, bool, float]),
                  FieldDef(title='my_dict', required=True, validate=True, allowed_types=[{str: float}]),
                  FieldDef(title='my_list', required=True, validate=True, allowed_types=[[int]]),
                  FieldDef(title='my_tuple', required=True, validate=True, allowed_types=[(bool,)]),
                  FieldDef(title='my_set', required=True, validate=True, allowed_types=[set([datetime])]),
                  FieldDef(title='my_nested_dict', required=True, validate=True, allowed_types=[{str: {str: int}}]),
                  FieldDef(title='my_nested_list', required=True, validate=True, allowed_types=[[[float]]]),
                  FieldDef(title='my_nested_tuple', required=True, validate=True, allowed_types=[((int,),)]),
                  FieldDef(title='my_nested_set', required=True, validate=True, allowed_types=[set([(datetime,)])]),
                  FieldDef(title='my_multiple_nested_types', required=True, validate=True, allowed_types=[{str: {str: int}}, {str: [[float]]}]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=["discotech.test.integration.validated_model_test.MyValidTypeClass"]),
                  FieldDef(title='my_list_custom_type', required=True, validate=True, allowed_types=[["discotech.test.integration.validated_model_test.MyValidTypeClass"]]),
                  FieldDef(title='my_dict_custom_type', required=False, validate=True, allowed_types=[{"discotech.test.integration.validated_model_test.MyValidTypeClass": "discotech.test.integration.validated_model_test.MyOtherValidTypeClass"}]),
                  FieldDef(title='my_nested_list_custom_type', required=True, validate=True, allowed_types=[[["discotech.test.integration.validated_model_test.MyValidTypeClass"]]]),
                  FieldDef(title='my_nested_dict_custom_type', required=True, validate=True, allowed_types=[{str: {str: "discotech.test.integration.validated_model_test.MyValidTypeClass"}}]),
                  FieldDef(title='my_multiple_custom_types', required=True, validate=True, allowed_types=["discotech.test.integration.validated_model_test.MyValidTypeClass", "discotech.test.integration.validated_model_test.MyOtherValidTypeClass"]),
                  FieldDef(title='my_alt_custom_type', required=True, validate=True, allowed_types=[MyValidTypeClass]),
                  FieldDef(title='my_decimal_type', required=True, validate=True, allowed_types=[Decimal]),
                  ]


class MyReferentialModel(TinyModel):
    """
    A class used for testing random-object generation on a referenced child object

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_custom_type', required=True, validate=False, allowed_types=["discotech.test.integration.validated_model_test.MyValidTestModel"])]


class MySelfReferentialModel(TinyModel):
    """
    A class used for testing random-object generation on a self-referenced child object. The model_recursion_depth parameter should avoid infinite recursion.

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_custom_type', required=True, validate=False, allowed_types=["discotech.test.integration.validated_model_test.MySelfReferentialModel"])]


class MyNonJsonModel(TinyModel):
    """
    A class used for testing. This is a valid class, but should fail JSON translation because of a required, non-JSONifiable field.

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_non_json_type', required=True, validate=True, allowed_types=[{tuple([int]): int}])]


class MyMissingFieldsModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of a missing FIELD_DEFS attribute

    """

    foo = 'bar'


class MyEmptyFieldsModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because the FIELD_DEFS attribute is an empty tuple

    """

    FIELD_DEFS = []


class MyUnnamedFieldModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of a FIELD_DEFS entry that has an empty name

    """

    FIELD_DEFS = [FieldDef(title='', required=True, validate=True, allowed_types=[int])]


class MyDuplicateFieldTitlesModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of two FIELD_DEFS entries that have the same title

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_int', required=True, validate=True, allowed_types=[int])]


class MyBadButUnvalidatedTypeModel(TinyModel):
    """
    A class used for testing. Has an unsupported Python built-in type in FIELD_DEFS but will validate because the field is set to unvalidated

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_complex', required=True, validate=False, allowed_types=[complex])]


class MyUnsupportedBuiltinModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of an unsupported Python built-in type in FIELD_DEFS

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_complex', required=True, validate=True, allowed_types=[complex])]


class MyUnsupportedMethodsModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of unsupported methods in SUPPORTED_METHODS

    """

    SUPPORTED_METHODS = ['random', 'to_json', 'from_json', 'my_unsupported_method', 'my_other_unsupported_method']

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_complex', required=True, validate=True, allowed_types=[complex])]


class MyInvalidUserDefinedTypeModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of an invalid user-defined type in FIELD_DEFS

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=[MyInvalidTypeClass])]


class MyOverwrittenSupportedMethodsModel(TinyModel):
    """
    A class used for testing. This contains an invalid user-defined type, but will still validate because SUPPORTED_METHODS was overwritten

    """

    SUPPORTED_METHODS = []

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=[MyInvalidTypeClass])]


class MyInvalidContainerTypeModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of a container type with multiple elements

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_list', required=True, validate=True, allowed_types=[[int, str]])]


class MyNonExistentModuleTypeModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of a user-defined type that references a non-existent module

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=['discotech.foo.Bar'])]


class MyOptionalNonExistentModuleTypeModel(TinyModel):
    """
    A class used for testing. This has a user-defined type that references a non-existent module but will validate because the field is set as optional

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=False, validate=True, allowed_types=['discotech.foo.Bar'])]


class MyNonExistentClassTypeModel(TinyModel):
    """
    A class used for testing. This should fail to initialize because of a user-defined type that references a non-existent class

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=['discotech.test.integration.validated_model_test.Foo'])]


class MyOptionalNonExistentClassTypeModel(TinyModel):
    """
    A class used for testing. This has a user-defined type that references a non-existent class but will validate because the field is set as optional

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=False, validate=True, allowed_types=['discotech.test.integration.validated_model_test.Foo'])]


class TinyModelTest(TestCase):

    COLLECTION_TYPES = (dict, list, tuple, set)

    def __test_value(self, allowed_types, value):
        if type(value) in self.COLLECTION_TYPES:
            valid_allowed_types = [x for x in allowed_types if type(x) == type(value)]
            ok_(valid_allowed_types)
            if value and type(value) == dict:
                self.__test_value(map(lambda x: x.keys()[0], valid_allowed_types), value.keys()[0])
                self.__test_value(map(lambda x: x.values()[0], valid_allowed_types), value.values()[0])
            elif value:
                self.__test_value(map(lambda x: iter(x).next(), valid_allowed_types), iter(value).next())
        else:
            ok_(type(value) in allowed_types)

    def test_valid_fields_and_data(self):

        # tests type validation, data validation, random object generation, and translation from JSON format
        today = datetime.today().replace(tzinfo=pytz.utc)
        dbf_yesterday = today - timedelta(days=2)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        da_tomorrow = today + timedelta(days=2)

        initial = {'my_int': 1,
                   'my_str': 'butts',
                   'my_bool': True,
                   'my_float': 1.2345,
                   'my_datetime': datetime.today(),
                   'my_none': None,
                   'my_multiple_builtin_types': 1,
                   'my_dict': {'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0},
                   'my_list': [1, 2, 3, 4, 5],
                   'my_tuple': (True, False, True, True, False),
                   'my_set': {yesterday, today, tomorrow},
                   'my_nested_dict': {'dict_one': {'one': 1, 'two': 2}, 'dict_two': {'three': 3}, 'dict_three': {'four': 4, 'five': 5}},
                   'my_nested_list': [[1.0, 2.0], [3.0], [], [5.0]],
                   'my_nested_tuple': ((1, 2), (3,), (4, 5),),
                   'my_nested_set': {(dbf_yesterday, yesterday), (today,), (tomorrow, da_tomorrow), },
                   'my_multiple_nested_types': {'dict_one': {'one': 1, 'two': 2}, 'dict_two': {'three': 3}, 'dict_three': {'four': 4, 'five': 5}},
                   'my_custom_type': MyValidTypeClass(),
                   'my_list_custom_type': [MyValidTypeClass(), MyValidTypeClass()],
                   'my_dict_custom_type': {MyValidTypeClass(): MyOtherValidTypeClass()},
                   'my_nested_list_custom_type': [[MyValidTypeClass()]],
                   'my_nested_dict_custom_type': {'dict_one': {'one': MyValidTypeClass()}},
                   'my_multiple_custom_types': MyOtherValidTypeClass(),
                   'my_alt_custom_type': MyValidTypeClass(),
                   'my_decimal_type': Decimal(1.2),
                   }

        initial_json = """
                       {"my_int": 1,
                        "my_str": "butts",
                        "my_bool": true,
                        "my_float": 1.2345,
                        "my_datetime": "2013-05-06T11:30:04.518856+00:00",
                        "my_none": null,
                        "my_multiple_builtin_types": 1,
                        "my_dict": {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0},
                        "my_list": [1, 2, 3, 4, 5],
                        "my_tuple": [true, false, true, true, false],
                        "my_set": ["2013-05-05T11:30:04.518856+00:00", "2013-05-06T11:30:04.518856+00:00", "2013-05-07T11:30:04.518856+00:00"],
                        "my_nested_dict": {"dict_one": {"one": 1, "two": 2}, "dict_two": {"three": 3}, "dict_three": {"four": 4, "five": 5}},
                        "my_nested_list": [[1.0, 2.0], [3.0], [], [5.0]],
                        "my_nested_tuple": [[1, 2], [3], [4, 5]],
                        "my_nested_set": [["2013-05-03T11:30:04.518856+00:00", "2013-05-04T11:30:04.518856+00:00"], ["2013-05-05T11:30:04.518856+00:00"], ["2013-05-06T11:30:04.518856+00:00", "2013-05-07T11:30:04.518856+00:00"]],
                        "my_multiple_nested_types": {"dict_one": {"one": 1, "two": 2}, "dict_two": {"three": 3}, "dict_three": {"four": 4, "five": 5}},
                        "my_custom_type": {"foo": "bar"},
                        "my_list_custom_type": [{"foo": "bar"}, {"baz": "bat"}],
                        "my_nested_list_custom_type": [[{"foo": "bar"}]],
                        "my_nested_dict_custom_type": {"dict_one": {"one": {"foo": "bar"}}},
                        "my_multiple_custom_types": {"foo": "bar"},
                        "my_alt_custom_type": {"foo": "bar"},
                        "my_decimal_type": 1.2
                        }
                        """

        # test validation
        "CREATE VALID OBJECT:"
        my_valid_object = MyValidTestModel(**initial)
        my_valid_object.validate()

        for field_def in my_valid_object.FIELD_DEFS:
            field = next(field for field in my_valid_object.FIELDS if field.title == field_def.title)
            self.__test_value(field_def.allowed_types, getattr(my_valid_object, field_def.title))
            ok_(field.is_valid(getattr(my_valid_object, field.title)))

        # test random
        "CREATE RANDOM OBJECT:"
        my_random_object = MyValidTestModel().random()
        my_random_object.validate()

        my_random_object.validate()

        for field_def in my_random_object.FIELD_DEFS:
            field = next(field for field in my_random_object.FIELDS if field.title == field_def.title)
            self.__test_value(field_def.allowed_types, getattr(my_random_object, field_def.title))
            ok_(field.is_valid(getattr(my_random_object, field.title)))

        # test from_json
        "CREATE OBJECT FROM JSON:"
        my_object_from_json = MyValidTestModel().from_json(model_as_json=initial_json)
        my_object_from_json.validate()

        for field_def in [x for x in my_object_from_json.FIELD_DEFS if x.required]:
            field = next(field for field in my_object_from_json.FIELDS if field.title == field_def.title)
            self.__test_value(field_def.allowed_types, getattr(my_object_from_json, field_def.title))
            ok_(field.is_valid(getattr(my_object_from_json, field.title)))

        # test to_json
        my_json_obj = my_object_from_json.to_json()

    def test_missing_data(self):

        initial = {'my_int': 1,
                   'my_str': 'two'
                   }

        my_object = MyBadButUnvalidatedTypeModel(**initial)

        assert_raises(ValidationError, my_object.validate)

    def test_extra_data(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel().random()
                   }

        my_object = MyReferentialModel(**initial)
        my_object.asdd = 'asdd'

        assert_raises(ValidationError, my_object.validate)

    def test_data_change_invalidates_field(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel().random()
                   }

        my_object = MyReferentialModel(**initial)
        my_object.validate()

        for field in my_object.FIELDS:
            field_def = next(field_def for field_def in my_object.FIELD_DEFS if field_def.title == field.title)
            if field_def.validate:
                ok_(field.is_valid(getattr(my_object, field.title)))

        my_object.my_str = 'three'
        for field in my_object.FIELDS:
            field_def = next(field_def for field_def in my_object.FIELD_DEFS if field_def.title == field.title)
            if field_def.validate:
                if field.title == 'my_str':
                    ok_(not field.is_valid(getattr(my_object, field.title)))
                else:
                    ok_(field.is_valid(getattr(my_object, field.title)))

    def test_invalid_data(self):

        initial = {'my_int': 'not_an_int',
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel().random()
                   }

        non_json_initial = {'my_int': 1,
                            'my_str': "two",
                            'my_non_json_type': {tuple([1]): 2}
                            }

        unsupported_object_json = """
                                   {"my_int": {"foo": "bar"},
                                    "my_str": "two"}
                                  """

        unsupported_list_json = """
                                 {"my_int": ["foo", "bar"],
                                  "my_str": "two"}
                                """

        unsupported_base_type_json = '{"my_int": 1,"my_str": "two","my_custom_type": "three"}'

        my_object = MyReferentialModel(**initial)
        my_non_json_object = MyNonJsonModel(**non_json_initial)

        assert_raises(ValidationError, my_object.validate)

        # test various JSON data warnings
        with warnings.catch_warnings(record=True) as w:
            my_object = MyReferentialModel().from_json(model_as_json=unsupported_object_json)
            ok_(w)
            ok_("JSON 'object' type not supported" in str(w[0].message))

        with warnings.catch_warnings(record=True) as w:
            my_object = MyReferentialModel().from_json(model_as_json=unsupported_list_json)
            ok_(w)
            ok_("JSON 'array' type not supported" in str(w[0].message))

        with warnings.catch_warnings(record=True) as w:
            my_object = MyReferentialModel().from_json(model_as_json=unsupported_base_type_json)
            ok_(w)
            ok_("JSON 'string | number | true | false | null' type not supported" in str(w[0].message))

        with warnings.catch_warnings(record=True) as w:
            my_json = my_non_json_object.to_json(warning_only=True)
            ok_(w)
            ok_("could not be translated to a valid JSON object" in str(w[0].message))

        # test JSON data Exception
        assert_raises(ValidationError, MyReferentialModel().from_json, **{'model_as_json': unsupported_object_json, 'warning_only': False})

        assert_raises(Exception, my_non_json_object.to_json, **{'warning_only': False})

        # test no exceptions
        my_object = MyReferentialModel().from_json(model_as_json=unsupported_object_json,
                                                   do_validation=False,
                                                   warning_only=False)

        # test field overrides
        new_custom_field_def = FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=[str])
        kwargs = {'model_as_json': unsupported_base_type_json, 'warning_only': False, 'field_overrides': [new_custom_field_def]}
        MyReferentialModel().from_json(**kwargs)

    def test_referential_field(self):

        my_valid_object = MyReferentialModel().random()
        for field in my_valid_object.FIELD_DEFS:
            if field.validate:
                if field.title == 'my_custom_type':
                    recursed_object = getattr(my_valid_object, field.title)
                    for recursed_object_field in recursed_object.FIELD_DEFS:
                        if recursed_object_field.validate:
                            self.__test_value(recursed_object_field.allowed_types, getattr(recursed_object, recursed_object_field.title))
                else:
                    self.__test_value(field.allowed_types, getattr(my_valid_object, field.title))

    def test_cyclical_reference(self):

        my_valid_object = MySelfReferentialModel().random(model_recursion_depth=0)
        for field in my_valid_object.FIELD_DEFS:
            if field.title == 'my_custom_type':
                ok_("This is a dummy value" in getattr(my_valid_object, field.title))
            else:
                self.__test_value(field.allowed_types, getattr(my_valid_object, field.title))

    def test_bad_but_unvalidated_type(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_complex': complex(4, 5)
                   }

        my_valid_object = MyBadButUnvalidatedTypeModel(**initial)

        for field in my_valid_object.FIELD_DEFS:
            self.__test_value(field.allowed_types, getattr(my_valid_object, field.title))

    def test_supported_methods_overwrite(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyInvalidTypeClass()
                   }

        my_valid_object = MyOverwrittenSupportedMethodsModel(**initial)

        for field in my_valid_object.FIELD_DEFS:
            self.__test_value(field.allowed_types, getattr(my_valid_object, field.title))

    def test_missing_fields(self):

        initial = {'foo': 1,
                   'bar': 2,
                   'baz': 3
                   }

        assert_raises(ValidationError, MyMissingFieldsModel, **initial)

    def test_empty_fields(self):

        initial = {'foo': 1,
                   'bar': 2,
                   'baz': 3
                   }

        assert_raises(ValidationError, MyEmptyFieldsModel, **initial)

    def test_duplicate_field_titles(self):

        initial = {'foo': 1,
                   'bar': 2,
                   }

        assert_raises(ValidationError, MyDuplicateFieldTitlesModel, **initial)

    def test_unnamed_field(self):

        initial = {'foo': 1,
                   'bar': 2,
                   'baz': 3
                   }

        assert_raises(ValidationError, MyUnnamedFieldModel, **initial)

    def test_unsupported_builtin(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_complex': complex(4, 5)
                   }

        assert_raises(ValidationError, MyUnsupportedBuiltinModel, **initial)

    def test_unsupported_methods(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_complex': complex(4, 5)
                   }

        assert_raises(ValidationError, MyUnsupportedMethodsModel, **initial)

    def test_invalid_user_defined_type(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyInvalidTypeClass()
                   }

        assert_raises(ValidationError, MyInvalidUserDefinedTypeModel, **initial)

    def test_multiple_container_value_error(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_list': [int, int]
                   }

        assert_raises(Exception, MyInvalidContainerTypeModel, **initial)

    def test_non_existent_type_module_error(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'baz'
                   }

        assert_raises(ValidationError, MyNonExistentModuleTypeModel, **initial)

    def test_non_existent_type_module_error(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'baz'
                   }

        assert_raises(Exception, MyNonExistentModuleTypeModel, **initial)

    def test_non_existent_type_module_warning(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'baz'
                   }

        with warnings.catch_warnings(record=True) as w:
            my_valid_object = MyOptionalNonExistentModuleTypeModel(**initial)
            ok_(w)
            ok_("Tried to import non-existent module" in str(w[0].message))
            for (key, value) in initial.iteritems():
                ok_(hasattr(my_valid_object, key))
                eq_(value, getattr(my_valid_object, key))

    def test_non_existent_type_class_error(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'bar'
                   }

        assert_raises(Exception, MyNonExistentClassTypeModel, **initial)

    def test_non_existent_type_class_warning(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'baz'
                   }

        with warnings.catch_warnings(record=True) as w:
            my_valid_object = MyOptionalNonExistentClassTypeModel(**initial)
            ok_(w)
            ok_("Tried to access non-existent class" in str(w[0].message))
            for (key, value) in initial.iteritems():
                ok_(hasattr(my_valid_object, key))
                eq_(value, getattr(my_valid_object, key))
