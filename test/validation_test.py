from datetime import datetime
from unittest import TestCase

from nose.tools import ok_
import pytz

from test.api_test import MyTinyModel
from tinymodel.internals.validation import (
    remove_has_many_values,
    remove_float_values,
    remove_datetime_values,
)


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
