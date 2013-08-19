from unittest import TestCase

from nose.tools import assert_raises, eq_

from tinymodel.service import Service
from tinymodel.utils import ValidationError

find = create = update = delete = lambda x: x
services = {'find': find, 'update': update, 'create': create, 'delete': delete}
invalid_services = {'find': 'find', 'delete': delete, 'update': update}


class ServiceTest(TestCase):
    def test_return_type(self):
        assert_raises(ValidationError, Service, 'foo', **services)
        eq_(Service(**services).return_type, 'json')
        eq_(Service(return_type='tinymodel', **services).return_type, 'tinymodel')
        eq_(Service(return_type='foreign_model', **services).return_type, 'foreign_model')
        eq_(Service(return_type='json', **services).return_type, 'json')

    def test_services(self):
        assert_raises(ValidationError, Service, **invalid_services)
        service = Service(**services)
        eq_(find, service.find)
        eq_(create, service.create)
        eq_(update, service.update)
        eq_(delete, service.delete)
