# Unlighthouse Scanner YAML Creation Tool

## Overview

The unlighthouse-sites.js script processes URLs and creates Google Sheets (from a template) to store site evaluations. New entries (with the domain, and google sheet URL) are then stored in a YAML file. It supports adding URLs directly or from a CSV file, normalizing and checking URLs, creating Google Sheets.

## Installation

### Prerequisites

* Node.js: Ensure Node.js is installed on your system. You can download it from Node.js.
* Google Cloud Platform: Set up a project and enable the Google Sheets API and Google Drive API.
* OAuth 2.0 Credentials: Create OAuth 2.0 credentials and download the credentials.json file.

Node Dependancies
* axios: Making HTTP requests.
* googleapis: Interacting with Google Sheets and Drive APIs.
* fs: File system operations.
* js-yaml: Parsing and writing YAML files.
* csv-parse: Parsing CSV files.
* commander: Command-line argument parsing.

### Command-Line Arguments
```
	•	--url: Add a single URL.
	•	--file: Add URLs from a CSV file.
```

### Example
`node unlighthouse-sites.js --url https://example.com## Usage`


## Notes

* Ensure the unlighthouse-sites.yml file exists in the same directory as this script.
* The script supports both single URL and batch URL processing via a CSV file.
* Google Sheets and YAML configuration are updated only if the URL does not already exist in the YAML file.

## Context

The unlighthouse-gTracker.js script relies on a YAML configuration file (unlighthouse-sites.yml) that lists the sites to be scanned. This file can be populated using the unlighthouse-sites.js script, which allows for adding new URLs and their corresponding Google Sheets information. This setup ensures that the scanning and reporting process is streamlined and organized, leveraging both scripts for effective site evaluations and accessibility checks.

Repository: CivicActions/site-evaluation-tools
* unlighthouse-gTracker.js: Main script for scanning and reporting.
* unlighthouse-sites.js: Script for managing URLs and Google Sheets.

Ensure to follow the installation steps and prerequisites for both scripts to utilize their full capabilities for site evaluations and accessibility checks.
