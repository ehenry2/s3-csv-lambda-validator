import argparse
import json
import os

import pyarrow.csv as csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-file", help="CSV file to scan")
    parser.add_argument("-o", "--output-file", help="Schema file to create or modify")
    parser.add_argument("-d", "--delimiter", help="delimiter for the file")
    parser.add_argument("-k", "--primary-key", help="Field name that is the primary key")
    parser.add_argument("-p", "--pattern",
                        help=("pattern to match the schema to file. "
                              "Example: 'reports/.*' will match 'reports/john.csv"))
#    parser.add_argument("-e", "--extension", help="File extension expected (e.g. .csv)")
    args = parser.parse_args()

    # Parse the input file.
    df = csv.read_csv(args.input_file,
                      parse_options=csv.ParseOptions(delimiter=args.delimiter))
    fields = []
    for field in df.schema:
        item = {
            "name": field.name,
            "type": str(field.type),
            "nullable": field.nullable
        }
        # Force primary key to be not-null.
        if field.name == args.primary_key:
            item["nullable"] = False
        fields.append(item)
    # Prepare the output.
    root = {"paths": []}
    if os.path.exists(args.output_file):
        with open(args.output_file) as f:
            root = json.loads(f.read())
    root["paths"].append(
        {
            "delimiter": args.delimiter,
            "primary_key": args.primary_key,
            "pattern": args.pattern,
#            "extension": args.extension,
            "fields": fields
        }
    )
    with open("schema.json", "w") as f:
        f.write(json.dumps(root, indent=4))

if __name__ == '__main__':
    main()
