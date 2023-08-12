#!/bin/bash

# Define the directory to search in
target_directory="output"

# Loop through all subdirectories
for dir in "$target_directory"/*; do
    if [ -d "$dir" ]; then
        # Rename files from balance_sheet.csv to balance_sheet_statement.csv
        find "$dir" -name "balance_sheet.csv" -execdir mv '{}' "$(dirname '{}' )/balance_sheet_statement.csv" \;
    fi
done
