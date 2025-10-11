<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-Playwright-green?style=for-the-badge&logo=microsoft-edge" alt="Framework">
  <img src="https://img.shields.io/badge/CI/CD-GitHub_Actions-black?style=for-the-badge&logo=githubactions" alt="CI/CD">
  <img src="https://img.shields.io/badge/Database-Google_Sheets-brightgreen?style=for-the-badge&logo=google-sheets" alt="Database">
</div>

<h1 align="center">🚀 Automated ChartInk Stock Screener 🚀</h1>

<p align="center">
  A robust, serverless Python automation that scrapes custom stock screeners from <a href="https://chartink.com/">ChartInk</a>,
  runs on a monthly schedule via GitHub Actions, and delivers beautifully formatted data directly to your Google Sheet.
</p>

---

## ✨ Key Features

- **🤖 Fully Automated Scraping**: Leverages **Playwright** to flawlessly handle dynamic, JavaScript-heavy websites, ensuring reliable data extraction every time.
- **🗓️ Scheduled & On-Demand Execution**: Runs automatically on the first day of every month using a CRON-based **GitHub Actions** workflow. It can also be triggered manually for instant runs.
- **⚡ Concurrent Processing**: Scrapes multiple ChartInk scanner URLs **simultaneously**, maximizing speed and efficiency.
- **📊 Professional Data Output**: Organizes scraped data in a **Google Sheet**, creating a new tab for each month. It applies professional formatting like bold headers, column resizing, and conditional coloring for positive/negative values.
- **🛡️ Secure Credential Management**: All sensitive information, like Google Cloud API keys, is managed securely using **GitHub Secrets**, never exposing them in the codebase.
- **🔄 Resilient & Fault-Tolerant**: Implements an automatic **retry mechanism** to gracefully handle temporary network failures or timeouts, ensuring the workflow completes successfully.
- **🧩 Modular & Maintainable**: The codebase is logically structured into distinct services for scraping, sheet manipulation, and configuration, making it easy to understand, maintain, and extend.

---

## 🛠️ Tech Stack

| Category          | Technology                                                                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Language** | `Python 3.10+`                                                                                                                                                         |
| **Web Scraping** | `Playwright`                                                                                                                                                           |
| **Data Handling** | `Pandas`                                                                                                                                                               |
| **Automation** | `GitHub Actions`                                                                                                                                                       |
| **Database** | `Google Sheets API` (`gspread`, `gspread-formatting`)                                                                                                                    |
| **Tooling** | `pip`, `python-dotenv`                                                                                                                                                   |

---

## ⚙️ Setup and Usage

Follow these steps to configure and run the automation in your own GitHub repository.

### 1. Google Cloud & Sheets Setup

1.  **Enable APIs**: In your Google Cloud project, enable the **Google Drive API** and the **Google Sheets API**.
2.  **Create Service Account**:
    - Navigate to `IAM & Admin` > `Service Accounts`.
    - Create a new service account with the **Editor** role.
    - Generate a **JSON key** for this account and download the file. This file contains your credentials.
3.  **Share Google Sheet**:
    - Create a new Google Sheet (e.g., "Trading Automation").
    - Open the downloaded JSON key file, find the `client_email` address, and copy it.
    - Share the Google Sheet with this email address, granting it **Editor** permissions.

### 2. GitHub Repository Setup

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/chartink-automation.git](https://github.com/your-username/chartink-automation.git)
    cd chartink-automation
    ```

2.  **Configure Scanners** (Optional):
    - Open `app/core/config.py`.
    - Modify the `scanners` list with your own ChartInk screener names and URLs.

3.  **Add Repository Secrets**:
    - In your GitHub repository, navigate to **Settings > Secrets and variables > Actions**.
    - Create a new secret named `GCP_CREDENTIALS`. Copy the **entire content** of your downloaded JSON key file and paste it as the value.
    - Create another secret named `SHEET_NAME` and set its value to the exact name of your Google Sheet (e.g., `Trading Automation`).

### 3. Running the Automation

The project is now fully configured! The workflow will run automatically based on the schedule in `.github/workflows/scheduled_scrape.yml`.

To run it manually:
1.  Go to the **Actions** tab in your GitHub repository.
2.  Select the **Monthly ChartInk Stock Scraper** workflow.
3.  Click **Run workflow** and then **Run workflow** again.

---

## 📂 Project Structure

The project is organized into a clean, modular structure:
chartink-automation/
├── .github/workflows/
│   └── scheduled_scrape.yml      # GitHub Actions workflow for scheduled execution
├── app/
│   ├── core/
│   │   └── config.py             # All settings, URLs, and environment variables
│   ├── services/
│   │   ├── scraper_service.py    # Logic for web scraping with Playwright
│   │   └── sheets_service.py     # Logic for Google Sheets updates and formatting
│   ├── utils/
│   │   └── logger.py             # Centralized logging setup
│   └── main.py                   # Main script to orchestrate the automation process
├── .gitignore                    # Specifies files to be ignored by Git
├── requirements.txt              # Project dependencies
└── README.md                     # This file

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements or find any issues, feel free to open an issue or submit a pull request.

## 📄 License

This project is open-source and available under the MIT License.
