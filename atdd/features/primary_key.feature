Feature: Missing Data in Primary Key

    @local
    Scenario: Primary key of csv has missing data (local test)
        Given the "missing_pk" csv is uploaded to our s3 bucket
        Given the "missing_pk" schema is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "ValidateSchema" check should fail

