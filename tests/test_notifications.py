import unittest.mock as mock

from csv_validator.notifications import CsvEmailNotifier


def test_results_to_csv_buffer():
    notifier = CsvEmailNotifier("", [], mock.Mock())
    expected = \
"""status,name,description,output,bucket,key\r
OK,check_1,First check,,testb,testkey\r
FAILED,check_2,Second check,failed,testb,testkey\r
"""
    results = [
        ("OK", "check_1", "First check", "", 'testb', 'testkey'),
        ("FAILED", "check_2", "Second check", "failed", 'testb', 'testkey')
    ]
    buf = notifier._results_to_csv_buffer(results)
    assert buf.getvalue() == expected


def test_ses_notify():
    # Case 1 - we have failure, send email.
    results = [
        ("OK", "check_1", "First check", "", 'testb', 'testkey'),
        ("FAILED", "check_2", "Second check", "failed", 'testb', 'testkey')
    ]
    mock_client = mock.MagicMock(name="mock_client")
    mock_session = mock.MagicMock(name="mock_session")
    mock_session.client.return_value = mock_client
    email = "me@example.com"
    recipients = ["you@example.com"]
    notifier = CsvEmailNotifier(email, recipients, mock_session)
    notifier.notify(results)
    mock_client.send_email.assert_called()
    # Case 2 - no failure, don't send.
    results = [
        ("OK", "check_1", "First check", "", 'testb', 'testkey')
    ]
    mock_client = mock.MagicMock(name="mock_client")
    mock_session = mock.MagicMock(name="mock_session")
    mock_session.client.return_value = mock_client
    email = "me@example.com"
    recipients = ["you@example.com"]
    notifier = CsvEmailNotifier(email, recipients, mock_session)
    notifier.notify(results)
    mock_client.send_email.assert_not_called()
