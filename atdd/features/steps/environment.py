from behave import *
from dotenv import load_dotenv


def before_all(context):
    load_dotenv()
