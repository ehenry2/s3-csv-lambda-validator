import json
import logging


class ConfigLoader:
    """
    Base class to load a configuration. To create your own
    custom configuration loading logic (e.g. hive), subclass
    this and implement logic for load function.
    """
    def load(self, session):
        """
        Load the configuration using whatever logic needed.

        :param session: Boto3 session
        :type  session: boto3 session

        :returns: configuration dict
        """
        raise NotImplementedError()


class S3JsonLoader(ConfigLoader):
    """
    Loads the configuration from a json file in s3.
    """
    def __init__(self, bucket, key):
        """
        Constructor.

        :param bucket: The s3 bucket the config file is in.
        :type  bucket: string

        :param key: The key name of the json file.
        :type  key: string
        """
        self.bucket = bucket
        self.key = key
    
    def load(self, session):
        """
        Load the configuration using whatever logic needed.

        :param session: Boto3 session
        :type  session: boto3 session

        :returns: configuration dict
        """
        client = session.client("s3")
        logging.info(f"Loading schema from s3://{self.bucket}/{self.key}")
        result = client.get_object(Bucket=self.bucket, Key=self.key)
        body = result["Body"].read()
        return json.loads(body)
