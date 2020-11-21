import os
import logging

from .notifications import DebugNotifier
from .rules import FileFormatValidator, ValidateSchema
from .rules import ValidationSuite
from .config import S3JsonLoader

import boto3


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


def handle(event, context):
    bucket = os.environ["CONFIG_BUCKET"]
    key = os.environ["CONFIG_KEY"]
    session = boto3.session.Session()
    rules = [
        FileFormatValidator("FileFormatValidator", "File format must end in .csv"),
        ValidateSchema(
            "ValidateSchema",
            "Validate the schema of the file is correct",
            S3JsonLoader(os)   
        )
    ]
    runner = ValidationSuite(rules, DebugNotifier())
    runner.validate(event, session)
