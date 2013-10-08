from datetime import datetime
from unittest import TestCase

from nose.tools import ok_, assert_raises, eq_
import pytz

from test.api_test import MyTinyModel, MyOtherModel
from tinymodel.internals.validation import (
    remove_has_many_values,
    remove_float_values,
    remove_datetime_values,
    validate_order_by,
    match_field_values,
)
from tinymodel.utils import ValidationError


class ValidationTest(TestCase):
    def test_remove_has_many_values(self):
        param_has_m2m = {'my_m2m': [1, 2, 2], 'my_int': 1}
        params = {'my_int': 1, 'my_str': 'foo'}

        ok_('my_m2m' not in remove_has_many_values(MyTinyModel, **param_has_m2m))
        ok_('my_m2m' not in remove_has_many_values(MyTinyModel, **params))

    def test_remove_float_values(self):
        param_has_float = {'my_m2m': [1], 'my_int': 1, 'my_float': 1.2}
        params = {'my_int': 1, 'my_str': 'foo'}

        ok_('my_float' not in remove_float_values(MyTinyModel, **param_has_float))
        ok_('my_float' not in remove_float_values(MyTinyModel, **params))

    def test_remove_datetime_values(self):
        today = today = datetime.today().replace(tzinfo=pytz.utc)
        param_has_datetime = {'my_m2m': [1], 'my_int': 1, 'my_datetime': today}
        params = {'my_int': 1, 'my_str': 'foo'}

        ok_('my_datetime' not in remove_datetime_values(MyTinyModel, **param_has_datetime))
        ok_('my_datetime' not in remove_datetime_values(MyTinyModel, **params))

    def test_order_by_find_Validation(self):
        params = {'order_by': {'my_int': None, 'my_str': 'ascending'}}
        invalid_ordering_params = {'order_by': {'my_int': ''}}
        invalid_searchable_fields_params = {'order_by': {'foo': 'descending'}}

        eq_(validate_order_by(MyTinyModel, **params), None)  # valid
        assert_raises(ValidationError, validate_order_by, MyTinyModel, **invalid_ordering_params)
        assert_raises(ValidationError, validate_order_by, MyTinyModel, **invalid_searchable_fields_params)

    def test_match_field_values(self):
        VALID_PARAMS = [
            {'my_int': 1, 'my_str': 'foo', 'my_bool': False, 'my_list': [], 'my_fk': MyOtherModel(id=1)},
            {'my_int': 1, 'my_str': 'foo',  'my_m2m': [MyOtherModel(id=1)]},
            {'my_str': ['foo', 'bar', 'baz']},
            {'my_bool': [True, False, False]},
            {'my_float': [0.5, 1.9, 2.3]},
            {'my_int': [1, 2, 3]},
            {'my_list': [[], []]},
            {'my_fk_id': 1},
            {'my_fk_id': [1, 2, 3, 4]},
        ]
        INVALID_PARAMS = [
            {'my_int': 'asd', 'my_str': 'asd'},
            {'my_int': 1, 'my_str': 1, 'my_bool': False},
            {'my_int': 1, 'my_str': 'foo', 'my_bool': 'False'},
        ]
        for params in VALID_PARAMS:
            match_field_values(MyTinyModel, **params)
        for params in INVALID_PARAMS:
            assert_raises(ValidationError, match_field_values, MyTinyModel, **params)
