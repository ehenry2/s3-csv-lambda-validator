import boto3
import os
import datetime
from behave import *

@given(u'the "{filename}" file is uploaded to our s3 bucket')
def step_impl(context, filename):
    key_prefix = os.environ["ATDD_KEY_PREFIX"].rstrip("/")
    now = datetime.datetime.now()
    str_now = now.strftime('%Y%m/%d/%H/%M')
    context.atdd_key_prefix = f"{key_prefix}/{str_now}"
    context.session = boto3.session.Session()
    context.atdd_bucket = os.environ["ATDD_BUCKET"]
    context.schema_key = ""
    context.csv_key = context.atdd_key_prefix + "/" + filename
    session = boto3.session.Session()
    client = session.client("s3")
    client.put_object(
        Bucket=context.atdd_bucket,
        Key=context.csv_key,
        Body=b""
    )