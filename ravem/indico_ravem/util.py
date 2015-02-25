import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import HTTPError
from urlparse import urljoin

from indico_ravem.plugin import RavemPlugin


def ravem_api_call(api_endpoint, method='GET', **kwargs):
    """Emits a call to the given RAVEM API endpoint.

    This function is meant to be used to easily generate calls to the RAVEM API.
    The RAVEM URL, username and password are automatically fetched from the
    settings of the RAVEM plugin each time.

    :param api_endpoint: str -- The RAVEM API endpoint to call.
    :param \*\*kwargs: The field names and values used for the RAVEM API as
    strings

    :returns: :class: requests.models.Response -- The response from the RAVEM
    API usually as a JSON (with an `error` message if the call failed.)
    """
    if method.upper() == 'GET':
        request = requests.get
    elif method.upper() == 'POST':
        request = requests.post
    else:
        raise ValueError('Unsupported HTTP method {method}, must be GET or POST'.format(method=method))

    root_endpoint = RavemPlugin.settings.get('api_endpoint')
    username = RavemPlugin.settings.get('username')
    password = RavemPlugin.settings.get('password')
    headers = {'Accept': 'application/json'}

    try:
        response = request(urljoin(root_endpoint, api_endpoint), auth=HTTPDigestAuth(username, password), params=kwargs,
                           verify=False, headers=headers)
        print response.request.url
    except Exception as error:
        RavemPlugin.logger.exception(
            "failed call: {method} {api_endpoint} with {params}: {error.message}"
            .format(method=method.upper(), api_endpoint=api_endpoint, params=kwargs, error=error)
        )
        raise

    try:
        response.raise_for_status()
    except HTTPError as error:
        RavemPlugin.logger.exception("{response.request.method} {response.url} failed with {error.message}"
                                     .format(response=response, error=error))
        raise

    json_response = response.json()
    if 'error' not in json_response and 'result' not in json_response:
        err_msg = ("{response.request.method} {response.url} returned a json without a result or error: "
                   "{json_response}").format(response=response, json_response=json_response)
        RavemPlugin.logger.exception(err_msg)
        raise RavemAPIException(err_msg, api_endpoint, response)

    return json_response


def get_room_endpoint(endpoints):
    if endpoints['vc_endpoint_legacy_ip']:
        return '{prefix}{endpoints[vc_endpoint_legacy_ip]}'.format(prefix=RavemPlugin.settings.get('prefix'),
                                                                endpoints=endpoints)
    else:
        return endpoints['vc_endpoint_vidyo_username']


class RavemException(Exception):
    pass


class RavemOperationException(RavemException):
    def __init__(self, message, reason):
        super(RavemOperationException, self).__init__(message)
        self.message = message
        self.reason = reason


class RavemAPIException(RavemException):
    def __init__(self, message, endpoint, response):
        super(RavemAPIException, self).__init__(message)
        self.message = message
        self.endpoint = endpoint
        self.response = response