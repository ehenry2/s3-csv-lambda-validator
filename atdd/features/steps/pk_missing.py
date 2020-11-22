from behave import *
import json


@then(u'the "{check_name}" check should fail')
def step_impl(context, check_name):
    client = context.session.client('s3')
    response = client.get_object(
        Bucket=context.atdd_bucket,
        Key=context.atdd_report_key
    )
    results = json.loads(response["Body"].read())
    for result in results:
        if result[1] == check_name:
            if result[0] != "FAILED":
                raise Exception(f"Check {check_name} did not fail as required: {result}")
            else:
                return
        print(result)
    raise Exception(f"Could not find a result that matches {check_name}")
