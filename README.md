# Briefing.DS 📊🤖

> **A Scheduled Personal Curation System** that gathers new R packages, data science tutorials, and cutting-edge AI/Agentic developer tools (highly optimized for Codex and Antigravity) daily at 7:00 PM, featuring a premium glassmorphic local dashboard.

---

## 🌟 Key Features

1. **Smart Deduplication & Curation**: Strictly filters out duplicates by title and URL across historical records.
2. **Topic Log Guardrails**: Tracks covered tags/topics in a local log database to dynamically penalize redundant topics, ensuring fresh, varied content every day.
3. **No Key Hurdles**: Powered entirely by public RSS feeds (R Weekly, R-bloggers) and the public, unauthenticated GitHub Search API.
4. **Silent Scheduler**: Automatically registers as a silent Windows Scheduled Task that executes daily at 7:00 PM using windowless python execution (`pythonw.exe`).
5. **Interactive Dashboard**: A premium, frosted-glass dark-mode UI with timeline browsing, real-time global search, an active tag cloud, and responsive controls to toggle items as Read/Unread.
6. **Zero Dependencies**: Built entirely with standard library tools (Python 3.x, vanilla CSS, vanilla JS, HTML5).

---

## 📂 Project Directory Structure

```
explorar_herramientas_repositorios/
├── data/
│   └── db.json               # Portable JSON database (historical records & topic logs)
├── scripts/
│   ├── collector.py          # Curation engine: fetches, scores, deduplicates data
│   └── schedule_task.ps1     # PowerShell script to register the Windows Scheduled Task
├── dashboard/
│   ├── index.html            # Premium dashboard interface
│   ├── style.css             # Glassmorphic responsive styling & design tokens
│   └── app.js                # Core frontend interactions, search, filter, and POST sync
├── server.py                 # Double-click launcher (local http server + browser autostart)
└── README.md                 # System documentation & manual
```

---

## 🚀 How to Get Started

### 1. Initialize & Gather Data
First, run a quick collection run to make sure the database is up-to-date and populated:
```powershell
python scripts/collector.py
```
*(Optional: Use `python scripts/collector.py --test` to simulate a run and see rankings in the terminal without modifying your database).*

### 2. Launch the Web Dashboard
Start the lightweight background server:
```powershell
python server.py
```
This will:
* Boot up a local TCP server on port `8000`.
* Listen for interactive POST requests to toggle read/unread status on database items.
* Automatically open your default browser to `http://localhost:8000/dashboard/index.html`.

### 3. Register the Silent Daily Scheduler
To ensure the collector automatically fetches updates at 7:00 PM every day even if you don't have terminals open:
* Right-click `scripts/schedule_task.ps1` and select **Run with PowerShell** (or run it from a standard PowerShell window).
* The script automatically registers a task named **`DailyDataScienceAIExplorer`** inside the standard **Windows Task Scheduler**.

---

## 🛠️ Personalizing Your Curation

You can easily refine and tailor the types of packages and AI tools you receive! Open `scripts/collector.py` and modify the arrays inside `CATEGORIES` to fit your exact stack:

```python
CATEGORIES = {
    "R Packages & Tools": [
        "ggplot", "ggplot2", "quarto", "shiny", "tidymodels", "rstats", "bioconductor", 
        # Add new packages here (e.g. "future", "targets", "gt")
    ],
    "Data Science & Reporting": [
        "data science", "machine learning", "data visualization", "analysis", "analytics", 
        # Add new concepts here (e.g. "nlp", "timeseries", "bayesian")
    ],
    "AI & Agentic Developer Tools": [
        "mcp", "model context protocol", "codex", "antigravity", "llm", "agents", "ai", 
        # Add new LLM/Agent tools here (e.g. "ollama", "langchain")
    ]
}
```

The system will automatically increase scores for articles or repositories matching these terms and place them in the correct column on your dashboard.

---

## 🧪 Technical Implementation Details

* **Interactive Syncing**: When you click the checkmark on a card inside your browser, the dashboard makes a `POST` request to `http://localhost:8000/api/toggle-read`. The Python server parses the target item and updates its state in `data/db.json` asynchronously, keeping data persisted across page reloads.
* **Topic Penalty Algorithm**:
  $$\text{Final Score} = \text{Base Keyword Score} - \sum_{\text{tag} \in \text{matched}} \min(\text{Historical Count} \times 0.5, 4)$$
  This formula applies a smooth mathematical penalty to topics that have been frequently curated, automatically shifting recommendations to less-covered topics when scores are tied.

---

## 🌐 Deploying to the Cloud for Free (Optional)

You can host this dashboard on the internet completely for free using **GitHub Pages** and automate the daily curations using **GitHub Actions**:

### 1. Upload to a GitHub Repository
Run these commands in your project folder to push the files to a new GitHub repository:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/your-repository-name.git
git push -u origin main
```

### 2. Enable GitHub Pages
1. Go to your repository settings on **GitHub.com**.
2. Click **Pages** in the left sidebar menu.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Choose the `main` branch and folder `/(root)`. Click **Save**.
5. Your dashboard will be live at: `https://your-username.github.io/your-repository-name/dashboard/index.html`

### 3. Automatic Daily Cloud Updates
We have included a GitHub Actions workflow file at `.github/workflows/collect.yml`. It will run automatically every day at 22:00 UTC (approx. 7:00 PM local time), run the data collection, and push the updated database to GitHub, which automatically redeploys your web dashboard.
When hosted on GitHub Pages, the dashboard automatically shifts to saving read checkmarks in your browser's **`localStorage`**, so they persist for you without needing a backend database server.
