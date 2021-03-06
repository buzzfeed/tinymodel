import pytz
import random as r
import string as s
import json as j

from decimal import Decimal
from dateutil import parser as date_parser
from datetime import datetime, timedelta

from tinymodel.internals.random_object import __random_field
from tinymodel.internals.json_object import(
    __field_to_json,
    __field_from_json,
)


COLLECTION_TYPES = (dict, list, tuple, set)
SUPPORTED_METHODS = ['to_json', 'from_json', 'random']

DATETIME_TRANSLATORS = {'to_json': lambda obj: obj.replace(microsecond=0).isoformat(),
                        'from_json': lambda json_value: date_parser.parse(j.loads(json_value)),
                        'random': lambda: (datetime.utcnow() - timedelta(seconds=r.randrange(2592000))).replace(tzinfo=pytz.utc),
                       }

SUPPORTED_BUILTINS = {
    type(None): {
        'to_json': lambda this_value: j.dumps(this_value),
        'from_json': lambda this_value=None: None,
        'random': lambda this_value=None: None,
    },
    int: {
        'to_json': lambda this_value: j.dumps(this_value),
        'from_json': lambda this_value: j.loads(this_value),
        'random': lambda: r.randint(0, 1000),
    },
    long: {
        'to_json': lambda this_value: j.dumps(this_value),
        'from_json': lambda this_value: long(j.loads(this_value)),
        'random': lambda: long(r.randint(0, 1000)),
    },
    float: {
        'to_json': lambda this_value: j.dumps(this_value),
        'from_json': lambda this_value: j.loads(this_value),
        'random': lambda: r.uniform(0, 1000),
    },
    Decimal: {
        'to_json': lambda this_value: j.dumps(float(this_value)),
        'from_json': lambda this_value: Decimal(j.loads(str(this_value))),
        'random': lambda: Decimal(r.uniform(0, 1000)),
    },
    bool: {
        'to_json': lambda this_value: j.dumps(this_value),
        'from_json': lambda this_value: j.loads(this_value),
        'random': lambda: r.choice([True, False]),
    },
    str: {
        'to_json': lambda this_value: str(j.dumps(this_value)),
        'from_json': lambda this_value: str(j.loads(this_value)),
        'random': lambda: ''.join(r.choice(''.join([s.digits, s.letters, ' '])) for x in range(r.randint(1, 25))).encode("ascii"),
    },
    unicode: {
        'to_json': lambda this_value: unicode(j.dumps(this_value)),
        'from_json': lambda this_value: unicode(j.loads(this_value)),
        'random': lambda: ''.join(unichr(r.choice([ord(i) for i in ''.join([s.letters, s.digits, ' '])])) for x in range(r.randint(1, 25))).encode("utf-8"),
    },
    datetime: {
        'to_json': lambda this_value, custom_translators=DATETIME_TRANSLATORS: j.dumps(this_value, default=custom_translators['to_json']),
        'from_json': lambda this_value, custom_translators=DATETIME_TRANSLATORS: custom_translators['from_json'](this_value),
        'random': lambda custom_translators=DATETIME_TRANSLATORS: custom_translators['random'](),
    },
    dict: {
        'to_json': lambda tinymodel, this_value: '{' + ','.join([__field_to_json(tinymodel, key) + ': ' + __field_to_json(tinymodel, value) for (key, value) in this_value.items()]) + '}',
        'from_json': lambda tinymodel, key_type, value_type, this_value, this_field_def: {__field_from_json(tinymodel, [key_type], key, this_field_def): __field_from_json(tinymodel, [value_type], value, this_field_def) for (key, value) in this_value.items()},
        'random': lambda tinymodel, key_type, value_type, model_recursion_depth, this_field_def: {__random_field(tinymodel, key_type, model_recursion_depth, this_field_def): __random_field(tinymodel, value_type, model_recursion_depth, this_field_def) for x in range(r.randint(0, 5))},
    },
    list: {
        'to_json': lambda tinymodel, this_value: '[' + ','.join([__field_to_json(tinymodel, element) for element in this_value]) + ']',
        'from_json': lambda tinymodel, element_type, this_value, this_field_def: [__field_from_json(tinymodel, [element_type], element, this_field_def) for element in this_value],
        'random': lambda tinymodel, element_type, model_recursion_depth, this_field_def: [__random_field(tinymodel, element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))]
    },
    tuple: {
        'to_json': lambda tinymodel, this_value: '[' + ','.join([__field_to_json(tinymodel, element) for element in this_value]) + ']',
        'from_json': lambda tinymodel, element_type, this_value, this_field_def: tuple([__field_from_json(tinymodel, [element_type], element, this_field_def) for element in this_value]),
        'random': lambda tinymodel, element_type, model_recursion_depth, this_field_def: tuple([__random_field(tinymodel, element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))])
    },
    set: {
        'to_json': lambda tinymodel, this_value: '[' + ','.join([__field_to_json(tinymodel, element) for element in this_value]) + ']',
        'from_json': lambda tinymodel, element_type, this_value, this_field_def: set([__field_from_json(tinymodel, [element_type], element, this_field_def) for element in this_value]),
        'random': lambda tinymodel, element_type, model_recursion_depth, this_field_def: set([__random_field(tinymodel, element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))])
    },
}
