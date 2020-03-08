#!/bin/bash

set -eu
set -o pipefail

# Get the relative path of the folder in docs to write output
if [ -z "${COLLECTION_FOLDER}" ]; then
    COLLECTION_FOLDER="_issues"
fi

# If the docs folder isn't created, do so.
if [ ! -d "/github/workspace/docs" ]; then
    printf "Creating docs folder for GitHub pages\n"
    cp -R /docs /github/workspace/docs
fi

# Cleanup old set of first issues
printf "Cleaning up previous first issues...\n"
rm -rf "/github/workspace/docs/${COLLECTION_FOLDER}"
export COLLECTION_FOLDER

# Generate first issues
python3 /generate-first-issues.py
