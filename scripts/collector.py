#!/usr/bin/env python3
import os
import sys
import json
import datetime
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections import Counter

# Configuration
R_WEEKLY_FEED = "https://rweekly.org/atom.xml"
R_BLOGGERS_FEED = "https://www.r-bloggers.com/feed/"

# Topic keywords and categories
CATEGORIES = {
    "R Packages & Tools": [
        "ggplot", "ggplot2", "quarto", "shiny", "tidymodels", "rstats", "bioconductor", 
        "r-package", "dplyr", "tidyverse", "cran", "devtools", "sf", "purrr", "reticulate",
        "rmarkdown", "knitr", "plumber"
    ],
    "Data Science & Reporting": [
        "data science", "machine learning", "data visualization", "analysis", "analytics", 
        "statistics", "modeling", "quarto-report", "dashboard", "regression", "deep learning",
        "forecasting", "eda", "wrangling", "tidy", "r-bloggers", "tutorial", "reporting"
    ],
    "AI & Agentic Developer Tools": [
        "mcp", "model context protocol", "codex", "antigravity", "llm", "agents", "ai", 
        "copilot", "openai", "gemini", "claude", "deepseek", "ollama", "prompt", "rag",
        "agentic", "tool", "mcp-server", "chatgpt"
    ]
}

# Tag mapping - words to extract as tags/topics
TAGS_MAP = [
    "ggplot", "quarto", "shiny", "tidymodels", "dplyr", "tidyverse", "cran", "sf",
    "mcp", "codex", "antigravity", "llm", "agents", "ai", "machine learning", "deep learning",
    "dashboard", "tutorial", "visualization", "statistics", "analytics", "quarto-report"
]

def find_elements_by_tag(element, tag_name):
    """Finds all child elements whose tag matches or ends with the given tag_name (ignores namespaces)."""
    results = []
    for el in element.iter():
        if el.tag == tag_name or el.tag.endswith('}' + tag_name):
            results.append(el)
    return results

def get_element_text(element, tag_name, default=""):
    """Gets the text content of the first matching tag, ignoring namespaces."""
    els = find_elements_by_tag(element, tag_name)
    if els and els[0].text:
        return els[0].text.strip()
    return default

def get_element_attribute(element, tag_name, attr_name, default=""):
    """Gets the attribute value of the first matching tag, ignoring namespaces."""
    els = find_elements_by_tag(element, tag_name)
    if els and attr_name in els[0].attrib:
        return els[0].attrib[attr_name].strip()
    return default

def fetch_rss_feed(url):
    """Fetches and parses an RSS or Atom feed, returning a list of standardized items."""
    print(f"Fetching feed: {url}")
    headers = {"User-Agent": "AntigravityCollector/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"Error fetching feed {url}: {e}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"Error parsing XML for {url}: {e}", file=sys.stderr)
        return []

    items = []
    
    # Try parsing as Atom (looks for 'entry')
    entries = find_elements_by_tag(root, "entry")
    if entries:
        print(f"Detected Atom feed for {url} with {len(entries)} entries.")
        for entry in entries:
            title = get_element_text(entry, "title")
            # Atom links can be in <link href="url" />
            link = get_element_attribute(entry, "link", "href")
            if not link:
                link = get_element_text(entry, "id")
            
            summary = get_element_text(entry, "summary")
            if not summary:
                summary = get_element_text(entry, "content", "No description available.")
            
            # Clean HTML if present in summary
            if summary.startswith("<") or "</" in summary:
                # Basic HTML tag stripper
                import re
                summary = re.sub('<[^<]+?>', '', summary).strip()
            
            if len(summary) > 200:
                summary = summary[:197] + "..."

            published = get_element_text(entry, "published") or get_element_text(entry, "updated")
            
            items.append({
                "title": title,
                "url": link,
                "summary": summary,
                "pub_date": published,
                "source": "R Weekly" if "rweekly" in url else "RSS Feed"
            })
    else:
        # Try parsing as RSS (looks for 'item')
        rss_items = find_elements_by_tag(root, "item")
        print(f"Detected RSS feed for {url} with {len(rss_items)} items.")
        for item in rss_items:
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description")
            
            # Basic HTML tag stripper
            if description.startswith("<") or "</" in description:
                import re
                description = re.sub('<[^<]+?>', '', description).strip()
                
            if len(description) > 200:
                description = description[:197] + "..."
                
            pub_date = get_element_text(item, "pubDate")
            
            items.append({
                "title": title,
                "url": link,
                "summary": description,
                "pub_date": pub_date,
                "source": "R-bloggers" if "r-bloggers" in url else "RSS Feed"
            })

    return items

def fetch_github_repos(query, days_ago=14):
    """Queries the public GitHub API for repositories matching query created in the last N days."""
    since_date = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
    url = f"https://api.github.com/search/repositories?q={query}+created:>{since_date}&sort=stars&order=desc"
    print(f"Querying GitHub: {url}")
    
    headers = {
        "User-Agent": "AntigravityCollector/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            repos = data.get("items", [])
            print(f"Found {len(repos)} GitHub repositories for query '{query}'.")
            
            items = []
            for repo in repos:
                desc = repo.get("description") or "No description provided."
                if len(desc) > 200:
                    desc = desc[:197] + "..."
                    
                items.append({
                    "title": f"{repo.get('full_name')} ({repo.get('stargazers_count')} stars)",
                    "url": repo.get("html_url"),
                    "summary": desc,
                    "pub_date": repo.get("created_at"),
                    "source": "GitHub Search"
                })
            return items
    except Exception as e:
        print(f"Error querying GitHub API for '{query}': {e}", file=sys.stderr)
        return []

def analyze_and_score(items, topics_log):
    """Scores and categorizes items, taking into account current topics log to prevent repetition."""
    scored_items = []
    
    # Calculate frequency of existing topics in log to calculate penalties
    topic_counts = Counter(topics_log)
    
    for item in items:
        title_lower = item["title"].lower()
        summary_lower = item["summary"].lower()
        full_text = f"{title_lower} {summary_lower}"
        
        # 1. Classify and score based on keywords
        category_scores = {}
        matched_tags = []
        
        for category, keywords in CATEGORIES.items():
            score = 0
            for kw in keywords:
                # Give higher weight to matches in the title
                if kw in title_lower:
                    score += 5
                if kw in summary_lower:
                    score += 2
            if score > 0:
                category_scores[category] = score
        
        # Identify matching tags for topic logging
        for tag in TAGS_MAP:
            if tag in full_text:
                matched_tags.append(tag)
        
        # Default classification if no keywords match
        if not category_scores:
            if "r-bloggers" in item["source"].lower() or "r weekly" in item["source"].lower():
                category = "R Packages & Tools"
                score = 1
            else:
                category = "Data Science & Reporting"
                score = 1
        else:
            # Pick category with highest score
            category = max(category_scores, key=category_scores.get)
            score = category_scores[category]
            
        # 2. Apply variety penalty if tags are heavily repeated in the history log
        penalty = 0
        for tag in matched_tags:
            count = topic_counts.get(tag, 0)
            if count > 0:
                # Penalize score based on how often this topic has been covered
                penalty += min(count * 0.5, 4) 
                
        final_score = max(score - penalty, 0.1)
        
        scored_items.append({
            "title": item["title"],
            "url": item["url"],
            "summary": item["summary"],
            "source": item["source"],
            "category": category,
            "date_added": datetime.date.today().isoformat(),
            "tags": matched_tags if matched_tags else ["general"],
            "score": final_score,
            "read": False
        })
        
    return scored_items

def main():
    # Configure standard output streams to handle UTF-8 on Windows shells
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
        
    test_mode = "--test" in sys.argv
    print(f"--- Daily Report Collector Running (Test Mode: {test_mode}) ---")
    
    # Path resolution
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    db_path = os.path.join(project_dir, "data", "db.json")
    
    # Silent run guardrails: check if we should run now
    force_mode = "--force" in sys.argv
    if not (test_mode or force_mode):
        now = datetime.datetime.now()
        today_str = datetime.date.today().isoformat()
        
        report_already_exists = False
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    db_temp = json.load(f)
                    reports = db_temp.get("reports", [])
                    if reports and reports[0].get("date") == today_str:
                        report_already_exists = True
            except Exception:
                pass
                
        # Only execute automatically if it's after 19:00 (7:00 PM) AND we haven't run today
        if now.hour < 19:
            print(f"Silent run skipped: Current hour is {now.strftime('%H:%M')}, which is before the 19:00 window.")
            sys.exit(0)
            
        if report_already_exists:
            print(f"Silent run skipped: Today's briefing ({today_str}) has already been generated successfully.")
            sys.exit(0)
            
    # 1. Load Database
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
        except Exception as e:
            print(f"Error loading database {db_path}: {e}", file=sys.stderr)
            db = {"topics_log": [], "historical_items": [], "reports": []}
    else:
        db = {"topics_log": [], "historical_items": [], "reports": []}
        
    existing_urls = {item["url"] for item in db.get("historical_items", [])}
    topics_log = db.get("topics_log", [])
    
    # 2. Fetch Data Sourcing
    all_raw_items = []
    
    # RSS Feeds
    all_raw_items.extend(fetch_rss_feed(R_WEEKLY_FEED))
    all_raw_items.extend(fetch_rss_feed(R_BLOGGERS_FEED))
    
    # GitHub Search (querying R packages and MCP servers)
    all_raw_items.extend(fetch_github_repos("topic:r", days_ago=10))
    all_raw_items.extend(fetch_github_repos("mcp-server", days_ago=14))
    all_raw_items.extend(fetch_github_repos("context-protocol", days_ago=14))
    
    # 3. Strictly Deduplicate by URL/Title
    new_items = []
    seen_titles = set()
    for item in all_raw_items:
        # Check URL duplication
        if item["url"] in existing_urls:
            continue
        # Check title duplication in current batch
        title_norm = item["title"].strip().lower()
        if title_norm in seen_titles:
            continue
        seen_titles.add(title_norm)
        new_items.append(item)
        
    print(f"Fetched {len(all_raw_items)} total items. Found {len(new_items)} brand new items after strict deduplication.")
    
    if not new_items:
        print("No new items discovered today. Skipping report generation.")
        return
        
    # 4. Score and Categorize
    scored_candidates = analyze_and_score(new_items, topics_log)
    
    # Group candidates by category
    categorized = {cat: [] for cat in CATEGORIES.keys()}
    for item in scored_candidates:
        categorized[item["category"]].append(item)
        
    # 5. Compile daily report
    report_items = []
    new_topics = []
    
    print("\n--- Daily Curation Rankings ---")
    for category, items in categorized.items():
        # Sort items in this category by score descending
        items.sort(key=lambda x: x["score"], reverse=True)
        print(f"\nCategory: {category} ({len(items)} candidates)")
        
        # Take the top 2 items from each category to keep it compact and manageable
        selected = items[:2]
        for idx, item in enumerate(selected):
            print(f"  [{idx+1}] Score: {item['score']:.1f} | {item['title']} ({item['source']})")
            # Generate a unique ID
            timestamp = int(datetime.datetime.now().timestamp()) + len(report_items)
            item["id"] = f"item_{timestamp}"
            report_items.append(item)
            new_topics.extend(item["tags"])
            
    if not report_items:
        print("No high-quality scored items selected today.")
        return
        
    # Draft a short editorial summary
    editorial = f"Briefing compiled on {datetime.date.today().strftime('%B %d, %Y')}. "
    ai_tools = [item["title"].split(" - ")[0] for item in report_items if item["category"] == "AI & Agentic Developer Tools"]
    r_tools = [item["title"].split(" - ")[0] for item in report_items if item["category"] == "R Packages & Tools"]
    
    summary_parts = []
    if r_tools:
        summary_parts.append(f"highlights new R packages and features like {', '.join(r_tools[:2])}")
    if ai_tools:
        summary_parts.append(f"explores cutting-edge AI integrations including {', '.join(ai_tools[:2])}")
        
    if summary_parts:
        editorial += "Today's selection " + " and ".join(summary_parts) + "."
    else:
        editorial += "A curated list of data science tools and updates is ready."
        
    report = {
        "date": datetime.date.today().isoformat(),
        "editorial_summary": editorial,
        "items": [item["id"] for item in report_items]
    }
    
    # 6. Save or print results
    if test_mode:
        print("\n=== TEST RUN REPORT OUTPUT (Not Saved) ===")
        print(json.dumps(report, indent=2))
        print("\nCurated Items:")
        print(json.dumps(report_items, indent=2))
    else:
        # Append report items to historical_items
        db["historical_items"].extend(report_items)
        
        # Prepend report to reports timeline
        db["reports"].insert(0, report)
        
        # Append unique new topics to topics log
        for topic in new_topics:
            if topic != "general" and topic not in db["topics_log"]:
                db["topics_log"].append(topic)
                
        # Keep topics log constrained to avoid infinite growth (e.g. max 100 most recent topics)
        if len(db["topics_log"]) > 100:
            db["topics_log"] = db["topics_log"][-100:]
            
        try:
            # Ensure folder exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            print(f"\nSuccess! Successfully compiled report with {len(report_items)} items and saved to {db_path}.")
        except Exception as e:
            print(f"Error saving to database: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
