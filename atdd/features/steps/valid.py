import datetime
import os
import json


from behave import *
import boto3


@given(u'the "{fixture_name}" csv is uploaded to our s3 bucket')
def step_impl(context, fixture_name):
    key_prefix = os.environ["ATDD_KEY_PREFIX"].rstrip("/")
    now = datetime.datetime.now()
    str_now = now.strftime('%Y%m/%d/%H/%M')
    context.atdd_key_prefix = f"{key_prefix}/{str_now}"
    context.session = boto3.session.Session()
    context.atdd_bucket = os.environ["ATDD_BUCKET"]
    context.csv_key = context.atdd_key_prefix + f"/{fixture_name}.csv"
    cwd = os.path.dirname(os.path.realpath(__file__))
    context.fixture_dir = os.path.join(cwd, "fixtures", fixture_name)
    csvfile = os.path.join(context.fixture_dir, f"{fixture_name}.csv")
    with open(csvfile, 'rb') as f:
        content = f.read()
    client = context.session.client("s3")
    client.put_object(
        Bucket=context.atdd_bucket,
        Key=context.csv_key,
        Body=content
    )


@given(u'the "{fixture_name}" schema is uploaded to our s3 bucket')
def step_impl(context, fixture_name):
    context.schema_key = context.atdd_key_prefix + f"/{fixture_name}.json"
    schemafile = os.path.join(context.fixture_dir, f"{fixture_name}.json")
    with open(schemafile, 'rb') as f:
        content = f.read()
    schema = json.loads(content)
    schema["paths"][0]["pattern"] = f"{context.atdd_key_prefix}/.*csv"
    client = context.session.client("s3")
    client.put_object(
        Bucket=context.atdd_bucket,
        Key=context.schema_key,
        Body=json.dumps(schema)
    )


@when(u'the csv validator is triggered locally')
def step_impl(context):
    from csv_validator.handler import handle
    os.environ["NOTIFIER_TYPE"] = "atdd"
    os.environ["CONFIG_BUCKET"] = context.atdd_bucket
    os.environ["CONFIG_KEY"] = context.schema_key
    context.atdd_report_key = context.atdd_key_prefix + '/report.json'
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": context.atdd_bucket
                    },
                    "object": {
                        "key": context.csv_key
                    }
                }
            }
        ],
        "Extras": {
            "atdd_key": context.atdd_report_key
        }
    }
    handle(event, None)


@then(u'all checks should pass successfully')
def step_impl(context):
    client = context.session.client('s3')
    response = client.get_object(
        Bucket=context.atdd_bucket,
        Key=context.atdd_report_key
    )
    results = json.loads(response["Body"].read())
    for result in results:
        if result[0] != "SUCCESS":
            raise Exception(f"Result of invocation not successful: {result}")


@when(u'the csv validator lambda function is triggered')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the csv validator lambda function is triggered')