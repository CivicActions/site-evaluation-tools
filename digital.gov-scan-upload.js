/*
 * GitHub Repo Tracker Script
 * 
 * Description:
 * This Node.js script downloads a CSV file from a specified URL, renames it with the current date, 
 * and uploads its contents to a new Google Sheets document. The script also updates an "Introduction" sheet 
 * within the Google Sheets document to keep track of the new sheet names. The Google Sheets API is used 
 * to handle authentication and data operations.
 *
 * Features:
 * - Downloads a CSV file from a given URL.
 * - Renames the downloaded file with the current date.
 * - Authenticates and uploads the CSV data to a new Google Sheets document.
 * - Ensures unique sheet titles to prevent overwrites.
 * - Updates an "Introduction" sheet with the title of the newly created sheet.
 *
 * This script is intended to run on a weekly cron job to automate data collection and organization.
 *
 * License:
 * This script is licensed under the GNU General Public License v3.0. 
 * You can redistribute it and/or modify it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
 * implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along with this program. If not, see 
 * <https://www.gnu.org/licenses/>.
 */
const axios = require('axios');
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const baseDir = path.resolve(__dirname);
const RESULTS_DIR = path.join(baseDir, "results");
const CREDENTIALS_PATH = path.join(baseDir, "credentials.json");
const TOKEN_PATH = path.join(baseDir, "token.json");

console.log('Reading credentials from:', CREDENTIALS_PATH);
console.log('File exists:', fs.existsSync(CREDENTIALS_PATH));
console.log("Environment variables:", process.env);

const downloadAndRenameFile = async (url) => {
    console.log('Downloading file from:', url);
    const response = await axios({
        url,
        method: 'GET',
        responseType: 'stream'
    });

    const date = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    const filePath = path.join(__dirname, `weekly-snapshot-${date}.csv`);
    console.log('Renaming downloaded file to:', filePath);

    const writer = fs.createWriteStream(filePath);

    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
        writer.on('finish', () => {
            console.log('File download and rename finished');
            resolve(filePath);
        });
        writer.on('error', (error) => {
            console.error('Error in file download and rename:', error);
            reject(error);
        });
    });
};

async function authenticateGoogleSheets(credentialsPath) {
    console.log('Authenticating Google Sheets with credentials from:', credentialsPath);
    const content = await fs.promises.readFile(credentialsPath, 'utf8');
    const credentials = JSON.parse(content);
    const { client_secret, client_id, redirect_uris } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

    let token;
    try {
        console.log('Reading token from:', TOKEN_PATH);
        token = await fs.promises.readFile(TOKEN_PATH, 'utf8');
    } catch (error) {
        console.error('Token file not found, requesting new token:', error);
        return getNewToken(oAuth2Client);
    }

    oAuth2Client.setCredentials(JSON.parse(token));
    console.log('Google Sheets authenticated successfully');
    return oAuth2Client;
}

function getNewToken(oAuth2Client) {
    const authUrl = oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    console.log('Authorize this app by visiting this URL:', authUrl);
    // Further implementation needed to handle the new token
    // Typically involves a web server to receive the response

    // Handle errors
    try {
        // Code that may throw an error
    } catch (error) {
        console.error('Error in token generation:', error);
        // Handle the error appropriately
    }
}

function cleanCell(cell) {
    let cleanedCell = cell.replace(/^"|"$/g, "").trim(); // Remove surrounding quotes
    cleanedCell = cleanedCell.replace(/""/g, '"'); // Replace double quotes with single
    return cleanedCell;
}

const uploadToGoogleSheet = async (filePath, sheets, spreadsheetId) => {
    console.log('Uploading data to Google Sheets from file:', filePath);
    const content = fs.readFileSync(filePath, 'utf8');

    // Parse the CSV content correctly handling commas within quotes
    const records = parse(content, {
        columns: false,
        skip_empty_lines: true,
    });

    const rows = records.map(row => row.map(cell => cleanCell(cell)));

    const today = new Date();
    let sheetTitle = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, "0")}-${today.getDate().toString().padStart(2, "0")}`;

    console.log('Checking if sheet with title already exists:', sheetTitle);
    
    // Check if the sheet already exists
    const sheetExists = await sheets.spreadsheets.get({
        spreadsheetId
    }).then(res => {
        return res.data.sheets.some(sheet => sheet.properties.title === sheetTitle);
    });

    if (sheetExists) {
        console.log(`Sheet with title "${sheetTitle}" already exists. Generating a new title.`);
        sheetTitle = `${sheetTitle}-${Date.now()}`; // Append timestamp to make title unique
    }

    console.log('Creating new sheet with title:', sheetTitle);

    // Create a new sheet with the unique title
    await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        resource: {
            requests: [
                {
                    addSheet: {
                        properties: {
                            title: sheetTitle,
                        },
                    },
                },
            ],
        },
    });

    console.log('Appending data to new sheet:', sheetTitle);
    // Append the data to the new sheet
    await sheets.spreadsheets.values.append({
        spreadsheetId,
        range: `${sheetTitle}!A1`,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: rows
        }
    });
    console.log('Data uploaded to Google Sheets successfully');
    return sheetTitle;
};

const updateIntroductionSheet = async (sheets, spreadsheetId, sheetTitle) => {
    console.log('Updating the "Introduction" sheet with new data');

    // Get the data in column G of the "Introduction" sheet
    const range = 'Introduction!G:G';
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: range,
    });

    const values = response.data.values || [];
    const lastRow = values.length + 1;

    // Update the last empty cell in column G with the new sheet title
    await sheets.spreadsheets.values.update({
        spreadsheetId,
        range: `Introduction!G${lastRow}`,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: [[sheetTitle]]
        }
    });

    console.log(`"Introduction" sheet updated successfully with ${sheetTitle} at row ${lastRow}`);
};

const main = async () => {
    const fileUrl = 'https://api.gsa.gov/technology/site-scanning/data/weekly-snapshot.csv';
    const spreadsheetId = '1CsXAzCzghYYwXzGCcrJqrsWpr5f7MbID2Qw6vQvi3sQ'; // Replace with your spreadsheet ID

    try {
        console.log('Starting file download and rename process');
        const filePath = await downloadAndRenameFile(fileUrl);
        console.log('File downloaded and renamed:', filePath);

        console.log('Starting Google Sheets authentication process');
        const auth = await authenticateGoogleSheets(CREDENTIALS_PATH);
        const sheets = google.sheets({ version: 'v4', auth });

        console.log('Starting data upload to Google Sheets');
        const sheetTitle = await uploadToGoogleSheet(filePath, sheets, spreadsheetId);
        console.log('File uploaded successfully');

        console.log('Updating the "Introduction" sheet');
        await updateIntroductionSheet(sheets, spreadsheetId, sheetTitle);
        console.log('Introduction sheet updated successfully');
    } catch (error) {
        console.error('Error in main process:', error);
    }
};

main();
