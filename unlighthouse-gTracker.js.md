# Unlihthouse Tracker (unlighthouse-gTracker.js)

## Overview

The unlighthouse-gTracker.js script automates the process of crawling and scanning websites for accessibility issues using the Purple-A11y tool, then uploads the results to Google Sheets. This process involves parsing command-line arguments, authenticating with Google Sheets API, creating Google Sheets if they don’t exist, running the Purple-A11y tool, processing scan results, and uploading them to Google Sheets.

## Installation

### Prerequisites

1. Node.js: Ensure Node.js is installed on your system. You can download it from Node.js.
1. Google Cloud Platform: Set up a project and enable the Google Sheets API and Google Drive API.
1. OAuth 2.0 Credentials: Create OAuth 2.0 credentials and download the credentials.json file.

### Dependencies

	•	fs: File system operations.
	•	path: Handling file paths.
	•	csv-parse: Parsing CSV files.
	•	googleapis: Interacting with Google Sheets and Drive APIs.
	•	jsdom: Parsing HTML content.
	•	yargs: Command-line argument parsing.
	•	child_process: Running external commands.
	•	crypto: Generating MD5 hashes.

### Steps

1. Download the unlighthouse-gTracker.js file
1. Setup a Google Cloud project
1. Enable the Google Sheets API
1. Save your OAuth Config
1. Ensure you have a recent version of node running
1. Run node unlighthouse-gTracker.js

### YAML Configuration

Create and populate the unlighthouse-sites.yml file with the sites you want to scan.

## Usage

### Command-Line Arguments

	•	--type: Type of scan (default: crawl).
	•	--name: Name of the site.
	•	--url: URL of the site to scan.
	•	--max: Maximum number of pages to scan (default: 100).
	•	--sheet_id: Google Sheets ID where the results will be uploaded.
	•	--exclude: URLs to exclude from the scan.
	•	--strategy: Strategy for scanning (e.g., same-hostname, sitemap).

## Runing the Script
`node unlighthouse-gTracker.js --type crawl --name Example --url https://example.com --max 100 --sheet_id <spreadsheet-id> --exclude '' --strategy same-hostname`

## Notes

	•	Ensure the google-crawl.yml file exists in the same directory as this script.
	•	The script creates a lock file (scan.lock) to prevent multiple instances from running simultaneously.
