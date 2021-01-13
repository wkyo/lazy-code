"""Provide convenient serialization functions and decorators for Marshallow

Supported:
- marshal_with, a decorator for marshal
- marshal
"""
from functools import wraps
from http import HTTPStatus


def unpack(response, default_code=HTTPStatus.OK):
    """
    Unpack a Flask standard response.

    A copy from `flask-restx`

    Flask response can be:
    - a single value
    - a 2-tuple ``(value, code)``
    - a 3-tuple ``(value, code, headers)``

    .. warning::

        When using this function, you must ensure that the tuple is not the response data.
        To do so, prefer returning list instead of tuple for listings.

    :param response: A Flask style response
    :param int default_code: The HTTP code to use as default if none is provided
    :return: a 3-tuple ``(data, code, headers)``
    :rtype: tuple
    :raise ValueError: if the response does not have one of the expected format
    """
    if not isinstance(response, tuple):
        # data only
        return response, default_code, {}
    elif len(response) == 1:
        # data only as tuple
        return response[0], default_code, {}
    elif len(response) == 2:
        # data and code
        data, code = response
        return data, code, {}
    elif len(response) == 3:
        # data, code and headers
        data, code, headers = response
        return data, code or default_code, headers
    else:
        raise ValueError("Too many response values")


def marshal(data, schema_inst, many=None, envolope=None):
    data = schema_inst.dump(data, many=many).data
    if envolope:
        data = {envolope: data}
    return data


def marshal_with(schema_inst, many=None, envolope=None):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resp = func(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                data = schema_inst.dump(resp, many=many)
                if envolope:
                    data = {envolope: data}
                return (
                    marshal(
                        data,
                        schema_inst,
                        many=many,
                        envolope=envolope
                    ),
                    code,
                    headers
                )
            else:
                return marshal(
                    resp,
                    schema_inst,
                    many=many,
                    envolope=envolope
                )
        return wrapper

    return decorator
