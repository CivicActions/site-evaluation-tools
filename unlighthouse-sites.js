/**
 * This script is licensed under the GNU General Public License (GPL).
 * 
 * This script automates the process of processing URLs and managing Google Sheets.
 * It performs the following steps:
 * 
 * 1. Parses command-line arguments to get the URL or file containing URLs.
 * 2. Authenticates with the Google Sheets API.
 * 3. Normalizes and checks the provided URL.
 * 4. Creates a Google Sheet from a template if the URL does not already exist in the YAML configuration.
 * 5. Updates the YAML configuration with new URLs and their corresponding Google Sheet information.
 * 6. Logs relevant information and errors throughout the process.
 * 
 * Dependencies:
 * - 'axios' for making HTTP requests.
 * - 'googleapis' for interacting with Google Sheets and Google Drive.
 * - 'fs' for file system operations.
 * - 'js-yaml' for parsing and writing YAML files.
 * - 'csv-parse' for parsing CSV files.
 * - 'commander' for command-line argument parsing.
 * 
 * Usage:
 * - Ensure that 'unlighthouse-sites.yml', 'credentials.json', and 'token.json' exist in the same directory as this script.
 * - Run the script using Node.js with appropriate arguments, e.g., `node <script-name>.js --url https://www.example.com` or `node <script-name>.js --file urls.csv`.
 * - The results will be updated in the YAML configuration and Google Sheets.
 */

const axios = require('axios');
const { google } = require('googleapis');
const fs = require('fs');
const yaml = require('js-yaml');
const { parse } = require('csv-parse/sync');
const { Command } = require('commander');

const SCOPES = [
  'https://www.googleapis.com/auth/spreadsheets',
  'https://www.googleapis.com/auth/drive'
];

const TOKEN_PATH = 'token.json';
const CREDENTIALS_PATH = 'credentials.json';

const program = new Command();
program
  .version('0.1.1')
  .description('Script to process URLs and manage Google Sheets.')
  .option('-u, --url <type>', 'Add a single URL')
  .option('-f, --file <type>', 'Add URLs from a CSV file')
  .on('--help', () => {
    console.log('\nExample calls:');
    console.log('  $ node unlighthouse-sites.js --url https://www.example.com');
    console.log('  $ node unlighthouse-sites.js --file urls.csv');
  })
  .parse(process.argv);

const options = program.opts();

if (!options.url && !options.file) {
  console.log('Error: No URL or file provided.');
  program.help(); // Display help and exit if no valid option provided
}

const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const authenticateGoogleSheets = async () => {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const { client_secret, client_id, redirect_uris } = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  try {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf8'));
    oAuth2Client.setCredentials(token);
    return oAuth2Client;
  } catch (error) {
    console.log('Error loading the token from file:', error);
    return null;
  }
};

// Normalize URL by removing trailing slashes, www, and ensuring https protocol
const normalizeUrl = (url) => {
  try {
    const urlObj = new URL(url);
    urlObj.protocol = 'https:';
    urlObj.hostname = urlObj.hostname.replace(/^www\./, '');
    return urlObj.toString().replace(/\/+$/, '');
  } catch (error) {
    console.error('Invalid URL:', url, error);
    return url;
  }
};

// Check and extract final URL and title after redirections
const checkUrl = async (url) => {
  try {
    const response = await axios.get(url, { maxRedirects: 5 });
    const finalUrl = normalizeUrl(response.request.res.responseUrl);
    const titleMatch = response.data.match(/<title>(.*?)<\/title>/i);
    return { url: finalUrl, title: titleMatch ? titleMatch[1] : 'No Title' };
  } catch (error) {
    console.error('Failed to retrieve URL:', url, error);
    return null;
  }
};

const createFromTemplate = async (auth, templateId, newTitle) => {
  const drive = google.drive({ version: 'v3', auth });
  try {
    const copy = await drive.files.copy({
      fileId: templateId,
      requestBody: {
        name: newTitle,
        parents: ['1-8FGgtrPBH7aZrMxVlAkxooHXSzDv-w_'] // Replace 'actual-folder-id' with your actual folder ID
      }
    });
    console.log('Spreadsheet ID:', copy.data.id);
    console.log('Spreadsheet URL:', `https://docs.google.com/spreadsheets/d/${copy.data.id}/edit`);
    return copy.data;
  } catch (err) {
    console.error('Failed to create spreadsheet from template:', err);
    return null;
  }
};

// Update YAML file with new data
const updateYAML = (filePath, data) => {
  let doc = yaml.load(fs.readFileSync(filePath, 'utf8')) || {};
  const normalizedUrl = normalizeUrl(data.url);
  const shortUrl = normalizedUrl.replace(/^https?:\/\/(www\.)?/, '');
  if (!doc[shortUrl]) { // Check if URL already exists
    doc[shortUrl] = [{ ...data }];
    fs.writeFileSync(filePath, yaml.dump(doc));
    console.log('Added new entry:', data);
  } else {
    console.log('Entry already exists for URL:', data.url);
  }
};

// Generate a random day of the week
const getRandomDay = () => {
  return weekdays[Math.floor(Math.random() * weekdays.length)];
};

const processUrl = async (url) => {
  const yamlPath = 'unlighthouse-sites.yml';
  const normalizedUrl = normalizeUrl(url);
  const shortUrl = normalizedUrl.replace(/^https?:\/\/(www\.)?/, '');
  const existingEntries = yaml.load(fs.readFileSync(yamlPath, 'utf8')) || {};
  console.log('Existing entries in YAML:', existingEntries);

  if (existingEntries[shortUrl]) {
    console.log('Entry already exists for URL:', shortUrl);
    console.log('A new spreadsheet was not created.');
    console.log('A new YAML entry was not created.');
    return;
  }

  const urlData = await checkUrl(url);
  console.log('URL data:', urlData);
  if (!urlData) return;

  const auth = await authenticateGoogleSheets();
  if (!auth) {
    console.error('Failed to authenticate with Google Sheets.');
    return;
  }

  const templateId = '1UVyn_LPLCFqrXORqNqwSUvrkZtrmXUYUErbVZtxc5Tw'; // Your template ID
  const copyData = await createFromTemplate(auth, templateId, urlData.title);

  if (!copyData) {
    console.error('Failed to create a new sheet from template.');
    return;
  }

  const newData = {
    url: urlData.url,
    name: urlData.title,
    sheet_id: copyData.id,
    sheet_url: `https://docs.google.com/spreadsheets/d/${copyData.id}/edit`,
    start_date: getRandomDay(), // Set a random day
    max: 500
  };
  updateYAML(yamlPath, newData);
};

// Main function to parse arguments and process URLs or files
const main = () => {
  program.parse(process.argv);
  const options = program.opts();
  if (options.url) {
    processUrl(options.url);
  } else if (options.file) {
    const content = fs.readFileSync(options.file, 'utf8');
    const records = parse(content, { columns: false });
    records.forEach(record => {
      const url = record[0].trim();
      processUrl(url);
    });
  }
};

main();
