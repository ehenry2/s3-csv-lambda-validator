
# S3 CSV Validator Lambda Function

## Introduction
This repo contains code for deploying a lambda function to validate CSV files
as they are created in your S3 bucket. Some features include:


* Column order validation
* Data type validation
* Primary key missing values check
* Wrong delimiter check
* Invalid file names chek


Features from the development perpective include:

* Unit tests
* ATDD tests (Acceptance tests) using the Behave framework
* Documentation on how to deploy the system
* Basic automated deployment using CodeBuild


## Before you begin
You will need at least two S3 buckets in production, one for configuration
and the other where your data resides (which the lambda will be monitoring).

## Setup
This section will walk you through creating what you need to get the lambda function running in your environment. Note that the policies we have you create here mostly follow the principle of least-privilege, but if you know what you're doing, feel free to refine them a bit more.

### Create a custom policy for reading from your s3 buckets
The first step is to create a custom policy to attach to the IAM role you will create in the next step. This will give your lambda function the ability to read from your data and configuration buckets and to write its logs to cloudwatch.

To create this from the AWS console, click on the "Services" tab on the top left, then search for "IAM". Once you
open the IAM page, on the left navigation bar that says "Dashboard", click on "Policies" (under "Access Management").
Click "Create Policy". Choose the "JSON" tab. Now, copy and paste the json below. Replace "my-data-bucket"
and "my-config-bucket" with the name of your data and configuration buckets, respectively.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadAccess",
      "Action": [
        "s3:GetObject"
      ],
      "Effect": "Allow",
      "Resource": [
          "arn:aws:s3:::my-data-bucket/*",
          "arn:aws:s3:::my-config-bucket/*"
      ]
    },
    {
      "Sid": "CloudWatchLogAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SendEmailWithSES",
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

When you're ready, click "Review Policy". Give it a name and summary, then click "Create Policy".


### Create an IAM role for your lambda function
The next step is to create an IAM role for your lambda function and attach the custom policy you created in the last step.

From the IAM dashboard, click on "Roles". Click "Create Role". Under "Select type of trusted entity", choose "AWS service". For "Choose a use case", click on "Lambda". Now, click on "Next: Permissions" to go to the next screen. On the "Attach permission policies" screen, search for the name of the custom policy in the last step. Click the check box next to it, then click "Next: Tags" to go to the next screen. Add any tags, then click "Next: Review". Add a role name and description, then click "Create role"


### Add your new IAM role to your S3 bucket policy.
If you don't have an s3 bucket policy you can skip this step. If you do have an s3 bucket policy, add the statement below to the "Statements" to give your role access. Replace \<your-aws-account-id\> ,\<iam-role-for-s3-access\>, and \<s3-bucket-name\> with the real values. Update the bucket policy for both buckets.

```
{
    "Sid": "AllowS3ValidatorIamRole",
    "Effect": "Allow",
    "Principal": {
        "AWS": "arn:aws:iam::<your-aws-account-id>:role/<iam-role-for-s3-access>"
    },
    "Action": [
        "s3:GetObject",
    ],
    "Resource": "arn:aws:s3:::<s3-bucket-name>/*"
}
```

### Create your lambda function
In this step, we will create the new lambda function
we'll use to run our validation.

In the AWS console under services, search for "Lambda".
On the lambda page, click "Create Function". Choose "Author from scratch".
Under "basic information", enter a function name. For runtime, choose "Python 3.8".
Click the button "Change default execution role". Once it pops out, under "Execution role"
choose "Use and existing role" and then pick the role you created in the second step under "Existing role".
Now click "Create Function".


### Configure your lambda function
Go to your function page. To get there from the lambda dashboard click on 'functions' on the
left and search for your function name. We now need to add some important configuration variables
to make the function work. Click on the "Properties" tab. Under environment variables, add the
following:

* CONFIG_BUCKET -> The name of your configuration bucket. example: "mybucket"
* CONFIG_KEY -> The name of the key (or file path) that points to your schema file. See the section on creating your schema file for more info on creating that file. example: "config/schema.json"
* NOTIFIER_TYPE -> The type of notifier to use. Valid choices are: "debug" (prints results to stdout),
"atdd" (used in ATDD testing, more on that later), and "email" (sends email with csv on validation failure).
If "email" is specified, the additional environment variables "EMAIL_SENDER" and "EMAIL_RECIPIENTS" must be specified as well.
* EMAIL_SENDER -> The email address to send the notification message as. If using SES (default), the address must have
been already verified. Example: "me@example.com"
* EMAIL_RECIPIENTS -> Comma separated list of the email addresses to send the notification message to.
Example: "you@example.com,them@example.com"

After you finish configuring the environment variables, under "Basic Settings", click "Edit". Bump the memory up to the maximum (~3008 MB) and the timeout to 15 minutes, 0 seconds (the maximum). The UI is a bit buggy, so just refresh the page if it won't accept your number. You might have to click the button to increment the minutes instead of typing it in. 
Make sure the execution role is the role you created earlier. Click "save".

Now we need to set the function handler. Under 'runtime settings', click "Edit". Change handler to
"csv_validator.handler.handle".


### Create your schema file
The lambda function requires a schema file specified
as a json to be loaded from an s3 bucket. It can be
tedious to create this json from scratch for a large
number of fields, so we've provided a handle tool to
autogenerate it for you from an existing csv.

First, we need to clone the repo and set up our
development environment.

```
# Clone repo and cd into the directory.
git clone https://github.com/ehenry2/s3-csv-lambda-validator
cd s3-csv-lambda-validator

# Create and activate your virtualenv
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
```

Now we can run our schema generator cli tool. Most options are self explanatory, but "pattern" refers to
a python regular expression (https://docs.python.org/3/library/re.html) that provides a schema for set of objects.
So for example, if you have a "reports" directory and you have various csvs landing there, but they all have
the same schema (e.g. reports/2020-01-01.csv, reports/2020-01-02.csv), you can put "reports/.*csv" to match
those files, or more complicated regex if you prefer. Note: file globs are not the same as python regex.
For example, to match all csv files in reports directory, 'reports/*.csv' would need to be changed to
'reports/.*\\.csv'.

An example of running the tool would be:

```
python3 bin/schema_from_file.py \
    --input-file my.csv \
    --output-file schema.json \
    --delimeter "," \
    --primary-key "id" \
    --pattern "reports/.*csv"
```

You can also add more than one path to a schema file by running the tool again.
If you specify a file that already exists as the "--output-file" parameter,
it will append another path to that file instead of overwriting it.

After you are done, you can upload your schema file to s3 (example is with old version of AWS CLI).

```
aws s3 cp schema.json s3://my-bucket/some/prefix/schema.json
```

Then set your CONFIG_KEY environment variable to the key path (e.g. "some/prefix/schema.json")

## Set up codebuild.
Because this lambda function depends on compiled dependencies specific to system architecture,
it's recommended to use codebuild to upload the code of your lambda function. You might be able
to get away with this if you're running linux + x86_64 arch, but this is relatively simple to configure
and cheap. Builds last around a minute, so cost is minimal (e.g. $.005/min, with some covered under free tier).


In the AWS console, go to 'Services' and search for "CodeBuild". Click on "Build Projects" -> 'Create Build Project'.
Give it a name under 'Project configuration'. Under 'Source', update 'Source provider' to 'Github'. Click 'Connect to github' and put in the info for your github account. It should then update for 'Repository' so you can pick 'Public Repository'. Then put 'https://github.com/ehenry2/s3-csv-lambda-validator' for the repository url. For 'Source version', put 'main'. Under 'Enviroment', choose 'Managed image', 'Operating System' -> 'Ubuntu', 'Runtime' -> 'Standard',
'Image' -> 'aws/codebuild/standard:4.0', 'Image version' -> 'Always use the latest for this runtime',
'Environment' -> 'Linux'. For service role, choose 'New Service Role' and give it a name. Click 'Additional Configuration' and change timeout to 10 minutes and hours to 0. Under 'compute' choose the smallest option (3GB memory). For the 'Buildspec' section, choose "Insert Build commands", then click "Switch to Editor". Copy and paste in the following, replacing the lambda name (e.g. in this example "s3-csv-validation-lambda" with the name of your lambda function.

```
version: 0.2

phases:
  build:
    commands:
       - mkdir builddir && cd builddir && pip3 install -r ../requirements.txt -t . && mkdir csv_validator && cp -R ../csv_validator/*.py csv_validator && zip -r9 code.zip . && aws lambda update-function-code --function-name s3-csv-validation-lambda --zip-file fileb://code.zip
```

Finally, under "logs", enter a name for log group and stream name. Then click "Create build project"


Next, we need to create another custom policy so we can have codebuild update our lambda function.
Go to the IAM console -> "Policies" -> "Create new". Then choose json tab and copy and paste this policy in, replacing
the lambda function with your lambda function name and the account number with your account number.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CodeBuildLambdaUpdate",
            "Effect": "Allow",
            "Action": "lambda:UpdateFunctionCode",
            "Resource": "arn:aws:lambda:us-east-1:<aws account num>:function:<your lambda function name>"
        }
    ]
}
```

Once you've created this policy, attach it to the CodeBuild role you created before.

You can now build your lambda. In the CodeBuild console, click on "Build Projects" -> name of your project, then "Start build". On the next screen the defaults should be fine and it should start building!


### Enable the lambda trigger
Now that your lambda function is ready to go, we will set it upto trigger your lambda to run every time an object is created in your bucket.
Go to your function page. In the "designer" section of the lambda page, click "Add trigger".
Under "Trigger configuration", pick "S3". Choose your data bucket for "bucket". For "event type", pick "PUT".
For prefix, put one of the paths you want to monitor with the lambda. You can create multiple s3 triggers for different
paths. It's recommended to do this instead of having one for the whole bucket.
Acknowledge the "Recursive Invocation", then click "Add".

Now you can upload an object and see it execute in cloudwatch (and/or receive email notifications if something went wrong).