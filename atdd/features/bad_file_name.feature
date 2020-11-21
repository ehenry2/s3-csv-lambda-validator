Feature: Incorrect file names

    @local @inprog
    Scenario: File has the wrong name (abc.txt instaed of file.txt)
        Given the "abc.txt" file is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "FileFormatValidator" check should fail

