Feature: Wrong delimiter

    @local
    Scenario: File is created with the wrong delimiter (local test)
        Given the "wrong_delim" csv is uploaded to our s3 bucket
        Given the "wrong_delim" schema is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "ValidateSchema" check should fail
