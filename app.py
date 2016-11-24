from __future__ import unicode_literals
from chalice import Chalice, BadRequestError
from chalicelib import constants
from chalicelib import fb
from chalicelib import utils
from chalicelib import auth
import logging
import requests
import json
import boto3
import botocore
import pprint

app = Chalice(app_name='pocket-bot')
app.debug = True

s3 = boto3.client('s3')
config_data = {}
config_data['user'] = {}
config_data['pocket'] = {}
config_data['keys'] = {}

try:
    config_data['user'] = json.loads(s3.get_object(Bucket=constants.BUCKET, Key=constants.CONFIG_KEY)['Body'].read())['user']
    config_data['pocket'] = json.loads(s3.get_object(Bucket=constants.BUCKET, Key=constants.CONFIG_KEY)['Body'].read())['pocket']
except KeyError:
    pass
except botocore.exceptions.ClientError:
    pass

logging.basicConfig(level=logging.INFO)

# config_data['keys'] is 'bootstrapped' into the s3 bucket.
config_data['keys'] = json.loads(s3.get_object(Bucket=constants.BUCKET, Key=constants.CONFIG_KEY)['Body'].read())['keys']
consumer_key = config_data['keys']['pocket_consumer_key']
verify_key = config_data['keys']['fb_verify_key']
fb_token = config_data['keys']['fb_access_token']

@app.route('/hello/{sender}', methods=['GET'])
def hello_point(sender):
    code = config_data['user'][sender]['code']
    pocket_token = auth.oauth_auth(code, consumer_key)
    config_data['user'][sender] = {'code': code, 'pocket_token': pocket_token}
    s3.put_object(Bucket=constants.BUCKET, Body=json.dumps(config_data), Key=constants.CONFIG_KEY)
    fb.fb_send(sender, 'Authenticated successfully', fb_token)
    return 'Hello, follow the bot'


@app.route('/favicon.ico', methods=['GET'])
def favicon_request():
    return 'ABCD'



@app.route('/botook', methods=['GET', 'POST'])
def bot_point():
    if app.current_request.method == 'GET':
        vtoken = app.current_request.query_params['hub.verify_token']
        mode = app.current_request.query_params['hub.mode']
        if mode == 'subscribe':
            if vtoken == verify_key:
                return '{0}'.format(app.current_request.query_params['hub.challenge'])
            else:
                raise BadRequestError('Invalid token')
        else:
            return 'Hello'

    else:
        body = app.current_request.json_body
        if body['object'] == "page":
            for entry in body["entry"]:
                for messaging_event in entry["messaging"]:

                    if messaging_event.get("message"):

                        sender = str(messaging_event["sender"]["id"])
                        fb.fb_send(sender, "Greetings, visitor", fb_token)

                        try:
                            message_text = messaging_event["message"]["text"]
                        except KeyError:
                            message_text = None

                        pprint.pprint(config_data)
                        pprint.pprint(messaging_event)

                        try:
                            if not message_text:
                                if messaging_event["message"]["attachments"][0]['payload'] is None:
                                    message_text = messaging_event["message"]["attachments"][0]['url']
                                else:
                                    message_text = messaging_event["message"]["attachments"][0]['payload']['url']
                        except (TypeError, KeyError):
                            fb.fb_send(sender, "Invalid input", fb_token)
                            return


                        if sender not in config_data['user'] or 'pocket_token' not in config_data['user'][sender] or message_text == 'auth':
                           fb.fb_send(sender, "Need to authenticate first!", fb_token)
                           (url, code) = auth.user_auth(sender, consumer_key, get_redirect_uri('/hello/'+str(sender)))
                           fb.fb_send(sender, "Click on this " + url + " for authorizing with Pocket", fb_token)
                           config_data['user'][sender] = {'code': code}
                        else:

                            pocket_token = config_data['user'][sender]['pocket_token']

                            r = requests.post(constants.POCKET_ADD_URL, data=json.dumps({
                                'consumer_key': consumer_key,
                                'access_token': pocket_token,
                                'url': message_text,
                                }), headers=utils.get_headers())
                            if r.status_code != 200:
                                fb.fb_send(sender, "Invalid input or addition failed", fb_token)
                                return


                            fb.fb_send(sender, message_text + " added successfully", fb_token)


    s3.put_object(Bucket=constants.BUCKET, Body=json.dumps(config_data), Key=constants.CONFIG_KEY)





def get_redirect_uri(new_path):
    proto = app.current_request.headers['x-forwarded-proto']
    if 'localhost' in app.current_request.headers['host']:
        return 'http://' + app.current_request.headers['host'] + new_path
    else:
        return proto + '://' + app.current_request.headers['host'] + '/dev' + new_path


