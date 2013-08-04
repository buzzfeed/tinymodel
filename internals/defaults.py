import pytz
import random as r
import string as s

from decimal import Decimal
from dateutil import parser as date_parser
from datetime import datetime, timedelta

COLLECTION_TYPES = (dict, list, tuple, set)
NATIVE_ATTRIBUTES = ('NATIVE_ATTRIBUTES',
                     'FIELD_DEFS',
                     'FIELDS',
                     'COLLECTION_TYPES',
                     'SUPPORTED_METHODS',
                     'SUPPORTED_BUILTINS',
                     'REMOVED_FIELDS',
                     'VALIDATION_FAILURES',
                     'VALIDATED_CLASSES',
                     'JSON_FAILURES')

SUPPORTED_METHODS = ['to_json', 'from_json', 'random']

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
        'random': lambda: ''.join(r.choice(''.join([s.digits, s.letters, ' '])) for x in range(r.randint(0, 25))).encode("ascii"),
    },
    unicode: {
        'to_json': lambda this_value: unicode(j.dumps(this_value)),
        'from_json': lambda this_value: unicode(j.loads(this_value)),
        'random': lambda: ''.join(unichr(r.choice([ord(i) for i in ''.join([s.letters, s.digits, ' '])])) for x in range(r.randint(0, 25))).encode("utf-8"),
    },
    datetime: {
        'to_json': lambda this_value: j.dumps(this_value, default=lambda obj: obj.replace(microsecond=0).isoformat()),
        'from_json': lambda this_value: date_parser.parse(j.loads(this_value)),
        'random': lambda: (datetime.utcnow() - timedelta(seconds=r.randrange(2592000))).replace(tzinfo=pytz.utc),
    },
    dict: {
        'to_json': lambda this_value: '{' + ','.join([self.__field_to_json(key) + ': ' + self.__field_to_json(value) for (key, value) in this_value.items()]) + '}',
        'from_json': lambda key_type, value_type, this_value, this_field_def: {self.__field_from_json([key_type], key, this_field_def): self.__field_from_json([value_type], value, this_field_def) for (key, value) in this_value.items()},
        'random': lambda key_type, value_type, model_recursion_depth, this_field_def: {self.__random_field(key_type, model_recursion_depth, this_field_def): self.__random_field(value_type, model_recursion_depth, this_field_def) for x in range(r.randint(0, 5))},
    },
    list: {
        'to_json': lambda this_value: '[' + ','.join([self.__field_to_json(element) for element in this_value]) + ']',
        'from_json': lambda element_type, this_value, this_field_def: [self.__field_from_json([element_type], element, this_field_def) for element in this_value],
        'random': lambda element_type, model_recursion_depth, this_field_def: [self.__random_field(element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))]
    },
    tuple: {
        'to_json': lambda this_value: '[' + ','.join([self.__field_to_json(element) for element in this_value]) + ']',
        'from_json': lambda element_type, this_value, this_field_def: tuple([self.__field_from_json([element_type], element, this_field_def) for element in this_value]),
        'random': lambda element_type, model_recursion_depth, this_field_def: tuple([self.__random_field(element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))])
    },
    set: {
        'to_json': lambda this_value: '[' + ','.join([self.__field_to_json(element) for element in this_value]) + ']',
        'from_json': lambda element_type, this_value, this_field_def: set([self.__field_from_json([element_type], element, this_field_def) for element in this_value]),
        'random': lambda element_type, model_recursion_depth, this_field_def: set([self.__random_field(element_type, model_recursion_depth, this_field_def) for x in range(r.randint(1, 5))])
    },
}
