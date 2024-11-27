
# Alt-Text Scan Tool

A Python script for scanning websites to evaluate the quality of `alt` text in images and generate actionable accessibility suggestions.

---

## Overview

This tool crawls websites or parses their sitemap to collect images and analyze their `alt` attributes for accessibility compliance. It generates a CSV file summarizing issues, suggestions, and metadata for each image.

---

## Features

- **Crawl Websites**: Analyze images from websites either by crawling pages directly or parsing their sitemap.
- **Accessibility Checks**: Detect missing, meaningless, or excessively long `alt` text.
- **Readability Analysis**: Assess readability for `alt` text over 25 characters.
- **Rate Limiting**: Throttle requests to avoid overloading servers.
- **CSV Reports**: Save analysis results to a CSV file.
- **New Features**:
  - Added support for crawling without relying on `sitemap.xml` using the `--crawl_only` option.
  - Readability analysis is now performed only on `alt` text longer than 25 characters.
  - Improved handling of nested sitemaps with recursive parsing.
  - Enhanced suggestions for WCAG compliance, including identifying decorative images and overly verbose `alt` text.

---

## Installation

### Prerequisites

1. Python 3.10 or later.
2. Install the required Python libraries:

   ```bash
   pip install -r requirements.txt
   ```

   **Required Libraries**:
   - `requests`
   - `bs4` (BeautifulSoup)
   - `pandas`
   - `tqdm`
   - `textstat`
   - `textblob`

---

## Usage

### Command-Line Arguments

| Argument              | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `domain`             | The base domain to analyze (e.g., `https://example.com`).                   |
| `--sample_size`      | Number of URLs to sample from the sitemap (default: 100).                   |
| `--throttle`         | Throttle delay in seconds between requests (default: 1).                   |
| `--crawl_only`       | Skip sitemap parsing and start crawling directly (default: `False`).        |

---

### Examples

#### 1. Analyze a Site Using the Sitemap
```bash
python alt_text_scan.py https://example.com --sample_size 200 --throttle 2
```

This will:
- Parse `https://example.com/sitemap.xml` to find URLs.
- Sample up to 200 URLs for analysis.
- Throttle requests with a 2-second delay.

#### 2. Crawl a Site Directly
```bash
python alt_text_scan.py https://example.com --sample_size 200 --throttle 2 --crawl_only
```

This will:
- Bypass `sitemap.xml`.
- Crawl the site starting from the homepage.
- Analyze up to 200 pages.

---

## Output

The script generates a CSV file named after the domain being analyzed, e.g., `example.com_images.csv`. Each row corresponds to an image and contains:

| Column             | Description                                                                      |
|--------------------|----------------------------------------------------------------------------------|
| `Image_url`       | The URL of the image.                                                           |
| `Alt_text`        | The `alt` attribute of the image (if available).                                |
| `Title`           | The `title` attribute of the image (if available).                              |
| `Count`           | The number of times the image appears.                                          |
| `Source_URLs`     | Pages where the image was found.                                                |
| `Size (KB)`       | The size of the image in kilobytes.                                             |
| `Suggestions`     | Recommendations for improving the `alt` text based on WCAG standards.           |

---

## Key Accessibility Checks

1. **Missing or Empty `alt` Text**:
   - Detects images with no `alt` attribute or empty `alt` values.
   - Suggests adding meaningful descriptions.

2. **Readability Analysis**:
   - Evaluates readability for `alt` text over 25 characters.
   - Suggests simplifying overly complex text.

3. **Text Length**:
   - Flags `alt` text under 25 characters as too short.
   - Flags `alt` text over 250 characters as too verbose.

4. **Meaningless `alt` Text**:
   - Identifies generic or placeholder `alt` text (e.g., "image of", "placeholder").

5. **Large Image Files**:
   - Highlights images over 250 KB as candidates for optimization.

---

## Known Limitations

1. **403 Forbidden Errors**: Some servers may block automated requests. Use `--throttle` to reduce request frequency or adjust headers in the script.
2. **Large Sitemaps**: Parsing deeply nested sitemaps may exceed the recursion depth limit. Use the `--crawl_only` option if necessary.
3. **CAPTCHA Restrictions**: Servers using CAPTCHAs or aggressive rate-limiting may block requests.

---

## Script

Below is the Python script:

```python
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse, urlunparse
import argparse
from tqdm import tqdm
import xml.etree.ElementTree as ET
import random
import time
from collections import defaultdict
import re
from textblob import TextBlob
from readability.readability import Document
from textstat import text_standard
from datetime import datetime

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.tiff', '.avif', '.webp')

# Function definitions
def is_valid_image(url):
    ...

def parse_sitemap(sitemap_url, base_domain, headers=None, depth=3):
    ...

def crawl_site(start_url, max_pages=100, throttle=0):
    ...

def get_relative_url(url, base_domain):
    ...

def get_images(domain, sample_size=100, throttle=0, crawl_only=False):
    ...

def analyze_alt_text(images_df, domain, readability_threshold=8):
    ...

def process_image(img_url, img, page_url, domain, images_data):
    ...

def crawl_page(url, images_data, url_progress, domain, throttle, consecutive_errors):
    ...

# Main function
def main(domain, sample_size=100, throttle=0, crawl_only=False):
    ...
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Crawl a website and collect image data with alt text.")
    parser.add_argument('domain', type=str, help='The domain to crawl (e.g., https://example.com)')
    parser.add_argument('--sample_size', type=int, default=100, help='Number of URLs to sample from the sitemap')
    parser.add_argument('--throttle', type=int, default=1, help='Throttle delay (in seconds) between requests')
    parser.add_argument('--crawl_only', action='store_true', help='Start crawling directly without using the sitemap')
    args = parser.parse_args()
    main(args.domain, args.sample_size, throttle=args.throttle, crawl_only=args.crawl_only)
```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/CivicActions/site-evaluation-tools).

---

## License

This project is licensed under the MIT License.
