#!/bin/bash

# Script to merge OAuth files into a single JSON file
# Usage: ./merge_oauth.sh [output_file]

OUTPUT_FILE="${1:-OAUTH.json}"
TEMP_FILE=$(mktemp)

echo "{" > "$TEMP_FILE"

# Find all files ending with _OAUTH
oauth_files=($(ls *_OAUTH 2>/dev/null))

if [ ${#oauth_files[@]} -eq 0 ]; then
    echo "No *_OAUTH files found in current directory"
    rm "$TEMP_FILE"
    exit 1
fi

# Process each OAuth file
for i in "${!oauth_files[@]}"; do
    file="${oauth_files[$i]}"
    
    # Extract the name (everything before _OAUTH)
    name=$(basename "$file" _OAUTH)
    
    # Read the token from the file
    token=$(cat "$file" | tr -d '\n\r')
    
    # Add comma if not the first entry
    if [ $i -gt 0 ]; then
        echo "," >> "$TEMP_FILE"
    fi
    
    # Add the key-value pair to JSON
    echo -n "  \"$name\": \"$token\"" >> "$TEMP_FILE"
done

echo "" >> "$TEMP_FILE"
echo "}" >> "$TEMP_FILE"

# Move temp file to final output
mv "$TEMP_FILE" "$OUTPUT_FILE"

echo "OAuth files merged successfully into $OUTPUT_FILE"
echo "Files processed: ${oauth_files[*]}" 