from datetime import datetime
import json
import random
from unittest import TestCase
from mock import patch, MagicMock
from nose.tools import assert_raises, ok_, eq_
from tinymodel import TinyModel, FieldDef, api, defaults
from tinymodel.service import Service
from tinymodel.utils import ModelException


class MyTinyModel(TinyModel):
    def __default(self):
        return True

    FIELD_DEFS = [
        FieldDef('my_int', allowed_types=[int]),
        FieldDef('my_str', allowed_types=[str]),
        FieldDef('my_bool', allowed_types=[bool]),
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

    def test_find_and_match_values(self):
        service = Service(find=MagicMock())
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(id=1), 'my_m2m': [MyOtherModel(id=5)],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        invalid_params = self.INVALID_PARAMS.copy()
        invalid_params.pop('foo', None)
        invalid_names = ['my_other', 'foo', 'bar']

        with patch('tinymodel.internals.api.render_to_response'):
            with patch('tinymodel.internals.api.match_field_values') as match_values1:
                for key in valid_params.keys():
                    MyTinyModel.find(service, **{key: 'foo'})
                    ok_(match_values1.called)
            with patch('tinymodel.internals.api.match_field_values') as match_values2:
                for key in invalid_names:
                    assert_raises(ModelException, MyTinyModel.find, service, **{key: 'foo'})
                    ok_(not match_values2.called)

        with patch('tinymodel.internals.api.render_to_response') as renderer1:
            for k, v in valid_params.iteritems():
                MyTinyModel.find(service, **{k: v})
                ok_(renderer1.called)

        # test limit and offset
        with patch('tinymodel.internals.api.render_to_response') as renderer1:
            for k, v in valid_params.iteritems():
                MyTinyModel.find(service, limit=10, offset=1, **{k: v})
                ok_(renderer1.called)

    def test_create(self):
        service = Service(create=MagicMock())
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.render_to_response') as rendered1:
                MyTinyModel.create(service, **self.TEST_DEFAULT_PARAMS)
                ok_(rendered1.called)

            with patch('tinymodel.internals.api.render_to_response') as rendered2:
                MyTinyModel.create(service, **self.VALID_PARAMS)
                ok_(rendered2.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered3:
            assert_raises(ModelException, MyTinyModel.create, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ModelException, MyTinyModel.create, service, **self.INVALID_PARAMS)
                ok_(not rendered4.called)

    def test_update(self):
        service = Service(update=MagicMock())
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.render_to_response') as rendered1:
                MyTinyModel.update(service, **self.TEST_DEFAULT_PARAMS)
                ok_(rendered1.called)

            with patch('tinymodel.internals.api.render_to_response') as rendered2:
                MyTinyModel.update(service, **self.VALID_PARAMS)
                ok_(rendered2.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered3:
            assert_raises(ModelException, MyTinyModel.update, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ModelException, MyTinyModel.update, service, **self.INVALID_PARAMS)
                ok_(not rendered4.called)

    def _test_get_or_create(self, service):
        kwargs = {'return_value': (MagicMock(), random.choice([False, True]))}
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.render_to_response', **kwargs) as rendered1:
                MyTinyModel.get_or_create(service, **self.TEST_DEFAULT_PARAMS)
                ok_(rendered1.called)

            with patch('tinymodel.internals.api.render_to_response', **kwargs) as rendered2:
                MyTinyModel.get_or_create(service, **self.VALID_PARAMS)
                ok_(rendered2.called)

        with patch('tinymodel.internals.api.render_to_response', **kwargs) as rendered3:
            assert_raises(ModelException, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response', **kwargs) as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ModelException, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)
                ok_(not rendered4.called)

    def test_get_or_create_natural_service(self):
        self._test_get_or_create(Service(get_or_create=MagicMock()))

    def test_get_or_create_alt_service(self):
        self._test_get_or_create(Service(find=MagicMock(), create=MagicMock()))

    def test_missing_service_function(self):
        service = Service()
        for service_method in ['find', 'create', 'update']:
            api_method = getattr(MyTinyModel, service_method)
            assert_raises(AttributeError, api_method, service, **self.VALID_PARAMS)

    def test_call_with_endpoint_name(self):
        service_methods_kwargs = {
            'find': {'return_value': [MagicMock()] * 3},
            'create': {'return_value': MagicMock()},
            'update': {'return_value': MagicMock()},
            'get_or_create': {'return_value': (MagicMock(), random.choice([False, True]))},
        }
        service_kwargs = dict([(method_name, MagicMock()) for method_name in service_methods_kwargs.keys()])
        service = Service(**service_kwargs)
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.remove_calculated_values'):
                for method_name, kwargs in service_methods_kwargs.iteritems():
                    with patch('tinymodel.internals.api.render_to_response', **kwargs):
                        api_method = getattr(MyTinyModel, method_name)
                        api_method(service, endpoint_name='endpoint_name')
                        service_kwargs[method_name].assert_called_with(endpoint_name='endpoint_name')

    def test_api_methods_response(self):
        service_methods_kwargs = {
            'find': {'kwargs': {'return_value': [MagicMock()] * 3}, 'type': list,},
            'create': {'kwargs': {'return_value': MagicMock()}},
            'update': {'kwargs': {'return_value': MagicMock()}},
            'get_or_create': {'kwargs': {'return_value': (MagicMock(), random.choice([False, True]))}, 'type': tuple},
        }
        service_kwargs = dict([(method_name, MagicMock(**params['kwargs'])) \
            for method_name, params in service_methods_kwargs.iteritems()])
        service = Service(return_type='foreign_model', **service_kwargs)
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.remove_calculated_values'):
                for method_name, params in service_methods_kwargs.iteritems():
                    api_method = getattr(MyTinyModel, method_name)
                    response = api_method(service)
                    if 'type' in params:
                        eq_(type(response), params['type'])
                        eq_(len(response), len(params['kwargs']['return_value']))
                    else:
                        ok_(not isinstance(response, defaults.COLLECTION_TYPES))

    def test_create_or_update(self):
        method = MyTinyModel.create_or_update_by
        find_response = [MagicMock(id=1)]
        find_empty_response = []
        service = MagicMock()

        assert_raises(ValueError, method, service, by=['id'])
        assert_raises(ValueError, method, service, by=[], **{'name': 'test'})
        assert_raises(ValueError, method, service, by=['id'], **{'name': 'test'})

        with patch('tinymodel.internals.api.find', **{'return_value': find_empty_response}):
            with patch('tinymodel.internals.api.create') as c1:
                with patch('tinymodel.internals.api.update') as u1:
                    params = {'name': 'test', 'id': 1}
                    MyTinyModel.create_or_update_by(service, by=['id'], **params)
                    ok_(not u1.called)
                    ok_(c1.called)
                    c1.assert_called_with(MyTinyModel, service, None, **params)

        with patch('tinymodel.internals.api.find', **{'return_value': find_response}):
            with patch('tinymodel.internals.api.create') as c2:
                with patch('tinymodel.internals.api.update') as u2:
                    params = {'name': 'test', 'id': 1}
                    MyTinyModel.create_or_update_by(service, by=['id'], **params)
                    ok_(u2.called)
                    u2.assert_called_with(MyTinyModel, service, None, **params)
                    ok_(not c2.called)
