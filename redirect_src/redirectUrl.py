import boto3
import json


def get_data_ddb(short_url):
    ddb_client = boto3.client('dynamodb', region_name='ap-northeast-2')
    res = ddb_client.query(
        TableName='dev-url-shortener',
        KeyConditionExpression='id = :id',
        ExpressionAttributeValues={
            ':id': {'S': short_url}
        }
    )
    if res['Items']:
        print(f"ddb res: {res['Items'][0].get('long_url', '').get('S', '')}")
        return res['Items'][0].get('long_url', '').get('S', '')
    else:
        return ''


def handler(event, context):
    print(f"Receive event: {event.get('pathParameters').get('id')}")
    long_url = get_data_ddb(event.get('pathParameters').get('id'))
    if long_url:
        print(f"Original URL: {long_url}")
        resp = {
            "statusCode": 302,
            "headers": {"Location": long_url},
            "body": "..."
        }
    else:
        resp = {
            "statusCode": 404,
            "headers": {"error": "no url found"},
            "body": "..."
        }
    return resp
