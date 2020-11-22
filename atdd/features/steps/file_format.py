import boto3
import os
import datetime
import json

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


@given(u'the schema is uploaded with correct path information')
def step_impl(context):
    context.schema_key = f"{context.atdd_key_prefix}/bad_file_name.json"
    here = os.path.dirname(os.path.realpath(__file__))
    schemafile = os.path.join(here, "fixtures/bad_file_name/bad_file_name.json")
    with open(schemafile, 'rb') as f:
        content = f.read()
    schema = json.loads(content)
    schema["paths"][0]["pattern"] = f"{context.atdd_key_prefix}/file.*\\.txt"
    client = context.session.client("s3")
    client.put_object(
        Bucket=context.atdd_bucket,
        Key=context.schema_key,
        Body=json.dumps(schema)
    )