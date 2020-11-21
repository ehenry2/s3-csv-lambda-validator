import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io


class Notifier:
    """
    Base notifier class. Inherit and implement notify function
    to implement your own notifier.
    """
    def notify(self, results):
        """
        Send a notification to the user when complete.

        :param results: The results in tuple form for each rule.
                        The tuple has the format (status, name, description, output)
        :type  results: List of tuples of (string, string, string, string)
        """
        raise NotImplementedError()


class DebugNotifier(Notifier):
    """
    Prints results to stdout.
    """
    def notify(self, results):
        """
        Send a notification to the user when complete.

        :param results: The results in tuple form for each rule.
                        The tuple has the format (status, name, description, output)
        :type  results: List of tuples of (string, string, string, string)
        """
        print(results)


class CsvEmailNotifier(Notifier):
    """
    Sends csv as a notification via email.
    """
    def __init__(self, sender, recipients, session):
        self.sender = sender
        self.recipients = recipients
        self.session = session

    @staticmethod
    def _results_to_csv_buffer(results):
        # Stream csv data to in-memory buffer.
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        # Write the header.
        header = ("status", "name", "description", "output")
        writer.writerow(header)
        for row in results:
            writer.writerow(row)
        # Return the buffer.
        return buffer

    def _buffer_to_attached_email(self, buffer):
        # Create multipart email.
        msg = MIMEMultipart('mixed')
        msg["From"] = self.sender
        msg["Subject"] = "S3 File Notification Report"
        # Add the body.
        body = "S3 file notification report"
        msg.attach(MIMEText(body, "plain"))
        # Add the csv file.
        attachment = MIMEText(buffer.getvalue(), "csv")
        attachment.add_header(
            "Content-Disposition",
            "attachment; filename= report.csv"
        )
        msg.attach(attachment)
        return msg.as_string()

    def notify(self, results):
        """
        Send a notification to the user when complete.

        :param results: The results in tuple form for each rule.
                        The tuple has the format (status, name, description, output)
        :type  results: List of tuples of (string, string, string, string)
        """
        # For email, we probably only want to notify if a failure has
        # occurred, so check first before we send anything.
        failed = False
        for result in results:
            if result[0] == "FAILED":
                failed = True
        if not failed:
            return
        # Send an email
        buffer = CsvEmailNotifier._results_to_csv_buffer(results)
        client = self.session.client('sesv2')
        client.send_email(
            Destination={
                "ToAddresses": self.recipients
            },
            Content={
                "Raw": {
                    "Data": self._buffer_to_attached_email(buffer)
                }
            }
        )
