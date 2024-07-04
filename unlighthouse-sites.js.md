# Unlighthouse Scanner YAML Creation Tool

## Overview

The unlighthouse-sites.js script processes URLs and manages Google Sheets for site evaluations. It supports adding URLs directly or from a CSV file, normalizing and checking URLs, creating Google Sheets from a template, and updating a YAML configuration file with new entries.

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
	•	--url: Add a single URL.
	•	--file: Add URLs from a CSV file.

### Example
`node unlighthouse-sites.js --url https://example.com## Usage`
