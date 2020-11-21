import json

from .rules import evaluate_rules

import boto3
from dotenv import load_dotenv


def run_scenario_from_json(filename):
    load_dotenv()
    with open(filename) as f:
        event = json.load(f)
    session = boto3.session.Session()
    results = evaluate_rules(event, session)
