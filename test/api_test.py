from datetime import datetime
import json
from unittest import TestCase
from mock import patch, MagicMock
from nose.tools import assert_raises, ok_
from tinymodel import TinyModel, FieldDef, api
from tinymodel.service import Service
from tinymodel.utils import ValidationError


class MyTinyModel(TinyModel):
    def __default(self):
        return True

    FIELD_DEFS = [
        FieldDef('my_int', allowed_types=[int]),
        FieldDef('my_str', allowed_types=[str]),
        FieldDef('my_bool', allowed_types=[bool]),
        FieldDef('my_fk', allowed_types=["test.api_test.MyOtherModel"], relationship='has_one'),
        FieldDef('my_m2m', allowed_types=[["test.api_test.MyOtherModel"]], relationship='has_many'),
        FieldDef('my_default_value', allowed_types=[bool], default=__default),
        FieldDef('my_datetime', allowed_types=[datetime]),
        FieldDef('my_float', allowed_types=[float]),
        FieldDef('my_id', allowed_types=[str, unicode]),
    ]


class MyOtherModel(TinyModel):
    FIELD_DEFS = [FieldDef('my_float', allowed_types=[float])]


class MyForeignModel(object):
    def __init__(self, *args, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.iteritems()]


class APiTest(TestCase):
    TEST_DEFAULT_PARAMS = {'my_str': 'str', 'my_int': 1, 'my_bool': True, 'my_default_value': False}
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

        # test return_type=json
        response = api.render_to_response(MyTinyModel, json_response, return_type='json')
        ok_(isinstance(response, MyTinyModel))
        response = api.render_to_response(MyTinyModel, [json_response], return_type='json')
        ok_(isinstance(response, list))
        [ok_(isinstance(o, MyTinyModel)) for o in response]
        assert_raises(TypeError, api.render_to_response, MyTinyModel, foreign_response, return_type='json')
        assert_raises(TypeError, api.render_to_response, MyTinyModel, tinymodel_response, return_type='json')
        # test return_type=tinymodel
        response = api.render_to_response(MyTinyModel, tinymodel_response, return_type='tinymodel')
        ok_(isinstance(response, MyTinyModel))
        response = api.render_to_response(MyTinyModel, [tinymodel_response], return_type='tinymodel')
        ok_(isinstance(response, list))
        [ok_(isinstance(o, MyTinyModel)) for o in response]
        assert_raises(TypeError, api.render_to_response, MyTinyModel, json_response, return_type='tinymodel')
        assert_raises(TypeError, api.render_to_response, MyTinyModel, foreign_response, return_type='tinymodel')
        # test return_type=foreign_model
        response = api.render_to_response(MyTinyModel, foreign_response, return_type='foreign_model')
        ok_(isinstance(response, MyTinyModel))
        response = api.render_to_response(MyTinyModel, [foreign_response], return_type='foreign_model')
        ok_(isinstance(response, list))
        [ok_(isinstance(o, MyTinyModel)) for o in response]
        assert_raises(TypeError, api.render_to_response, MyTinyModel, json_response, return_type='foreign_model')
        assert_raises(TypeError, api.render_to_response, MyTinyModel, tinymodel_response, return_type='foreign_model')

    def test_find_and_match_names_and_values(self):
        service = Service(find=MagicMock())
        valid_params = self.VALID_PARAMS.copy()
        valid_params.update({'my_fk': MyOtherModel(), 'my_m2m': [MyOtherModel()],
                             'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                             'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                             'my_m2m_ids': [u'1', u'2']})
        invalid_params = self.INVALID_PARAMS.copy()
        invalid_params.pop('foo', None)
        invalid_names = ['my_other', 'my_fk_ids', 'my_m2m_id']

        with patch('tinymodel.internals.api.render_to_response'):
            with patch('tinymodel.internals.api.match_field_values') as match_values1:
                for key in valid_params.keys():
                    MyTinyModel.find(service, **{key: 'foo'})
                    ok_(match_values1.called)
            with patch('tinymodel.internals.api.match_field_values') as match_values2:
                for key in invalid_names:
                    assert_raises(ValidationError, MyTinyModel.find, service, **{key: 'foo'})
                    ok_(not match_values2.called)

        with patch('tinymodel.internals.api.match_model_names'):
            with patch('tinymodel.internals.api.render_to_response') as renderer1:
                for k, v in valid_params.iteritems():
                    MyTinyModel.find(service, **{k: v})
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
            assert_raises(ValidationError, MyTinyModel.create, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ValidationError, MyTinyModel.create, service, **self.INVALID_PARAMS)
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
            assert_raises(ValidationError, MyTinyModel.update, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ValidationError, MyTinyModel.update, service, **self.INVALID_PARAMS)
                ok_(not rendered4.called)

    def _test_get_or_create(self, service):
        with patch('tinymodel.internals.api.match_field_values'):
            with patch('tinymodel.internals.api.render_to_response') as rendered1:
                MyTinyModel.get_or_create(service, **self.TEST_DEFAULT_PARAMS)
                ok_(rendered1.called)

            with patch('tinymodel.internals.api.render_to_response') as rendered2:
                MyTinyModel.get_or_create(service, **self.VALID_PARAMS)
                ok_(rendered2.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered3:
            assert_raises(ValidationError, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)
            ok_(not rendered3.called)

        with patch('tinymodel.internals.api.render_to_response') as rendered4:
            with patch('tinymodel.internals.api.match_field_values'):
                assert_raises(ValidationError, MyTinyModel.get_or_create, service, **self.INVALID_PARAMS)
                ok_(not rendered4.called)

    def test_get_or_create_intuitive_service(self):
        self._test_get_or_create(Service(get_or_create=MagicMock()))

    def test_get_or_create_alt_service(self):
        self._test_get_or_create(Service(find=MagicMock(), create=MagicMock()))

    def test_missing_service_function(self):
        service = Service()
        for service_method in ['find', 'create', 'update']:
            api_method = getattr(MyTinyModel, service_method)
            assert_raises(AttributeError, api_method, service, **self.VALID_PARAMS)

    def test_call_with_endpoint_name(self):
        service_method_names = ['find', 'create', 'update', 'get_or_create']
        service_kwargs = {name: MagicMock() for name in service_method_names}
        service = Service(**service_kwargs)
        with patch('tinymodel.internals.api.render_to_response'):
            with patch('tinymodel.internals.api.match_field_values'):
                with patch('tinymodel.internals.api.match_model_names'):
                    with patch('tinymodel.internals.api.remove_default_values'):
                        for name in service_method_names:
                            service_method = getattr(MyTinyModel, name)
                            service_method(service, endpoint_name='endpoint_name')
                            service_kwargs[name].assert_called_with(endpoint_name='endpoint_name')
