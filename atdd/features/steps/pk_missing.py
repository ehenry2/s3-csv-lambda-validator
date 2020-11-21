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
    print(results)
    for result in results:
        print(result)
        if result[1] == check_name:
            if result[0] != "FAILED":
                raise Exception(f"Check {check_name} did not fail as required: {result}")
            print(result)
    raise Exception
