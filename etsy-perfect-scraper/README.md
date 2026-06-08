# Etsy Perfect Collection Scraper (Etsy Perfect Scraper)

A robust, premium Etsy scaper powered by **Playwright** that automatically archives user favorites, extracts high-resolution product designs, and generates clean analytics, complete with an automated video recording of the scraping session.

## 🚀 Features

- **🌐 Dynamic Playwright Browser Scraper**: Automates modern chromium browsers to render JavaScript-heavy Etsy listing pages seamlessly.
- **🖼️ High-Resolution Image Extraction**: Uses custom URL processing heuristics to bypass default thumbnails and fetch ultra-high-resolution original product images (`il_fullxfull`).
- **📂 Structured Archival Directory System**: Organizes extracted designs into sanitized folders containing:
  - High-res product images (`image_1.jpg`)
  - Standalone text metadata files (`page_text.txt`)
  - Direct links to the listing (`product_url.txt`)
- **📊 Auto-Generated Portfolio Analytics**: Synthesizes collection summaries (`analysis.txt`) and unified listing link lists (`links.txt`).
- **🎥 Scraping Session Screen Recording**: Records browser interaction dynamically, converting/saving the session as a compressed `process_recording.mp4` using `ffmpeg` (with standard `.webm` fallback).

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Browser Automation**: `Playwright` (Chromium engine)
- **Video/Media Conversion**: `ffmpeg` (optional fallback to dynamic renaming)
- **Libraries**: `urllib`, `subprocess`, `os`

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd etsy-perfect-scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

3. **Configure output & target**:
   - Edit `scraper.py` to change your target `TARGET_URL` (Etsy favorites/people URL) and directory output paths.

4. **Run the scraper**:
   ```bash
   python scraper.py
   ```

---

*Designed and developed with 💙 by Emirhan Kaya.*
