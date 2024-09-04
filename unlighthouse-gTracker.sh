#!/bin/zsh
#
# Unlighthouse Google Tracker Script (unlighthouse-gTracker.sh)
#
# Description:
# This script automates the process of scanning websites using the Unlighthouse tool. It reads the URLs 
# scheduled for a specific day of the week from a YAML file, then runs Unlighthouse scans for each URL. 
# The script also handles the cleanup of Chrome Canary processes, logs the start and end times of the 
# script, and logs all output to a specified log file.
#
# Features:
# - Extracts URLs from a YAML configuration file based on the specified day of the week.
# - Runs the Unlighthouse scanner for each URL, logging results and errors.
# - Uses Node.js and manages memory by forcing garbage collection after each run.
# - Closes Chrome Canary and Chrome Helper processes after each scan to prevent resource exhaustion.
# - Logs execution details such as Node.js version, extracted URLs, and start/end times to a log file.
#
# Usage:
# - By default, the script runs for the current day of the week, but a specific day can be provided using 
#   the -d option (e.g., `./unlighthouse-gTracker.sh -d Monday`).
# - The script is intended to be used in a scheduled cron job to automate weekly scans for different URLs.
#
# License:
# This script is licensed under the GNU General Public License v3.0.
# You can redistribute it and/or modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
#

# Log the start time of the script
echo "Script started at $(date)" > /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log

# Close Chrome Canary instances after each run
/usr/bin/pkill -f "Google Chrome Canary"
/usr/bin/pkill -f "Google Chrome Helper"

# Navigate to the project directory
cd /Users/mgifford/CA-Sitemap-Scans

# Log Node.js version
echo "Node.js version:" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
/opt/homebrew/bin/node -v >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log 2>&1

# Default to today's day of the week
day=$(date +%A)

# Check if a day of the week was provided as an argument
while getopts "d:" opt; do
  case $opt in
    d)
      day=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
      exit 1
      ;;
  esac
done

# Convert the day variable to Title Case for comparison
day=$(echo "$day" | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}')

# Log the day being used for the script
echo "Day for scanning: $day" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log

# Print all start_date values to check correctness
echo "All start_date values:" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
yq e ".[] | .[].start_date" unlighthouse-sites.yml >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log 2>&1

# Extract URLs for the specified day
echo "Extracting URLs from YAML for day: $day" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
urls=$(yq e ".[] | .[] | select(.start_date == \"$day\") | .url" unlighthouse-sites.yml 2>> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log)

# Log the extracted URLs
echo "Extracted URLs:" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
echo "$urls" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log

# Function to run a single Unlighthouse process
run_unlighthouse() {
    url=$1
    echo "Processing $url for $day..." >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
    /opt/homebrew/bin/node --expose-gc --max-old-space-size=8096 /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.js --url="$url" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log 2>&1
    if [[ $? -ne 0 ]]; then
        echo "Process for $url failed." >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log
    fi
    # Force garbage collection
    /opt/homebrew/bin/node -e 'if (global.gc) { global.gc(); console.log("Garbage collection complete"); }' >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log 2>&1

    # Close Chrome Canary instances after each run
    /usr/bin/pkill -f "Google Chrome Canary"
    /usr/bin/pkill -f "Google Chrome Helper"
}

# Process URLs one by one
echo "$urls" | while IFS= read -r url; do
    run_unlighthouse "$url"
done

# Log the end time of the script
echo "Script ended at $(date)" >> /Users/mgifford/CA-Sitemap-Scans/unlighthouse-gTracker.log%      
