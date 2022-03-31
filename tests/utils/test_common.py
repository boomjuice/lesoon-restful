import pytest

from lesoon_restful.utils.base import AttributeDict


class TestCommon:

    def test_AttributeDict(self):
        attr = AttributeDict({'a': 1})
        assert attr.a == 1

        with pytest.raises(KeyError):
            c = attr.b
