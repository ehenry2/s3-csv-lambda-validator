import unittest.mock as mock

from csv_validator.rules import FileFormatValidator, Rule, SUCCESS, ValidateSchema, ValidationSuite
from csv_validator.rules import NoMatchingSchemaException

import pyarrow.lib
import pytest


class MockRuleFailure(Rule):
    def __init__(self, name, description, reason):
        super().__init__(name, description)
        self.reason = reason
        self.calls = None
    
    def called_with(self):
        return self.calls

    def validate(self, session, event):
        """
        Run the business logic of the rule.

        :param session: Boto3 session
        :type  session: Boto3 session

        :param event: Event passed to the lambda
        :type  event: dict
        """
        self.fail(self.reason)
        self.calls = (session, event)


class MockRuleOk(Rule):

    def __init__(self, name, description):
        super().__init__(name, description)
        self.calls = None

    def called_with(self):
        return self.calls

    def validate(self, session, event):
        """
        Run the business logic of the rule.

        :param session: Boto3 session
        :type  session: Boto3 session

        :param event: Event passed to the lambda
        :type  event: dict
        """
        self.status = SUCCESS
        self.calls = (session, event)


def test_validation_suite():
    r1 = MockRuleOk("r1", 'first rule')
    r2 = MockRuleFailure("r2", 'secondrule', 'epic fail')
    rules = [r1, r2]
    expected_results = [
        ("SUCCESS", "r1", 'first rule', ''),
        ("FAILED", "r2", 'secondrule', 'epic fail')
    ]
    event = {}
    session = mock.MagicMock()
    mock_notifier = mock.MagicMock()
    suite = ValidationSuite(rules, mock_notifier)
    suite.validate(event, session)
    assert session, event == r1.called_with()
    assert session, event == r2.called_with()
    mock_notifier.notify.assert_called_with(expected_results)


def test_file_format_validator():
    event = {
        "Records": [{
            "s3": {
                "bucket": {
                    "name": "fake_bucket"
                },
                "object": {
                    "key": "reports/myfile.xls"
                }
            }
        }]
    }
    # Check reject xls
    v = FileFormatValidator("", "")
    v.validate(mock.MagicMock(), event)
    assert v.status == "FAILED"
    # Check csv is passes.
    event["Records"][0]["s3"]["object"]["key"] = "reports/myfile.csv"
    v = FileFormatValidator("", "")
    v.validate(mock.MagicMock(), event)
    assert v.status == "SUCCESS"


def test_get_schema():
    # Case 1 - we have a match on second path.
    paths = [
        {
            "pattern": "reports/.*"
        },
        {
            "pattern": "uploads/.*",
            "delimiter": "|",
            "primary_key": "id",
            "fields": [
                {
                    "name": "id",
                    "type": "string",
                    "nullable": False
                }
            ]
        }
    ]
    mock_loader = mock.MagicMock()
    mock_loader.load.return_value = {
        "paths": paths
    }
    r = ValidateSchema("", "", mock_loader)
    r.paths = paths
    session = mock.MagicMock()
    s = r.get_schema("uploads/aabbccdd.csv")
    assert isinstance(s, pyarrow.lib.Schema)
    # Case 2 - none found.
    r = ValidateSchema("", "", mock_loader)
    r.paths = paths
    with pytest.raises(NoMatchingSchemaException):
        r.get_schema("items/stuff.csv")
