import logging
import re

import pyarrow
import pyarrow.csv as csv
import pyarrow.fs as fs


NOT_RUN = "NOT_RUN"
STARTED = "STARTED"
SUCCESS = "SUCCESS"
FAILED = "FAILED"
TABLE_NAME = "SCHEMA_TABLE_NAME"


class Rule:
    """
    Base class representing a rule. Rules should implement
    the validate() method.
    """
    def __init__(self, name, description):
        """
        Constructor.

        :param name: Name of the rule.
        :type  name: String

        :param description: Description of the rule
        :type  description: String
        """
        self.description = description
        self.status = NOT_RUN
        self.output = ""
        self.continue_on_fail = False
        self.name = name

    def fail(self, message):
        """
        Acknowledge that the rule failed.

        :param message: Output/Explanation for rule failure.
        :type  message: String
        """
        self.status = FAILED
        self.output = message

    def validate(self, session, event):
        """
        Run the business logic of the rule.

        :param session: Boto3 session
        :type  session: Boto3 session

        :param event: Event passed to the lambda
        :type  event: dict
        """
        raise NotImplementedError


class ValidationSuite:
    """
    This class contains the base logic to run all of the rules
    and deliver the validation result.
    """
    def __init__(self, rules, notifier):
        """
        Constructor.

        :param rules: List of rules that the suite will validate.
        :type rules: List of objects that implement Rule interface.

        :param notifier: The notifier that encapsulates the logic of sending
                         the notification.
        :type  notifier: object that implements Notifier
        """
        self.rules = rules
        self.notifier = notifier
    
    def validate(self, event, session):
        """
        Run validation on all the rules and send a notification.

        :param event: The event passed to the lambda.
        :type  event: dict

        :param session: boto3 session
        :type  session: boto3 session
        """
        results = []
        for rule in self.rules:
            rule.validate(session, event)
            results.append((rule.status, rule.name, rule.description, rule.output))
            if rule.status == FAILED and rule.continue_on_fail is False:
                break
        self.notifier.notify(results)


class NoMatchingSchemaException(Exception):
    pass


class WrongDelimiterException(Exception):
    pass


class ColumnOrderException(Exception):
    pass


class EmptyPrimaryKeyException(Exception):
    pass


class FileFormatValidator(Rule):

    def validate(self, session, event):
        self.status = STARTED
        for record in event["Records"]:
            key = record["s3"]["object"]["key"]
            logging.info(f"Validating csv file format for {key}")
            if key.split(".")[-1] != "csv":
                msg = f"{key} does not match pattern of *.csv"
                logging.info(msg)
                self.fail(msg)
                return
        self.status = SUCCESS


class ValidateSchema(Rule):

    def __init__(self, name, description, config_loader):
        super().__init__(name, description)
        self.paths = None
        self.config_loader = config_loader
        self.delimiter = None
        self.pattern = None
        self.primary_key = None

    def validate(self, session, event):
        self.status = STARTED
        self.paths = self.config_loader.load(session)["paths"]
        for record in event["Records"]:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            logging.info(f"Validating schema of file: s3://{bucket}/{key}")
            try:
                schema = self.get_schema(key)
                self.scan_file(bucket, key, schema)
            except pyarrow.lib.ArrowInvalid as e:
                self.fail(e.args[0])
                return
            except NoMatchingSchemaException:
                self.fail(f"No schema matches key: {key}")
                return
            except WrongDelimiterException:
                self.fail("Delimiter of the file is incorrect")
                return
            except ColumnOrderException as e:
                self.fail(str(e))
                return
            except EmptyPrimaryKeyException as e:
                self.fail("Primary key column has a missing value")
                return
            except Exception as e:
                self.fail("Unknown error: {0}".format(str(e)))
                return
        self.status = SUCCESS

    def scan_file(self, bucket, key, schema):
        logging.info(f"delim is {self.delimiter}")
        uri = f"{bucket}/{key}"
        s3fs = fs.S3FileSystem()
        # Run column order validation by opening and not reading anything.
        filestream = s3fs.open_input_stream(uri)
        reader = csv.open_csv(filestream)
        for index, col in enumerate(reader.schema):
            if col.name != schema[index].name:
                msg = "column {} is out of order".format(col.name)
                raise ColumnOrderException(msg)
        # Run the rest of the validations.
        filestream = s3fs.open_input_stream(uri)
        opts = csv.ConvertOptions(column_types=schema)
        parse_opts = csv.ParseOptions(delimiter=self.delimiter)
        reader = csv.open_csv(filestream, convert_options=opts,
                              parse_options=parse_opts)
        # Kind of a hack, but it works...if delim wrong, everything is read
        # as one column.
        if len(schema) > 1 and len(reader.schema) == 1:
            raise WrongDelimiterException()
        # Parse through the file, pyarrow will through exceptions
        # if there's invalid data.
        for batch in reader:
            # If primary key is a string, need to check the column
            # for empty strings.
            if schema.field(self.primary_key).type == "string":
                table = pyarrow.Table.from_batches([batch])
                for val in table[self.primary_key]:
                    if val.as_py() == "":
                        raise EmptyPrimaryKeyException()


    def get_schema(self, key):
        for path in self.paths:
            pattern = path["pattern"]
            if re.match(pattern, key):
                self.delimiter = path["delimiter"]
                self.pattern = path["pattern"]
                self.primary_key = path["primary_key"]
                fields = []
                for field in path["fields"]:
                    fields.append(
                        pyarrow.field(
                            field["name"],
                            field["type"],
                            field["nullable"]
                        )
                    )
                schema = pyarrow.schema(fields)
                return schema
        raise NoMatchingSchemaException()

