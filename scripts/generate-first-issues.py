#!/bin/bash

import json
import os
import requests
import sys

here = os.path.dirname(os.path.abspath(__file__))
print("Present working directory is %s" % here)
api_base = "https://api.github.com/repos/{repo}/issues"

# GitHub Workflow - we get variables from environment
REPOS_FILE = os.environ.get("REPOS_FILE")
ISSUE_LABEL = os.environ.get("ISSUE_LABEL", "good first issue")
COLLECTION_FOLDER = os.environ.get("COLLECTION_FOLDER", "_issues")
if not REPOS_FILE:
    sys.exit(f"{REPOS_FILE} must be defined.")

if not os.path.exists(REPOS_FILE):
    sys.exit(f"{REPOS_FILE} does not exist.")

token = os.environ.get("GITHUB_TOKEN")
if not token:
    sys.exit("Please export GITHUB_TOKEN")

# Read in the repos file
with open(REPOS_FILE, "r") as filey:
    lines = filey.readlines()

# Must authenticate
headers = {"Authorization": f"token {token}"}
data = {"state": "open", "labels": ISSUE_LABEL}

# Documentation base is located at docs
output_dir = "/github/workspace/docs/%s" % COLLECTION_FOLDER

# Print metadata for user
print("Issue label: [%s]" % ISSUE_LABEL)
print("Collection output folder: [%s]" % output_dir)

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

# Load repos
for line in lines:

    # Extra tags are optional, separated by comma
    extra_tags = ""
    try:
        repo, extra_tags = line.strip().split(" ")
    except ValueError:
        repo = line.strip()

    extra_tags = extra_tags.split(",")
    repo = "/".join(repo.split("/")[-2:])
    url = api_base.format(repo=repo)

    print("Looking up issues for %s" % repo)

    # This will return the first
    response = requests.get(url, headers=headers, params=data)
    if response.status_code != 200:
        sys.exit("Error with response %s: %s" % (response.status_code, response.reason))
    issues = response.json()

    # For each issue, write a markdown file
    for issue in issues:
        date = issue["created_at"].split("T")[0]
        basename = "%s-%s-%s.md" % (date, repo.replace("/", "-"), issue["number"])
        filename = os.path.join(output_dir, basename)

        # Include front end matter for jekyll
        content = "---\n"

        # Add labels as tags
        tags = set([x["name"] for x in issue["labels"]])
        tags.remove(ISSUE_LABEL)
        tags = list(tags)

        if extra_tags:
            tags = tags + extra_tags
        if tags:
            tags = [x.replace(":", "").replace(" ", "-") for x in tags]
            tags.sort()
            print("Adding tags %s" % ",".join(tags))
            content += "tags: %s\n" % (",".join(tags))

        # Title must have quotes escaped
        content += 'title: %s\n' % json.dumps(issue["title"])
        content += 'html_url: "%s"\n' % issue["html_url"]
        content += "user: %s\n" % (issue["user"]["login"])
        content += "repo: %s\n" % repo
        content += "---\n\n"
        content += issue["body"]

        # Output to ../docs/_issues
        with open(filename, "w") as filey:
            filey.writelines(content)
