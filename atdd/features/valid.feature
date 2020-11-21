Feature: Valid CSVs are sucessful

    @local
    Scenario: Valid CSV is created (local test)
        Given the "valid" csv is uploaded to our s3 bucket
        Given the "valid" schema is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then all checks should pass successfully

    @qa
    Scenario: Valid CSV is created
        Given the "valid" csv is uploaded to our s3 bucket
        Given the "valid" schema is uploaded to our s3 bucket
        When the csv validator lambda function is triggered
        Then all checks should pass successfully