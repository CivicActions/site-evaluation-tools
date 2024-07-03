# GitHub Repo Tracker

This Node.js script downloads a CSV file from a specified URL, renames it with the current date, and uploads its contents to a new Google Sheets document. The script also updates an “Introduction” sheet within the Google Sheets document to keep track of the new sheet names. The Google Sheets API is used to handle authentication and data operations.

## Overview

### The script performs the following steps:

1. Downloads a CSV file from the Site Scanning page.
1. Renames the file with the current date.
1. Authenticates with Google Sheets using provided credentials.
1. Uploads the CSV data to a new sheet in the specified Google Sheets document.
1. Updates an “Introduction” sheet in the Google Sheets document with the title of the newly created sheet.

### Advantages

* Data Aggregation: The data is easier to consume in a Google Sheets format than in a CSV file.
* Data Integrity: Changes in the data structure can be detected, allowing for error checking.
digital.gov-scan-upload.js.mdAccountability: Highlighting agencies that are falling behind can encourage improvements. Monitoring and visibility are key.

## Google Sheets Document

The processed data is uploaded to the following Google Sheets document: [Google Sheets Link](https://docs.google.com/spreadsheets/d/1CsXAzCzghYYwXzGCcrJqrsWpr5f7MbID2Qw6vQvi3sQ)

## Installation Instructions

### Prerequisites

* Node.js (v16 or later recommended)
* npm (Node Package Manager)
* Google Cloud project with Google Sheets API enabled
* Credentials JSON file for Google Sheets API

## Install

1. Download the digital.gov-scan-upload.js file
1. Setup a [Google Cloud](https://developers.google.com/workspace/guides/create-project) project
1. Enable the [Google Sheets API](https://developers.google.com/sheets)
1. Save your [OAuth](https://developers.google.com/workspace/guides/configure-oauth-consent) Config
1. Ensure you have a recent version of node running
1. Run `node digital.gov-scan-upload.js.md`
 

## License

This project is licensed under the GNU General Public License v3.0. You can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

This README file includes installation instructions, a brief overview of the script, the advantages of using the script, and the necessary setup and scheduling details.