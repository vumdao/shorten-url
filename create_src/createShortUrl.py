import boto3
import random
import string
import datetime
import json


def create_short_url(long_url):
    ddb_client = boto3.client('dynamodb', region_name='ap-northeast-2')
    shorten_str = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    short_url = f'https://s.cloudopz.co/{shorten_str}'
    expire_date = datetime.datetime.now() + datetime.timedelta(days=7)
    ddb_client.put_item(
        TableName='dev-url-shortener',
        Item={
            'id': {"S": shorten_str},
            'long_url': {"S": long_url},
            'short_url': {"S": short_url},
            'expiry_date': {"N": str(int(datetime.datetime.timestamp(expire_date)))}
        }
    )
    return short_url


def handler(event, context):
    data = json.loads(event.get("body"))
    url = data.get('url', '')
    short_url = create_short_url(url)
    resp = {
        "statusCode": 200,
        "body": json.dumps(f'{{"short_url": "{short_url}"}}')
    }
    return resp
