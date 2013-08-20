import json
from unittest import TestCase
from mock import patch, MagicMock
from nose.tools import assert_raises, ok_
from tinymodel import TinyModel, FieldDef, api
from tinymodel.service import Service
from tinymodel.utils import ValidationError


class MyTinyModel(TinyModel):
    FIELD_DEFS = [
        FieldDef('my_int', allowed_types=[int]),
        FieldDef('my_str', allowed_types=[str]),
        FieldDef('my_bool', allowed_types=[bool]),
        FieldDef('my_fk', allowed_types=["test.api_test.MyOtherModel"], relationship='has_one'),
        FieldDef('my_m2m', allowed_types=[["test.api_test.MyOtherModel"]], relationship='has_many'),
    ]


class MyOtherModel(TinyModel):
    FIELD_DEFS = [FieldDef('my_float', allowed_types=[float])]


class MyForeignModel(object):
    def __init__(self, *args, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.iteritems()]


class APiTest(TestCase):
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

    def test_match_names_and_values(self):
        service = Service(return_type='json', find=MagicMock())
        valid_params = {'my_str': 'str', 'my_int': 1, 'my_bool': True,
                        'my_fk': MyOtherModel(), 'my_m2m': [MyOtherModel()],
                        'my_fk_id': 1, 'my_fk_id': 1L, 'my_fk_id': '1', 'my_fk_id': u'1',
                        'my_m2m_ids': [1, 2], 'my_m2m_ids': [1L, 2L], 'my_m2m_ids': ['1', '2'],
                        'my_m2m_ids': [u'1', u'2']}
        invalid_names = ['my_other', 'my_fk_ids', 'my_m2m_id']
        invalid_params = {'my_str': 1, 'my_fk': MyForeignModel(), 'my_fk_id': 'foo',
                          'my_m2m': [MyForeignModel()], 'my_m2m_ids': ['foo', u'bar']}
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
            with patch('tinymodel.internals.api.render_to_response') as renderer2:
                for k, v in invalid_params.iteritems():
                    assert_raises(ValidationError, MyTinyModel.find, service, **{k: v})
                    ok_(not renderer2.called)
