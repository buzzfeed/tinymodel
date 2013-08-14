import random as r
import warnings
import pytz

from datetime import datetime, timedelta
from decimal import Decimal
from unittest import TestCase
from nose.tools import eq_, ok_, assert_raises

from tinymodel import(
    TinyModel,
    FieldDef,
)

from tinymodel.utils import(
    ValidationError,
    ModelException,
)

class ForeignModel(object):

    """
    A foreign model, used for testing from_foreign_model

    """
    def __init__(self, params):
        """
        Initializes a foreign model with some field values

        """
        for key, value in params.items():
            setattr(self, key, value)


class MyValidTypeClass(object):

    """
    An example of a user-defined class that would be valid as a TinyModel field type.

    """

    def __init__(self, **kwargs):
        self.id = r.randint(1,1000)

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

    def __init__(self, **kwargs):
        self.id = r.randint(1,1000)

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

    def __calc_my_default(self):
        return self.my_int + int(self.my_float)

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
                  FieldDef(title='my_default', required=True, validate=True, allowed_types=[int, long], default=__calc_my_default),
                  FieldDef(title='my_nested_dict', required=True, validate=True, allowed_types=[{str: {str: int}}]),
                  FieldDef(title='my_nested_list', required=True, validate=True, allowed_types=[[[float]]]),
                  FieldDef(title='my_nested_tuple', required=True, validate=True, allowed_types=[((int,),)]),
                  FieldDef(title='my_nested_set', required=True, validate=True, allowed_types=[set([(datetime,)])]),
                  FieldDef(title='my_multiple_nested_types', required=True, validate=True, allowed_types=[{str: {str: int}}, {str: [[float]]}]),
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=["test.model_internals_test.MyValidTypeClass"], relationship="has_one"),
                  FieldDef(title='my_list_custom_type', required=True, validate=True, allowed_types=[["test.model_internals_test.MyValidTypeClass"]], relationship="has_many"),
                  FieldDef(title='my_dict_custom_type', required=False, validate=True, allowed_types=[{"test.model_internals_test.MyValidTypeClass": "test.model_internals_test.MyOtherValidTypeClass"}]),
                  FieldDef(title='my_nested_list_custom_type', required=True, validate=True, allowed_types=[[["test.model_internals_test.MyValidTypeClass"]]]),
                  FieldDef(title='my_nested_dict_custom_type', required=True, validate=True, allowed_types=[{str: {str: "test.model_internals_test.MyValidTypeClass"}}]),
                  FieldDef(title='my_multiple_custom_types', required=True, validate=True, allowed_types=["test.model_internals_test.MyValidTypeClass", "test.model_internals_test.MyOtherValidTypeClass"], relationship="has_one"),
                  FieldDef(title='my_alt_custom_type', required=True, validate=True, allowed_types=[MyValidTypeClass], relationship="has_one"),
                  FieldDef(title='my_decimal_type', required=True, validate=True, allowed_types=[Decimal]),
                  ]


class MyReferentialModel(TinyModel):

    """
    A class used for testing random-object generation on a referenced child object

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_custom_type', required=True, validate=False, allowed_types=["test.model_internals_test.MyValidTestModel"])]


class MySelfReferentialModel(TinyModel):

    """
    A class used for testing random-object generation on a self-referenced child object. The model_recursion_depth parameter should avoid infinite recursion.

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int, long]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str, unicode]),
                  FieldDef(title='my_custom_type', required=True, validate=False, allowed_types=["test.model_internals_test.MySelfReferentialModel"])]


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
                  FieldDef(title='my_custom_type', required=True, validate=True, allowed_types=['test.model_internals_test.Foo'])]


class MyOptionalNonExistentClassTypeModel(TinyModel):

    """
    A class used for testing. This has a user-defined type that references a non-existent class but will validate because the field is set as optional

    """

    FIELD_DEFS = [FieldDef(title='my_int', required=True, validate=True, allowed_types=[int]),
                  FieldDef(title='my_str', required=True, validate=True, allowed_types=[str]),
                  FieldDef(title='my_custom_type', required=False, validate=True, allowed_types=['test.model_internals_test.Foo'])]


class TinyModelTest(TestCase):

    COLLECTION_TYPES = (dict, list, tuple, set)

    def test_valid_fields_and_data(self):

        test_alt_custom_type = MyValidTypeClass()
        test_list_custom_types = [MyValidTypeClass(), MyValidTypeClass()]

        # tests type validation, data validation, random object generation, and translation from JSON format
        today = datetime.today().replace(tzinfo=pytz.utc)
        dbf_yesterday = today - timedelta(days=2)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        da_tomorrow = today + timedelta(days=2)

        initial = {'my_int': 1,
                   'my_str': 'lol_butts',
                   'my_bool': True,
                   'my_float': 1.2345,
                   'my_datetime': datetime.utcnow().replace(tzinfo=pytz.utc).isoformat(), #test datetimes as strings
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
                   'my_alt_custom_type_id': MyValidTypeClass().id, #test is_id_field
                   'my_decimal_type': Decimal(1.2),
                   }

        initial_json = """
                       {"my_int": 1,
                        "my_str": "lol_butts",
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
                        "my_list_custom_type_ids": %s,
                        "my_nested_list_custom_type": [[{"foo": "bar"}]],
                        "my_nested_dict_custom_type": {"dict_one": {"one": {"foo": "bar"}}},
                        "my_multiple_custom_types": {"foo": "bar"},
                        "my_alt_custom_type_id": %s,
                        "my_decimal_type": 1.2
                        }
                        """ % ([o.id for o in test_list_custom_types], test_alt_custom_type.id)

        initial_foreign_model = ForeignModel(initial)

        # test validation
        my_valid_object = MyValidTestModel(**initial)
        my_valid_object.validate()

        # test that default is recalculated on field change
        eq_(my_valid_object.my_default, 2)
        my_valid_object.my_int = 3
        eq_(my_valid_object.my_default, 4)

        # test replace_refs_with_ids
        has_one_id = my_valid_object.my_custom_type.id
        has_many_ids = [o.id for o in my_valid_object.my_list_custom_type]

        my_valid_object.replace_refs_with_ids(return_copy=False)

        eq_(my_valid_object.my_custom_type, has_one_id)
        eq_(my_valid_object.my_list_custom_type, has_many_ids)

        my_valid_object.validate()

        # test random
        my_random_object = MyValidTestModel(random=True)
        my_random_object.validate()

        # test from_json
        my_object_from_json = MyValidTestModel(from_json=initial_json)
        my_object_from_json.validate()

        # test to_json
        my_json_obj = my_object_from_json.to_json(return_dict=True)

        # test from_foreign_model
        my_object_from_foreign_model = MyValidTestModel(from_foreign_model=initial_foreign_model)
        my_object_from_foreign_model.validate()

    def test_missing_data(self):

        initial = {'my_int': 1,
                   'my_str': 'two'
                   }

        my_object = MyReferentialModel(**initial)

        assert_raises(ValidationError, my_object.validate)

    def test_extra_data(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel(random=True)
                   }

        my_object = MyReferentialModel(**initial)

        assert_raises(ModelException, setattr, my_object, 'foo', 'bar')

    def test_data_change_invalidates_field(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel(random=True)
                   }

        my_object = MyReferentialModel(**initial)
        my_object.validate()

        for field in my_object.FIELDS:
            if field.field_def.validate:
                ok_(field.is_valid())

        my_object.my_str = 'three'
        for field in my_object.FIELDS:
            if field.field_def.validate:
                if field.field_def.title == 'my_str':
                    ok_(not field.is_valid())
                else:
                    ok_(field.is_valid())

    def test_invalid_data(self):

        initial = {'my_int': 'not_an_int',
                   'my_str': 'two',
                   'my_custom_type': MyValidTestModel(random=True),
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

        # test JSON data Exception
        assert_raises(ModelException, MyReferentialModel, **{'from_json': unsupported_object_json})

        assert_raises(ModelException, my_non_json_object.to_json)

    def test_referential_field(self):

        my_valid_object = MyReferentialModel(random=True)
        my_valid_object.validate()

    def test_cyclical_reference(self):

        my_valid_object = MySelfReferentialModel(random=True)
        my_valid_object.validate()

    def test_bad_but_unvalidated_type(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_complex': complex(4, 5)
                   }

        my_valid_object = MyBadButUnvalidatedTypeModel(**initial)
        my_valid_object.validate()

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

    def test_non_existent_type_class_error(self):

        initial = {'my_int': 1,
                   'my_str': 'two',
                   'my_custom_type': 'bar'
                   }

        assert_raises(Exception, MyNonExistentClassTypeModel, **initial)
