Feature: File format is not a csv

    @local
    Scenario: File format of the file put into the bucket is not a csv (local test)
        Given the "fake.xls" file is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "FileFormatValidator" check should fail

