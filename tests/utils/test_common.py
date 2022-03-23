import pytest

from lesoon_restful.utils.base import AttributeDict
from lesoon_restful.utils.base import convert_dict


class TestCommon:

    def test_AttributeDict(self):
        attr = AttributeDict({'a': 1})
        assert attr.a == 1

        with pytest.raises(KeyError):
            c = attr.b

    def test_convert_dict(self):
        param = '{"id":1}'
        assert convert_dict(param) == {'id': 1}

        param = ''
        assert convert_dict(param) == {}

        param = '%7B%22a%22%3A%20%7B%22%24eq%22%3A%201%7D%7D'
        assert convert_dict(param) == {'a': {'$eq': 1}}

        param = 'orderNo asc'
        assert convert_dict(param, silent=True) == param
