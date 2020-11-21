Feature: Wrong dtype for a column

    @local
    Scenario: CSV has strings in an integer column
        Given the "wrong_dtype" csv is uploaded to our s3 bucket
        Given the "wrong_dtype" schema is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "SchemaValidator" check should fail
