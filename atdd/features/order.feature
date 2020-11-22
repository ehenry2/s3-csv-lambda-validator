Feature: Columns are out of order

    @local
    Scenario: Columns are in the wrong order in the CSV file
        Given the "col_out_of_order" csv is uploaded to our s3 bucket
        Given the "col_out_of_order" schema is uploaded to our s3 bucket
        When the csv validator is triggered locally
        Then the "ValidateSchema" check should fail
