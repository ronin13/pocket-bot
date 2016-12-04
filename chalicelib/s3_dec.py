from __future__ import unicode_literals
from chalicelib import constants
import json
import boto3
import functools


def s3_load(func):
    @functools.wraps(func)
    def internal(*args, **kwargs):
        s3 = boto3.client('s3')
        config_data = json.loads(s3.get_object(Bucket=constants.BUCKET, Key=constants.CONFIG_KEY)['Body'].read())
        kwargs['config_data'] = config_data
        (response, config_data) =  func(*args, **kwargs)
        s3.put_object(Bucket=constants.BUCKET, Body=json.dumps(config_data), Key=constants.CONFIG_KEY)
        return response
    return internal
