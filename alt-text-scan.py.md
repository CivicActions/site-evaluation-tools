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

1. **Python 3.10 or later**.

2. **Install Required Python Libraries**:

Install the required Python libraries using pip3:

Save: Save this content as requirements.txt.
Install: Run `pip3 install -r requirements.txt` in your terminal.

---

## Usage

### Command-Line Arguments

| Argument        | Description                                                          |
| --------------- | -------------------------------------------------------------------- |
| `domain`        | The base domain to analyze (e.g., `https://example.com`).            |
| `--sample_size` | Number of URLs to sample from the sitemap (default: 100).            |
| `--throttle`    | Throttle delay in seconds between requests (default: 1).             |
| `--crawl_only`  | Skip sitemap parsing and start crawling directly (default: `False`). |

---

### Examples

#### 1. Analyze a Site Using the Sitemap

```bash
python3 alt-text-scan.py https://example.com --sample_size 200 --throttle 2
```

This will:

- Parse `https://example.com/sitemap.xml` to find URLs.
- Sample up to 200 URLs for analysis.
- Throttle requests with a 2-second delay.

#### 2. Crawl a Site Directly

```bash
python3 alt-text-scan.py https://example.com --sample_size 200 --throttle 2 --crawl_only
```

This will:

- Bypass `sitemap.xml`.
- Crawl the site starting from the homepage.
- Analyze up to 200 pages.

---

## Output

The script generates a CSV file named after the domain being analyzed, e.g., `example.com_images.csv`. Each row corresponds to an image and contains:

| Column        | Description                                                           |
| ------------- | --------------------------------------------------------------------- |
| `Image_url`   | The URL of the image.                                                 |
| `Alt_text`    | The `alt` attribute of the image (if available).                      |
| `Title`       | The `title` attribute of the image (if available).                    |
| `Count`       | The number of times the image appears.                                |
| `Source_URLs` | Pages where the image was found.                                      |
| `Size (KB)`   | The size of the image in kilobytes.                                   |
| `Suggestions` | Recommendations for improving the `alt` text based on WCAG standards. |

---

## Key Accessibility Checks

1. **Missing or Empty ****************`alt`**************** Text**:

   - Detects images with no `alt` attribute or empty `alt` values.
   - Suggests adding meaningful descriptions.

2. **Readability Analysis**:

   - Evaluates readability for `alt` text over 25 characters.
   - Suggests simplifying overly complex text.

3. **Text Length**:

   - Flags `alt` text under 25 characters as too short.
   - Flags `alt` text over 250 characters as too verbose.

4. **Meaningless ****************`alt`**************** Text**:

   - Identifies generic or placeholder `alt` text (e.g., "image of", "placeholder").

5. **Large Image Files**:

   - Highlights images over 250 KB as candidates for optimization.

---

## Known Limitations

1. **403 Forbidden Errors**: Some servers may block automated requests. Use `--throttle` to reduce request frequency or adjust headers in the script.

2. **Large Sitemaps**: Parsing deeply nested sitemaps may exceed the recursion depth limit. Use the `--crawl_only` option if necessary.

3. **CAPTCHA Restrictions**: Automated tools may trigger CAPTCHA challenges. Human intervention might be needed in such cases.
