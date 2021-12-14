import json
import typing as t
from urllib import parse

from lesoon_restful.exceptions import InvalidJSON

if t.TYPE_CHECKING:
    from lesoon_restful.manager import Manager


class AttributeDict(dict):

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class ManagerProxy:

    def __init__(self, manager: 'Manager' = None):
        self._manager = manager

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, value):
        self._manager = value
        self.__dir__ = self._manager.__dir__
        self.__dict__ = self._manager.__dict__

    def __getattr__(self, item):
        return self._manager.__getattribute__(item)


def convert_dict(param: str = None) -> t.Dict[str, t.Any]:
    if param:
        try:
            # 特殊字符转义处理
            where = parse.unquote(param)
            _where = json.loads(where)
            if not isinstance(_where, dict):
                return dict()
            else:
                return _where
        except (json.JSONDecodeError, TypeError):
            raise InvalidJSON(f'参数无法序列化 {param}')

    else:
        return dict()
