# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pprint

import requests
from chalice import BadRequestError
from chalice import Chalice

from chalicelib import auth
from chalicelib import constants
from chalicelib import fb
from chalicelib import utils
from chalicelib.s3_dec import s3_load

app = Chalice(app_name='pocket_bot')
app.debug = True

# S3 buckets have server-side-encryption enabled.
config_data = {}
config_data['user'] = {}
config_data['pocket'] = {}
config_data['keys'] = {}


@app.route('/hello/{sender}', methods=['GET'])
@s3_load
def hello_point(sender, **kwargs):
    config_data.update(kwargs['config_data'])
    fb_token = config_data['keys']['fb_access_token']
    consumer_key = config_data['keys']['pocket_consumer_key']
    code = config_data['user'][sender]['code']

    pocket_token = auth.oauth_auth(code, consumer_key)
    config_data['user'][sender] = {'code': code, 'pocket_token': pocket_token}
    fb.fb_send(sender, 'Authenticated successfully', fb_token)

    return ('Hello, follow the bot', config_data)


# A dummy to avoid 404 on favicon.ico
@app.route('/favicon.ico', methods=['GET'])
def favicon_request():
    return 'ABCD'


@app.route('/botook', methods=['GET', 'POST'])
@s3_load
def bot_point(**kwargs):
    config_data.update(kwargs['config_data'])
    verify_key = config_data['keys']['fb_verify_key']
    fb_token = config_data['keys']['fb_access_token']
    consumer_key = config_data['keys']['pocket_consumer_key']

    if app.current_request.method == 'GET':
        vtoken = app.current_request.query_params['hub.verify_token']
        mode = app.current_request.query_params['hub.mode']
        if mode == 'subscribe':
            if vtoken == verify_key:
                return (app.current_request.query_params['hub.challenge'], config_data)
            else:
                raise BadRequestError('Invalid token')
        else:
            return ('Hello', config_data)

    else:
        body = app.current_request.json_body
        if body['object'] == "page":
            for entry in body["entry"]:
                for messaging_event in entry["messaging"]:

                    if messaging_event.get("message"):

                        sender = str(messaging_event["sender"]["id"])

                        try:
                            message_text = messaging_event["message"]["text"]
                        except KeyError:
                            message_text = None

                        pprint.pprint(config_data)
                        pprint.pprint(messaging_event)

                        try:
                            if not message_text:
                                if messaging_event["message"]["attachments"][0]['payload'] is None:
                                    message_text = messaging_event[
                                        "message"]["attachments"][0]['url']
                                else:
                                    message_text = messaging_event["message"][
                                        "attachments"][0]['payload']['url']
                        except (TypeError, KeyError):
                            fb.fb_send(sender, "Invalid input", fb_token)
                            return ('', config_data)

                        if sender not in config_data['user'] or 'pocket_token' not in config_data['user'][sender] or message_text == 'auth':
                            fb.fb_send(sender, "Greetings, visitor", fb_token)
                            fb.fb_send(
                                sender, "Need to authenticate first!", fb_token)
                            (url, code) = auth.user_auth(sender, consumer_key,
                                                         get_redirect_uri('/hello/' + str(sender)))
                            fb.fb_send(sender, "Click on this " + url +
                                       " for authorizing with Pocket", fb_token)
                            config_data['user'][sender] = {'code': code}
                            return ('', config_data)
                        elif message_text.startswith('http'):

                            pocket_token = config_data[
                                'user'][sender]['pocket_token']

                            r = requests.post(constants.POCKET_ADD_URL, data=json.dumps({
                                'consumer_key': consumer_key,
                                'access_token': pocket_token,
                                'url': message_text,
                            }), headers=utils.get_headers())
                            if r.status_code != 200:
                                fb.fb_send(
                                    sender, "Invalid input or addition failed", fb_token)
                                return ('', config_data)

                            fb.fb_send(
                                sender, "URL added successfully", fb_token)
                            return ('', config_data)
                        else:
                            fb.fb_send(sender, "Unknown verb or url", fb_token)
                            return ('', config_data)


def get_redirect_uri(new_path):
    proto = app.current_request.headers['x-forwarded-proto']
    if 'localhost' in app.current_request.headers['host']:
        return 'http://' + app.current_request.headers['host'] + new_path
    else:
        return proto + '://' + app.current_request.headers['host'] + '/dev' + new_path
