class RestfulException(Exception):
    pass


class ItemNotFound(RestfulException):
    pass


class RequestMustBeJSON(RestfulException):
    pass


class BackendConflict(RestfulException):
    pass


class InvalidJSON(RestfulException):
    pass
