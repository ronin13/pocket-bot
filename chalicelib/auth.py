# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import requests
from chalice import BadRequestError

from chalicelib import constants
from chalicelib import utils


def user_auth(sender, consumer_key, redirect_uri):

    r = requests.post(constants.POCKET_REQUEST_URL, data=json.dumps({
        'consumer_key': consumer_key,
        'redirect_uri': redirect_uri,
    }), headers=utils.get_headers())
    if r.status_code != 200:
        raise BadRequestError('Request token failed')

    code = r.json()['code']

    url = constants.POCKET_AUTHORIZE_URL.format(code, redirect_uri)
    return (url, code)


def oauth_auth(code, consumer_key):
    r = requests.post(constants.POCKET_OAUTH_URL, data=json.dumps({
        'consumer_key': consumer_key,
        'code': code,
    }), headers=utils.get_headers())
    if r.status_code != 200:
        raise BadRequestError('Oauth authorization failed')

    return r.json()['access_token']
