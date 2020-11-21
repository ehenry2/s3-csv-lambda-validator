import os
import logging

from .notifications import CsvEmailNotifier, DebugNotifier, AtddNotifier
from .rules import FileFormatValidator, ValidateSchema
from .rules import ValidationSuite
from .config import S3JsonLoader

import boto3


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


def handle(event, context):
    schema_bucket = os.environ["CONFIG_BUCKET"]
    schema_key = os.environ["CONFIG_KEY"]
    session = boto3.session.Session()
    notifier_type = os.environ.get("NOTIFIER_TYPE", "debug")
    notifier = None
    if notifier_type.lower() == "debug":
        notifier = DebugNotifier()
    elif notifier_type.lower() == "atdd":
        bucket = os.environ["ATDD_BUCKET"]
        key = event["Extras"]["atdd_key"]
        notifier = AtddNotifier(bucket, key, session)
    elif notifier_type.lower() == "email":
        sender = os.environ["EMAIL_SENDER"]
        recipients = os.environ["EMAIL_RECIPIENTS"]
        notifier = CsvEmailNotifier(sender, recipients, session)
    rules = [
        FileFormatValidator("FileFormatValidator", "File format must end in .csv"),
        ValidateSchema(
            "ValidateSchema",
            "Validate the schema of the file is correct",
            S3JsonLoader(schema_bucket, schema_key)
        )
    ]
    runner = ValidationSuite(rules, notifier)
    runner.validate(event, session)
