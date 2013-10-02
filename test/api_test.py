import datetime
import json
import pytz
from unittest import TestCase
from nose.tools import assert_raises, ok_, eq_
from tinymodel import TinyModel, TinyModelList, FieldDef, api
from tinymodel.service import Service

MOCK_RETURN_VALUES = {'id': 1,
                      'my_int': 42,
                      'my_str': 'foo',
                      'my_bool': True,
                      'my_fk': {'id': 1, 'my_float': 1.5},
                      'my_m2m': [{'id': 2, 'my_float': 2.5}, {'id': 3, 'my_float': 3.5}],
                      'my_datetime': datetime.datetime.utcnow().replace(tzinfo=pytz.utc, microsecond=0),
                      'my_float': 0.5,
                      }

DT_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime)  or isinstance(obj, datetime.date) else None

class MyTinyModel(TinyModel):
    def __default(self):
        return True

    FIELD_DEFS = [
        FieldDef('id', allowed_types=[int]),
        FieldDef('my_int', allowed_types=[int]),
        FieldDef('my_str', allowed_types=[str]),
        FieldDef('my_bool', allowed_types=[bool]),
        FieldDef('my_fk', allowed_types=["test.api_test.MyOtherModel"], relationship='has_one'),
        FieldDef('my_m2m', allowed_types=[["test.api_test.MyOtherModel"]], relationship='has_many'),
        FieldDef('my_calculated_value', allowed_types=[bool], calculated=__default),
        FieldDef('my_datetime', allowed_types=[datetime.datetime]),
        FieldDef('my_float', allowed_types=[float]),
    ]


class MyOtherModel(TinyModel):
    FIELD_DEFS = [
        FieldDef('id', allowed_types=[long, int]),
        FieldDef('my_float', allowed_types=[float])
    ]


class MyForeignModel(object):
    def __init__(self, *args, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.iteritems()]


class ApiTest(TestCase):

    __json_service_methods = {'find': lambda *x, **y: json.dumps([MOCK_RETURN_VALUES], default=DT_HANDLER),
                              'create': lambda *x, **y: json.dumps(MOCK_RETURN_VALUES, default=DT_HANDLER),
                              'update': lambda *x, **y: json.dumps(MOCK_RETURN_VALUES, default=DT_HANDLER),
                              'delete': lambda *x, **y: json.dumps(MOCK_RETURN_VALUES, default=DT_HANDLER),
                             }

    __tinymodel_service_methods = {'find': lambda *x, **y: TinyModelList(klass=MyTinyModel, data=[MOCK_RETURN_VALUES]),
                                   'create': lambda *x, **y: MyTinyModel(**MOCK_RETURN_VALUES),
                                   'update': lambda *x, **y: MyTinyModel(**MOCK_RETURN_VALUES),
                                   'delete': lambda *x, **y: MyTinyModel(**MOCK_RETURN_VALUES),
                                  }

    __foreign_model_service_methods = {'find': lambda *x, **y: [MyForeignModel(**MOCK_RETURN_VALUES)],
                                       'create': lambda *x, **y: MyForeignModel(**MOCK_RETURN_VALUES),
                                       'update': lambda *x, **y: MyForeignModel(**MOCK_RETURN_VALUES),
                                       'delete': lambda *x, **y: MyForeignModel(**MOCK_RETURN_VALUES),
                                      }

    TEST_SERVICES = {'json': Service(return_type='json', **__json_service_methods),
                     'tinymodel': Service(return_type='tinymodel', **__tinymodel_service_methods),
                     'foreign_model': Service(return_type='foreign_model', **__foreign_model_service_methods),
                    }
    def test_tiny_model_list(self):
        my_list = TinyModelList(klass=MyTinyModel, data=[MOCK_RETURN_VALUES])
        my_list_2 = TinyModelList(klass=MyTinyModel, data=[MOCK_RETURN_VALUES])

        #test get item
        ok_(isinstance(my_list[0], MyTinyModel), my_list[0])
        eq_(my_list[0].my_str, 'foo', my_list[0])

        #test repr
        ok_(repr(my_list), repr(my_list))

        #test concatenation
        my_list_3 = my_list + my_list_2
        eq_(len(my_list_3), 2, my_list_3)
        ok_(isinstance(my_list_3[1], MyTinyModel), my_list_3[1])
        eq_(my_list_3[1].my_str, 'foo', my_list_3[1])

        #test append
        my_list.append(MyTinyModel(**MOCK_RETURN_VALUES))
        eq_(len(my_list), 2, my_list)
        ok_(isinstance(my_list[1], MyTinyModel), my_list[1])
        eq_(my_list[1].my_str, 'foo', my_list[1])

        #test set item
        my_list[1] = MyTinyModel(**MOCK_RETURN_VALUES)
        eq_(len(my_list), 2, my_list)
        ok_(isinstance(my_list[1], MyTinyModel), my_list[1])
        eq_(my_list[1].my_str, 'foo', my_list[1])

        #test extend
        my_list.extend([MyTinyModel(**MOCK_RETURN_VALUES), MyTinyModel(**MOCK_RETURN_VALUES)])
        eq_(len(my_list), 4, my_list)
        ok_(isinstance(my_list[3], MyTinyModel), my_list[3])
        eq_(my_list[3].my_str, 'foo', my_list[3])

        #test set slice
        my_list[2:4] = [MyTinyModel(**MOCK_RETURN_VALUES), MyTinyModel(**MOCK_RETURN_VALUES)]
        eq_(len(my_list), 4, my_list)
        ok_(isinstance(my_list[3], MyTinyModel), my_list[3])
        eq_(my_list[3].my_str, 'foo', my_list[3])

        #test get slice
        sublist = my_list[0:2]
        eq_(len(sublist), 2, sublist)
        ok_(isinstance(sublist[1], MyTinyModel), sublist[1])
        eq_(sublist[1].my_str, 'foo', sublist[1])

        #test iteration
        for item in my_list:
            item.my_str = 'bar'

        ok_(all(lambda x: x.my_str == 'bar' for x in my_list), my_list)

        #test delete item
        del(my_list[0])
        eq_(len(my_list), 3, my_list)

        #test delete slice
        del(my_list[0:2])
        eq_(len(my_list), 1, my_list)


    def test_api(self):
        for return_type, test_service in self.TEST_SERVICES.items():
            print "\n==========================="
            print "TESTING API FOR RETURN TYPE:", return_type
            found = MyTinyModel.find(service=test_service, **MOCK_RETURN_VALUES)
            MyTinyModel.create(service=test_service, **MOCK_RETURN_VALUES)
            MyTinyModel.update(service=test_service, **MOCK_RETURN_VALUES)
            MyTinyModel.delete(service=test_service, **MOCK_RETURN_VALUES)
            MyTinyModel.get_or_create(service=test_service, **MOCK_RETURN_VALUES)
            MyTinyModel.create_or_update_by(service=test_service, by=['id'], **MOCK_RETURN_VALUES)
