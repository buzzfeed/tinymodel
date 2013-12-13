from datetime import datetime, timedelta
import json
import random
from unittest import TestCase

from caliendo.patch import patch
from nose.tools import assert_raises, ok_, eq_

from tinymodel import TinyModel, FieldDef, api, defaults
from tinymodel.service import Service
from tinymodel.utils import ModelException


def ServiceMock(return_type='foreign_model'):
    return Service(
        return_type=return_type,
        find=lambda *args, **kwargs: [MyOtherModel(id=1)],
        create=lambda *args, **kwargs: MyOtherModel(id=1),
        update=lambda *args, **kwargs: MyOtherModel(id=1),
        delete=lambda *args, **kwargs: MyOtherModel(id=1),
        get_or_create=lambda *args, **kwargs: (True, MyOtherModel(id=1)),
        sum=lambda *args, **kwargs: {},
    )


class MyTinyModel(TinyModel):
    def __default(self):
        return True

    FIELD_DEFS = [
        FieldDef('my_int', allowed_types=[int]),
        FieldDef('my_str', allowed_types=[str]),
        FieldDef('my_bool', allowed_types=[bool]),
        FieldDef('my_list', allowed_types=[list]),
        FieldDef('my_fk', allowed_types=["test.api_test.MyOtherModel"], relationship='has_one'),
        FieldDef('my_m2m', allowed_types=[["test.api_test.MyOtherModel"]], relationship='has_many'),
        FieldDef('my_calculated_value', allowed_types=[bool], calculated=__default),
        FieldDef('my_datetime', allowed_types=[datetime]),
        FieldDef('my_float', allowed_types=[float]),
        FieldDef('my_id', allowed_types=[str, unicode]),
    ]


class MyOtherModel(TinyModel):
    FIELD_DEFS = [
        FieldDef('id', allowed_types=[long, int]),
        FieldDef('my_float', allowed_types=[float])
    ]


class MyForeignModel(object):
    def __init__(self, *args, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.iteritems()]


class APiTest(TestCase):
    TEST_DEFAULT_PARAMS = {'my_str': 'str', 'my_int': 1, 'my_bool': True, 'my_calculated_value': False}
    VALID_PARAMS = {'my_str': 'str', 'my_int': 1, 'my_bool': True, 'my_id': 'TEST'}
    INVALID_PARAMS = {'my_str': 1, 'my_fk': MyForeignModel(), 'my_fk_id': 'foo',
                      'my_m2m': [MyForeignModel()], 'my_m2m_ids': ['foo', u'bar'],
                      'foo': 'foo'}

    def test_render_to_response(self):
        json_response = json.dumps({
            "my_int": 1, "my_str": "foo", "my_bool": True,
            "my_fk": MyOtherModel(my_float=0.0).to_json(),
            "my_m2m": [MyOtherModel(my_float=0.1).to_json(), MyOtherModel(my_float=0.2).to_json()],
        })
        foreign_response = MyForeignModel(my_int=1, my_str='bar', my_bool=False,
                                          my_fk=MyOtherModel(),
                                          my_m2m=[MyOtherModel()])
        tinymodel_response = MyTinyModel(from_json=json_response)

        def __check_alien_params(resp, alien_params):
            resp, alien_params_ = resp[:1], resp[1:]
            if alien_params:
                eq_(alien_params_, alien_params)
            else:
                ok_(not alien_params_)

        def __run_simple_test(responses, return_type, alien_params=[]):
            this_response = responses.pop(return_type)
            response = api.render_to_response(MyTinyModel, this_response, return_type, *alien_params)
            __check_alien_params(response, alien_params)
            ok_(isinstance(response, list) and isinstance(response[0], MyTinyModel))
            response = api.render_to_response(MyTinyModel, [this_response], return_type, *alien_params)
            __check_alien_params(response, alien_params)
            ok_(isinstance(response, list))
            [ok_(isinstance(o, MyTinyModel)) for o in response[0]]
            for s_response in responses.values():
                assert_raises(TypeError, api.render_to_response, MyTinyModel, s_response, return_type)

        service_responses = {
            'json': json_response,
            'foreign_model': foreign_response,
            'tinymodel': tinymodel_response
        }
        for rtype in service_responses.keys():
            __run_simple_test(service_responses.copy(), rtype)

        responses = service_responses.copy()
        service_args = {}
        alien_params = [True, False, None, 1, [], {}, (), set()]
        for k in service_responses.keys():
            resp_alien_params = [random.choice(alien_params) for i in range(random.randint(1, len(alien_params)))]
            service_args[k] = resp_alien_params
        for rtype in responses.keys():
            __run_simple_test(responses.copy(), rtype, alien_params=service_args[rtype])

    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    @patch('tinymodel.internals.api.match_field_values', None)
    def test_find_matched_values_succed(self):
        service = ServiceMock(return_type='tinymodel')
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(id=1), 'my_m2m': [MyOtherModel(id=5)],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        for key in valid_params.keys():
            MyTinyModel.find(service, **{key: 'foo'})

    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_find_and_matched_values(self):
        service = ServiceMock(return_type='tinymodel')
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(id=1), 'my_m2m': [MyOtherModel(id=5)],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        invalid_params = self.INVALID_PARAMS.copy()
        invalid_params.pop('foo', None)
        invalid_names = ['my_other', 'foo', 'bar']

        # match values fails
        for key in invalid_names:
            assert_raises(ModelException, MyTinyModel.find, service, **{key: 'foo'})

        # test render_to_response
        for k, v in valid_params.iteritems():
            MyTinyModel.find(service, **{k: v})

        # limit and offset
        for k, v in valid_params.iteritems():
            MyTinyModel.find(service, limit=10, offset=1, **{k: v})

        # custom find params
        today = datetime.now()
        other_day = today - timedelta(days=random.randint(1, 7))
        valid_ranges = {
            'my_int': [{'lt': 100}, {'gt': 20}, {'lte': 100}, {'gte': 10},
                       {'gt': 10, 'lt': 100}, {'gte': 20, 'lte': 200}],
            'my_datetime': [{'lt': today}, {'gt': other_day}, {'lte': other_day}, {'gte': today},
                       {'gt': other_day, 'lt': today}, {'gte': other_day, 'lte': today},
                       {'lt': today.date()}, {'gt': today.isoformat()}],
        }
        for key, ranges in valid_ranges.iteritems():
            for r in ranges:
                MyTinyModel.find(service, **{key: r})

    @patch('tinymodel.internals.api.match_field_values', rvalue=None)
    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_create_succed(self):
        service = ServiceMock()
        MyTinyModel.create(service, **self.TEST_DEFAULT_PARAMS)
        MyTinyModel.create(service, **self.VALID_PARAMS)

    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_create_fails(self):
        service = ServiceMock(return_type='tinymodel')
        assert_raises(ModelException, MyTinyModel.create, service, **self.INVALID_PARAMS)

    @patch('tinymodel.internals.api.match_field_values', rvalue=None)
    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_delete_succed(self):
        service = ServiceMock(return_type='tinymodel')
        MyTinyModel.delete(service, **self.TEST_DEFAULT_PARAMS)
        MyTinyModel.delete(service, **self.VALID_PARAMS)

    @patch('tinymodel.internals.api.render_to_response', [{}])
    def test_delete_fails(self):
        service = ServiceMock(return_type='tinymodel')
        assert_raises(ModelException, MyTinyModel.delete, service, **self.INVALID_PARAMS)

    @patch('tinymodel.internals.api.match_field_values', rvalue=None)
    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_update_succed(self):
        service = ServiceMock()
        MyTinyModel.update(service, **self.TEST_DEFAULT_PARAMS)
        MyTinyModel.update(service, **self.VALID_PARAMS)

    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_update_fails(self):
        service = ServiceMock()
        assert_raises(ModelException, MyTinyModel.update, service, **self.INVALID_PARAMS)

    @patch('tinymodel.internals.api.match_field_values', rvalue=None)
    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_get_or_create_alt_service(self):
        service = ServiceMock()
        MyTinyModel.get_or_create(service, **self.TEST_DEFAULT_PARAMS)
        MyTinyModel.get_or_create(service, **self.VALID_PARAMS)
        assert_raises(ModelException, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)

    @patch('tinymodel.internals.api.render_to_response', rvalue=[{}])
    def test_get_or_create_alt_service_fails_match_values(self):
        service = ServiceMock()
        assert_raises(ModelException, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)

    def test_missing_service_function(self):
        service = Service()
        for service_method in ['find', 'create', 'update']:
            api_method = getattr(MyTinyModel, service_method)
            assert_raises(AttributeError, api_method, service, **self.VALID_PARAMS)

    def test_call_with_endpoint_name(self):
        methods = ['create', 'update', 'delete', 'find']
        service = ServiceMock(return_type='tinymodel')
        for method_name in methods:
            api_method = getattr(MyOtherModel, method_name)
            api_method(service, endpoint_name='endpoint_name')

    def test_api_methods_response(self):
        methods = ['create', 'update', 'delete',
                   {'method_name': 'get_or_create', 'type': tuple},
                   {'method_name': 'find', 'type': list},
                  ]
        service = ServiceMock(return_type='tinymodel')
        for method_name in methods:
            return_type = None
            if type(method_name) == dict:
                return_type = method_name['type']
                method_name = method_name['method_name']
            api_method = getattr(MyOtherModel, method_name)
            response = api_method(service)
            if return_type:
                eq_(type(response), return_type)
            else:
                ok_(not isinstance(response, defaults.COLLECTION_TYPES))

    @patch('tinymodel.internals.api.find', rvalue=[])
    @patch('tinymodel.internals.api.create', rvalue=[])
    def test_create_or_update__create(self):
        service = ServiceMock()
        params = {'name': 'test', 'id': 1}
        result, created = MyTinyModel.create_or_update_by(service, by=['id'], **params)
        ok_(created)

    @patch('tinymodel.internals.api.find', rvalue=[MyOtherModel(id=1, my_float=1.2)])
    @patch('tinymodel.internals.api.update', rvalue=[])
    def test_create_or_update__update(self):
        service = ServiceMock()
        params = {'name': 'test', 'id': 1}
        result, created = MyTinyModel.create_or_update_by(service, by=['id'], **params)
        ok_(not created)

    def test_create_or_update_fails(self):
        service = ServiceMock()
        assert_raises(ValueError, MyTinyModel.create_or_update_by, service, by=['id'])
        assert_raises(ValueError, MyTinyModel.create_or_update_by, service, by=[], **{'name': 'test'})
        assert_raises(ValueError, MyTinyModel.create_or_update_by, service, by=['id'], **{'name': 'test'})

    @patch('tinymodel.internals.api.render_to_response', rvalue=[[{}]])
    @patch('tinymodel.internals.validation.match_field_values', rvalue=[[{}]])
    def test_sum_succeed(self):
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(id=1), 'my_m2m': [MyOtherModel(id=5)],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        service = ServiceMock()
        for key in valid_params.keys():
            MyTinyModel.sum(service, return_fields=['my_int'], **{key: 'foo'})

    @patch('tinymodel.internals.api.render_to_response', rvalue=[[{}]])
    def test_sum_fails(self):
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(id=1), 'my_m2m': [MyOtherModel(id=5)],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        invalid_params = self.INVALID_PARAMS.copy()
        invalid_params.pop('foo', None)
        invalid_names = ['my_other', 'foo', 'bar']
        service = ServiceMock()
        for key in invalid_names:
            assert_raises(ModelException, MyTinyModel.sum, service, return_fields=['my_int'], **{key: 'foo'})
        for k, v in valid_params.iteritems():
            assert_raises(ValueError, MyTinyModel.sum, service, **{k: v})
