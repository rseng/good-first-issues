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
# This is expected to be run in a GitHub action
output_dir = "/github/workspace/docs/%s" % COLLECTION_FOLDER

# Clear out previous issues, might be old
shutil.rmtree(outdir_dir)
os.makedirs(output_dir)

# Print metadata for user
print("Issue label: [%s]" % ISSUE_LABEL)
print("Collection output folder: [%s]" % output_dir)

if not os.path.exists(output_dir):
    os.mkdir(output_dir)


def generate_markdown(line):
    """
    Generate markdown for a repo / tags
    """
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
        print(
            "Issue with response %s: %s, sleeping"
            % (response.status_code, response.reason)
        )
        time.sleep(60)
        return None, None

    issues = response.json()

    # For each issue, write a markdown file
    for issue in issues:
        date = issue["created_at"].split("T")[0]
        basename = "%s-%s-%s.md" % (date, repo.replace("/", "-"), issue["number"])
        filename = os.path.join(output_dir, basename)

        # Include front end matter for jekyll
        content = "---\n"

        # Add labels as tags
        tags = list([x["name"] for x in issue["labels"]])
        if ISSUE_LABEL in tags:
            tags.remove(ISSUE_LABEL)

        if extra_tags:
            tags = tags + extra_tags
        if tags:
            tags = [x.replace(":", "").replace(" ", "-") for x in tags]
            tags = [x for x in tags if x]
            tags.sort()
            if tags:
                print("Adding tags %s" % ",".join(tags))
                content += "tags: %s\n" % (",".join(tags))

        # Sometimes people leave the body empty
        body = issue["body"] or issue["title"]

        # Title must have quotes escaped
        content += "title: %s\n" % json.dumps(issue["title"])
        content += 'html_url: "%s"\n' % issue["html_url"]
        content += "user: %s\n" % (issue["user"]["login"])
        content += "repo: %s\n" % repo
        content += "---\n\n"
        content += body
    return filename, content


# Load repos
for line in lines:

    # Output to ../docs/_issues
    try:
        filename, content = generate_markdown(line)
        if not filename or not content:
            continue
        with open(filename, "w") as filey:
            filey.writelines(content)
    except:
        print(f"Issue saving issue for {filename}")

count = os.listdir(output_dir)
print(f"Found {count} total issues.")
