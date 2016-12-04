# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import requests
from chalice import BadRequestError

from chalicelib import constants
from chalicelib import utils


def fb_send(receiver, message, fb_token):

    params = {"access_token": fb_token}
    message_text = message[:310]

    data = json.dumps({
        "recipient": {
            "id": receiver
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post(constants.FBOOK_GRAPH_URL, params=params,
                      headers=utils.get_headers(), data=data)
    if r.status_code != 200:
        raise BadRequestError('Facebook message send failed')
