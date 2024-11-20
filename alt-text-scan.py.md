# Image Analysis Script for Web Accessibility

## Overview

This script analyzes images on a website for accessibility compliance. It identifies issues with alt text and other metadata, providing suggestions to improve accessibility. The script can parse sitemaps or crawl the website manually if a sitemap is unavailable or invalid.

## Features

	•	Crawl websites for image data using sitemaps or manual crawling.
	•	Analyze image metadata, including alt text, title, and size.
	•	Generate detailed suggestions for improving alt text.
	•	Exclude non-HTML content (e.g., PDFs, videos).
	•	Output results to a CSV file with a summary of findings and recommendations.

## Installation

### Prerequisites

Ensure you have Python 3.10 or later installed. Install the following Python libraries:

pip install requests beautifulsoup4 pandas tqdm textblob readability-lxml textstat

## Usage

Running the Script

To run the script, use the following command:

python3.10 alt_scan.py <domain> --sample_size <number>

## Parameters

	•	<domain>: The starting URL for the website (e.g., https://example.com).
	•	--sample_size: Maximum number of unique URLs to crawl (default: 100).

Example

python3.10 alt_scan.py https://www.whitehouse.gov --sample_size 1000

This command crawls up to 1,000 unique pages on the specified domain and analyzes the images found.

## Output

The script generates two files:
	1.	CSV File: <domain>_images.csv
Contains detailed image metadata and suggestions for improving accessibility.
	2.	Console Output:
Provides progress updates and a summary of findings.

CSV Columns

	•	Image_name: The file name of the image.
	•	Image_url: The full URL of the image.
	•	Alt_text: The alt text associated with the image.
	•	Title: The title attribute of the image (if any).
	•	Count: Number of occurrences of the image.
	•	Source_URLs: Pages where the image is found.
	•	Size (KB): Approximate size of the image in kilobytes.
	•	Load_Time (s): Time taken to fetch the image.
	•	Suggestions: Accessibility improvement recommendations.

## Features of Analysis

The script provides actionable suggestions, including:
	•	“Image hidden with no semantic value” if an image is marked with aria-hidden or hidden attributes.
	•	“No alt text provided” for images without alt attributes.
	•	“Check if the SVG file includes a title” for SVGs without meaningful descriptions.
	•	“Decorative image” for images with empty alt attributes.
	•	Suggestions to avoid unnecessary phrases like “A picture of” in alt text.
	•	Readability checks using a customizable threshold.

## Troubleshooting

Invalid or Missing Sitemap

If the sitemap cannot be parsed or is invalid, the script falls back to crawling the website starting from the homepage.

Excluded Files

The script excludes non-HTML content, such as:
	•	Documents (.pdf, .docx, etc.)
	•	Media files (.jpg, .mp4, etc.)
	•	Archives (.zip, .rar, etc.)

## Logging Issues

The script outputs warnings for any URLs it fails to process.

## Contributing

Feel free to submit issues or pull requests to improve this script.

## License

This project is open-source and available under the MIT License.
