# Automated Stock Screener for ChartInk



## 🚀 Overview

This project is a fully automated, serverless Python script that scrapes stock data from custom screeners on [ChartInk](https://chartink.com/). It runs on a monthly schedule using GitHub Actions, extracts the data, and saves it to a neatly formatted Google Sheet for further analysis.

It was built to be **robust**, **scalable**, and **maintainable**, serving as a powerful tool for personal investment analysis and a strong portfolio piece demonstrating skills in RPA, data scraping, and cloud automation.

---

## ✨ Features

- **Automated Scraping**: Uses Playwright to reliably scrape data from dynamic, JavaScript-heavy websites.
- **Scheduled Execution**: Leverages GitHub Actions for cron-based scheduling, running automatically on the first day of every month.
- **Concurrent Processing**: Scrapes multiple scanner URLs simultaneously for maximum speed and efficiency.
- **Organized Data Output**: Saves data to a Google Sheet, creating a new tab for each month and applying professional formatting (bolding, column resizing, timestamps) for readability.
- **Robust & Resilient**: Implements automatic retry logic to handle temporary network failures.
- **Maintainable Codebase**: The project is logically separated into modules for configuration, scraping, and sheet manipulation, making it easy to extend.
- **Secure**: All sensitive credentials (like Google API keys) are handled securely using GitHub Secrets.

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Web Scraping**: Playwright
- **Data Handling**: Pandas
- **Automation/CI/CD**: GitHub Actions
- **Database**: Google Sheets API (`gspread` & `gspread-formatting`)

---

## ⚙️ Setup and Usage

Follow these steps to get the automation running in your own environment.

### 1. Prerequisites

- A GitHub account.
- A Google Cloud Platform account with a project created.
- Python 3.10 or higher installed locally.

### 2. Google Sheets API Setup

1.  **Enable APIs**: In your Google Cloud project, enable the **Google Drive API** and the **Google Sheets API**.
2.  **Create Service Account**:
    - Navigate to "IAM & Admin" > "Service Accounts".
    - Create a new service account with the **Editor** role.
    - Create a JSON key for this account and download the file.
3.  **Rename Key**: Rename the downloaded JSON file to `credentials.json` and place it in the root of your project folder.
4.  **Share Google Sheet**:
    - Create a new Google Sheet (e.g., "Trading Automation").
    - Open `credentials.json`, copy the `client_email` address.
    - Share the Google Sheet with this email address, giving it **Editor** permissions.

### 3. Local Project Setup

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/trading-automation.git](https://github.com/your-username/trading-automation.git)
    cd trading-automation
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Browsers**: Download the necessary browser binaries for Playwright.
    ```bash
    playwright install --with-deps firefox
    ```
4.  **Configure Scanners**: Open `config.py` and update the `SCANNER_MAPPING` dictionary with your desired ChartInk URLs and custom names.

### 4. Running Locally

To test the script on your local machine, run:
```bash
python main.py
```
This will use your local `credentials.json` file.

### 5. GitHub Actions Automation Setup

1.  **Push to GitHub**: Make sure your project, including the `.github/workflows/scheduled_scrape.yml` file, is pushed to your GitHub repository. Ensure your `credentials.json` is listed in `.gitignore`.
2.  **Add Repository Secrets**:
    - In your GitHub repo, go to **Settings > Secrets and variables > Actions**.
    - Create a new secret named `GCP_CREDENTIALS`. Copy the entire content of your `credentials.json` file and paste it as the value.
    - Create another secret named `SHEET_NAME` and set its value to the name of your Google Sheet (e.g., `Trading Automation`).

The workflow is now configured to run automatically. You can also trigger it manually from the **Actions** tab in your repository to test it.

---

## 📂 Project Structure

```
trading-automation/
├── .github/workflows/          # GitHub Actions workflow
│   └── scheduled_scrape.yml
├── config.py                   # All settings and scanner URLs
├── main.py                     # Main script to orchestrate the automation
├── scraper.py                  # Web scraping logic
├── sheets.py                   # Google Sheets update and formatting logic
├── requirements.txt            # Project dependencies
├── credentials.json            # (Local use only, should be in .gitignore)
└── README.md                   # This file
```
