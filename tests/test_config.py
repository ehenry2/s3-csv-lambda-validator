import json
import os
import unittest.mock as mock

from csv_validator.config import S3JsonLoader

import pytest


@pytest.fixture(scope='module')
def simple_schema_raw():
    here = os.path.dirname(os.path.realpath(__file__))
    there = os.path.join(here, "fixtures/simple.json")
    with open(there) as f:
        content = f.read().encode('utf-8')
    return content


def test_s3_json_loader(simple_schema_raw):
    mock_stream = mock.MagicMock()
    mock_stream.read.return_value = simple_schema_raw
    get_obj_resp = {
        "Body": mock_stream
    }
    mock_client = mock.MagicMock(name="mock_client")
    mock_client.get_object.return_value = get_obj_resp
    session = mock.MagicMock(name="mock_session")
    session.client.return_value = mock_client
    bucket = "ita9999-fake-bucket"
    key = "some/place/my.json"
    loader = S3JsonLoader(bucket, key)
    result = loader.load(session)
    assert result == json.loads(simple_schema_raw)
