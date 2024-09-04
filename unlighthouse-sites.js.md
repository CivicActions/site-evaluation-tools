# URL Processor and Google Sheets Manager Script

## Overview

The `unlighthouse-sites.js` script processes URLs, either provided as a single URL or from a CSV file, and interacts with Google Sheets. It creates Google Sheets from a template to store URL-related data, such as evaluations or reports. The script checks, normalizes, and processes URLs, handles redirections, and appends new entries to a YAML configuration file (`unlighthouse-sites.yml`).

### Features:
- **Single or Batch URL Processing**: Process individual URLs or multiple URLs from a CSV file.
- **Google Sheets Integration**: Authenticates with the Google Sheets API, creates new Google Sheets from a template, and appends data.
- **YAML File Management**: Stores URL data (e.g., normalized URL, Google Sheet ID, and start date) in a YAML file for further tracking.
- **URL Normalization**: Normalizes URLs to ensure consistency and handles redirections.
- **Scheduling**: Assigns a random day of the week for scheduling.

## Installation

### Prerequisites:
1. **Node.js**: Ensure that Node.js is installed on your system. You can download it from [Node.js](https://nodejs.org/).
2. **Google Cloud Platform**: Set up a project and enable the Google Sheets API and Google Drive API.
3. **OAuth 2.0 Credentials**: Create OAuth 2.0 credentials and download the `credentials.json` file. Place the `credentials.json` and `token.json` files in the same directory as the script.

### Node.js Dependencies:
The following dependencies are used in this script:

- `axios`: For making HTTP requests to retrieve URLs.
- `googleapis`: For interacting with Google Sheets and Drive APIs.
- `fs`: For file system operations.
- `js-yaml`: For parsing and writing YAML files.
- `csv-parse`: For parsing CSV files.
- `commander`: For parsing command-line arguments.

Install these dependencies by running:

```bash
npm install axios googleapis fs js-yaml csv-parse commander
```

## Command-Line Arguments

The script accepts the following command-line options:

- `--url`: Add a single URL for processing.
- `--file`: Add multiple URLs from a CSV file.

### Example Usage

To process a single URL:

```bash
node unlighthouse-sites.js --url https://example.com
```

To process URLs from a CSV file:

```bash
node unlighthouse-sites.js --file urls.csv
```

## Notes

- Ensure that the `unlighthouse-sites.yml` file exists in the same directory as the script. This file stores the processed URLs and their associated Google Sheets.
- If a URL already exists in the YAML file, the script will skip adding it again.
- The `credentials.json` and `token.json` files are required for authenticating with Google Sheets.

## Context

This script automates the process of managing URLs and their associated Google Sheets for tracking purposes. It works by checking, normalizing, and storing URLs in a YAML configuration file (`unlighthouse-sites.yml`). The script interacts with the Google Sheets API to create new Google Sheets from a template for each new URL.

You can use this script to track site evaluations, manage accessibility reports, or automate the organization of URL data. The random day assignment feature makes it easy to schedule tasks over a week.

### Repository Structure:
- **unlighthouse-sites.js**: Script for processing URLs and creating Google Sheets.
- **unlighthouse-gTracker.sh**: A companion script for scanning sites listed in the YAML file.
- **unlighthouse-gTracker.js**: The JavaScript that is called by the above file and runs Unlighthouse & uploads the results to Google Sheets.

Ensure that you follow the installation steps and prerequisites to utilize the full capabilities of the script for managing URL tracking and site evaluations.
