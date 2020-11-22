Feature: Incorrect file names

    @local
    Scenario: File has the wrong name (abc.txt instaed of file.txt)
        Given the "abc.csv" file is uploaded to our s3 bucket
        Given the schema is uploaded with correct path information
        When the csv validator is triggered locally
        Then the "ValidateSchema" check should fail
