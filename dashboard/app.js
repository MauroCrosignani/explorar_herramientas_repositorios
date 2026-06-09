// Application State
let db = null;
let activeView = 'latest'; // 'latest' or 'history'
let selectedReportDate = null;
let searchQuery = '';
let selectedTopic = null;

// DOM Elements
const elTimelineList = document.getElementById('timeline-list');
const elTopicCloud = document.getElementById('topic-cloud');
const elReportDate = document.getElementById('report-date');
const elReportLatestBadge = document.getElementById('report-latest-badge');
const elReportSummary = document.getElementById('report-summary');
const elSearchInput = document.getElementById('search-input');
const elSearchClearBtn = document.getElementById('search-clear-btn');

const elStackR = document.getElementById('stack-r');
const elStackDS = document.getElementById('stack-ds');
const elStackAI = document.getElementById('stack-ai');

const elCountR = document.getElementById('count-r');
const elCountDS = document.getElementById('count-ds');
const elCountAI = document.getElementById('count-ai');

const elViewReport = document.getElementById('view-report');
const elViewHistory = document.getElementById('view-history');
const elHistoryGrid = document.getElementById('history-cards-grid');
const elHistoryTotalCount = document.getElementById('history-total-count');

// Navigation Tabs
const btnLatest = document.getElementById('btn-latest');
const btnHistory = document.getElementById('btn-history');

// Filters for History View
const selectFilterCategory = document.getElementById('filter-category');
const selectFilterReadStatus = document.getElementById('filter-read-status');
const btnMarkAllRead = document.getElementById('btn-mark-all-read');

// Initial Load
document.addEventListener('DOMContentLoaded', async () => {
  await loadDatabase();
  setupEventListeners();
  initLucide();
});

// Load DB from local server
async function loadDatabase() {
  try {
    // Relative fetch to go up one folder from dashboard/ index
    const response = await fetch('../data/db.json');
    if (!response.ok) throw new Error('Database file failed to load.');
    db = await response.json();
    
    // Merge with browser's localStorage read states (enables free static cloud hosting support)
    const localReadStates = JSON.parse(localStorage.getItem('briefing_read_states') || '{}');
    if (db.historical_items) {
      db.historical_items.forEach(item => {
        if (localReadStates[item.id] !== undefined) {
          item.read = localReadStates[item.id];
        }
      });
    }
    
    // Set initial selected date to the latest compiled report
    if (db.reports && db.reports.length > 0) {
      selectedReportDate = db.reports[0].date;
    }
    
    renderApp();
  } catch (error) {
    console.error('Error loading database:', error);
    showErrorMessage();
  }
}

// Global UI Rendering Router
function renderApp() {
  if (!db) return;
  
  renderSidebarTimeline();
  renderSidebarTopics();
  
  if (activeView === 'latest') {
    renderReportView();
  } else {
    renderHistoryView();
  }
  
  initLucide();
}

// Render Timeline Sidebar
function renderSidebarTimeline() {
  if (!db.reports || db.reports.length === 0) {
    elTimelineList.innerHTML = '<p class="section-desc">No briefings generated yet.</p>';
    return;
  }
  
  elTimelineList.innerHTML = '';
  db.reports.forEach((report, idx) => {
    const isSelected = report.date === selectedReportDate;
    
    const div = document.createElement('div');
    div.className = `timeline-item ${isSelected && activeView === 'latest' ? 'active' : ''}`;
    div.dataset.date = report.date;
    
    // Format Date for timeline (e.g. May 30)
    const d = new Date(report.date + 'T00:00:00');
    const formattedDate = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    div.innerHTML = `
      <span>${formattedDate} Briefing</span>
      ${idx === 0 ? '<span class="timeline-badge">Latest</span>' : ''}
    `;
    
    div.addEventListener('click', () => {
      activeView = 'latest';
      selectedReportDate = report.date;
      btnLatest.classList.add('active');
      btnHistory.classList.remove('active');
      
      // Clear tag filters when switching to a direct daily briefing
      selectedTopic = null;
      
      renderApp();
    });
    
    elTimelineList.appendChild(div);
  });
}

// Render Floating Topic Cloud Sidebar
function renderSidebarTopics() {
  if (!db.topics_log || db.topics_log.length === 0) {
    elTopicCloud.innerHTML = '<p class="section-desc">No topics logged yet.</p>';
    return;
  }
  
  elTopicCloud.innerHTML = '';
  db.topics_log.forEach(topic => {
    const isSelected = selectedTopic === topic;
    const btn = document.createElement('button');
    btn.className = `topic-tag ${isSelected ? 'active' : ''}`;
    btn.textContent = `#${topic}`;
    
    btn.addEventListener('click', () => {
      if (selectedTopic === topic) {
        // Toggle off
        selectedTopic = null;
      } else {
        selectedTopic = topic;
        
        // If we select a topic, automatically transition to History View 
        // because topic filtering query spans the entire database history
        if (activeView !== 'history') {
          activeView = 'history';
          btnHistory.classList.add('active');
          btnLatest.classList.remove('active');
        }
      }
      renderApp();
    });
    
    elTopicCloud.appendChild(btn);
  });
}

// Render Daily Report Curation view
function renderReportView() {
  elViewReport.classList.add('active');
  elViewHistory.classList.remove('active');
  
  if (!db.reports || db.reports.length === 0) {
    elReportSummary.textContent = "No daily curation briefings have been created yet. Set up your daily schedule or trigger collector.py to populate listings.";
    return;
  }
  
  const report = db.reports.find(r => r.date === selectedReportDate);
  if (!report) {
    elReportSummary.textContent = "Selected briefing report not found.";
    return;
  }
  
  // Update header and date labels
  const dateObj = new Date(report.date + 'T00:00:00');
  elReportDate.textContent = dateObj.toLocaleDateString('en-US', { 
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
  });
  
  // Show "Latest" tag pill only on the absolute newest briefing
  if (report.date === db.reports[0].date) {
    elReportLatestBadge.style.display = 'inline-flex';
  } else {
    elReportLatestBadge.style.display = 'none';
  }
  
  elReportSummary.textContent = report.editorial_summary;
  
  // Group daily items by category
  const reportItems = db.historical_items.filter(item => report.items.includes(item.id));
  
  const itemsByCat = {
    "R Packages & Tools": [],
    "Data Science & Reporting": [],
    "AI & Agentic Developer Tools": []
  };
  
  reportItems.forEach(item => {
    if (itemsByCat[item.category]) {
      itemsByCat[item.category].push(item);
    } else {
      // Fallback
      itemsByCat["Data Science & Reporting"].push(item);
    }
  });
  
  // Render stacks
  renderCardStack(itemsByCat["R Packages & Tools"], elStackR, elCountR, 'R');
  renderCardStack(itemsByCat["Data Science & Reporting"], elStackDS, elCountDS, 'DS');
  renderCardStack(itemsByCat["AI & Agentic Developer Tools"], elStackAI, elCountAI, 'AI');
}

// Render Grid of Curations in a specific Category Stack
function renderCardStack(items, container, countLabel, themeKey) {
  // Apply Search filter inside current report view if query exists
  let filteredItems = items;
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    filteredItems = items.filter(item => 
      item.title.toLowerCase().includes(q) || 
      item.summary.toLowerCase().includes(q) ||
      item.tags.some(tag => tag.toLowerCase().includes(q))
    );
  }
  
  countLabel.textContent = `${filteredItems.length} curated`;
  container.innerHTML = '';
  
  if (filteredItems.length === 0) {
    container.innerHTML = `
      <div class="no-results-small" style="text-align:center; padding:20px; font-size:12px; color:var(--text-muted); border: 1px dashed var(--border-glass); border-radius:12px;">
        No items matching filters.
      </div>
    `;
    return;
  }
  
  filteredItems.forEach(item => {
    const card = createCardElement(item, themeKey);
    container.appendChild(card);
  });
}

// Render Historical Grid database view
function renderHistoryView() {
  elViewReport.classList.remove('active');
  elViewHistory.classList.add('active');
  
  let items = db.historical_items || [];
  
  // 1. Apply category filter select
  const catFilter = selectFilterCategory.value;
  if (catFilter !== 'all') {
    items = items.filter(item => item.category === catFilter);
  }
  
  // 2. Apply status filter select
  const readFilter = selectFilterReadStatus.value;
  if (readFilter === 'read') {
    items = items.filter(item => item.read === true);
  } else if (readFilter === 'unread') {
    items = items.filter(item => item.read === false);
  }
  
  // 3. Apply floating active Topic Tag Filter
  if (selectedTopic) {
    items = items.filter(item => item.tags.includes(selectedTopic));
  }
  
  // 4. Apply Global Search Query
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    items = items.filter(item => 
      item.title.toLowerCase().includes(q) || 
      item.summary.toLowerCase().includes(q) ||
      item.tags.some(tag => tag.toLowerCase().includes(q))
    );
  }
  
  elHistoryTotalCount.textContent = `${items.length} items total`;
  elHistoryGrid.innerHTML = '';
  
  if (items.length === 0) {
    elHistoryGrid.innerHTML = `
      <div class="no-results">
        <i data-lucide="folder-open"></i>
        <h3>No curated tools found</h3>
        <p>Try clearing your search filters, query string, or topic tags to expand your search.</p>
      </div>
    `;
    return;
  }
  
  items.forEach(item => {
    // Determine card category accent theme
    let themeKey = 'DS';
    if (item.category === "R Packages & Tools") themeKey = 'R';
    if (item.category === "AI & Agentic Developer Tools") themeKey = 'AI';
    
    const card = createCardElement(item, themeKey);
    elHistoryGrid.appendChild(card);
  });
}

// Helper to create HTML Card elements
function createCardElement(item, themeKey) {
  const card = document.createElement('div');
  card.className = `card card-theme-${themeKey.toLowerCase()} ${item.read ? 'read' : ''}`;
  card.dataset.id = item.id;
  
  // Format Date added label
  const dateObj = new Date(item.date_added + 'T00:00:00');
  const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  
  // Extract fields and handle highlights if search matches
  let titleHTML = escapeHTML(item.title);
  let summaryHTML = escapeHTML(item.summary);
  
  if (searchQuery) {
    titleHTML = highlightText(titleHTML, searchQuery);
    summaryHTML = highlightText(summaryHTML, searchQuery);
  }
  
  // Source badge icon
  let sourceIcon = 'external-link';
  if (item.source.toLowerCase().includes('github')) sourceIcon = 'git-pull-request';
  
  card.innerHTML = `
    <div class="card-top">
      <a href="${item.url}" target="_blank" class="source-badge">
        <i data-lucide="${sourceIcon}"></i>
        <span>${escapeHTML(item.source)}</span>
      </a>
      <button class="action-check" title="Toggle read state">
        <i data-lucide="${item.read ? 'check-square' : 'square'}"></i>
      </button>
    </div>
    
    <h4 class="card-title">
      <a href="${item.url}" target="_blank">${titleHTML}</a>
    </h4>
    
    <p class="card-desc">${summaryHTML}</p>
    
    <div class="card-tags">
      <span class="card-tag" style="background:rgba(255,255,255,0.01); border-color:transparent; font-weight:700;">${dateStr}</span>
      ${item.tags.map(tag => `<span class="card-tag">${escapeHTML(tag)}</span>`).join('')}
    </div>
  `;
  
  // Event: Toggle read/unread state
  const btnCheck = card.querySelector('.action-check');
  btnCheck.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const newReadState = !item.read;
    item.read = newReadState;
    
    // Smooth transition toggle classes
    if (newReadState) {
      card.classList.add('read');
      btnCheck.innerHTML = '<i data-lucide="check-square"></i>';
    } else {
      card.classList.remove('read');
      btnCheck.innerHTML = '<i data-lucide="square"></i>';
    }
    
    initLucide();
    
    // Save state back to server database
    await toggleReadStateOnServer(item.id, newReadState);
    
    // In Report view, toggle read doesn't re-render stack to avoid annoying shift in layout
    // but in History view, if filtered to unread/read, it needs re-rendering to filter out!
    if (activeView === 'history' && selectFilterReadStatus.value !== 'all') {
      renderApp();
    }
  });
  
  return card;
}

// POST API call to persist read state (Hybrid: uses Server on Localhost, LocalStorage on Web/Cloud)
async function toggleReadStateOnServer(itemId, isRead) {
  // Always update browser's localStorage as a fallback / static host support
  const localReadStates = JSON.parse(localStorage.getItem('briefing_read_states') || '{}');
  localReadStates[itemId] = isRead;
  localStorage.setItem('briefing_read_states', JSON.stringify(localReadStates));

  // If running on local server, also write back to db.json
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  if (isLocalhost) {
    try {
      const response = await fetch('/api/toggle-read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: itemId, read: isRead })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update read state on local server.');
      }
    } catch (error) {
      console.error('Error persisting read state to server:', error);
    }
  }
}

// Set up UI Event Listeners
function setupEventListeners() {
  // Navigation
  btnLatest.addEventListener('click', () => {
    activeView = 'latest';
    btnLatest.classList.add('active');
    btnHistory.classList.remove('active');
    renderApp();
  });
  
  btnHistory.addEventListener('click', () => {
    activeView = 'history';
    btnHistory.classList.add('active');
    btnLatest.classList.remove('active');
    renderApp();
  });
  
  // History Category Filters
  selectFilterCategory.addEventListener('change', () => {
    renderApp();
  });
  
  selectFilterReadStatus.addEventListener('change', () => {
    renderApp();
  });
  
  // Bulk mark all read
  btnMarkAllRead.addEventListener('click', async () => {
    let itemsToUpdate = db.historical_items;
    
    // Narrow down based on active filters
    const catFilter = selectFilterCategory.value;
    if (catFilter !== 'all') {
      itemsToUpdate = itemsToUpdate.filter(item => item.category === catFilter);
    }
    if (selectedTopic) {
      itemsToUpdate = itemsToUpdate.filter(item => item.tags.includes(selectedTopic));
    }
    
    // Select only those which are unread
    const unreadItems = itemsToUpdate.filter(item => !item.read);
    
    if (unreadItems.length === 0) return;
    
    // Update locally
    unreadItems.forEach(item => { item.read = true; });
    renderApp();
    
    // Send batch requests to server
    for (const item of unreadItems) {
      await toggleReadStateOnServer(item.id, true);
    }
  });
  
  // Live Global Search
  elSearchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.trim();
    
    if (searchQuery) {
      elSearchClearBtn.style.display = 'block';
      // Automatically shift to history/search view when user starts searching globally
      // to display matching records from the entire archive
      if (activeView !== 'history') {
        activeView = 'history';
        btnHistory.classList.add('active');
        btnLatest.classList.remove('active');
      }
    } else {
      elSearchClearBtn.style.display = 'none';
    }
    
    renderApp();
  });
  
  // Clear search button
  elSearchClearBtn.addEventListener('click', () => {
    elSearchInput.value = '';
    searchQuery = '';
    elSearchClearBtn.style.display = 'none';
    renderApp();
  });
}

// Utility: Re-instantiate Lucide SVG Icons in newly rendered HTML
function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// Utility: Basic string HTML escaping
function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Utility: Dynamic highlighting of matching search text
function highlightText(text, search) {
  if (!search) return text;
  const escapedSearch = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'); // Escape regex chars
  const regex = new RegExp(`(${escapedSearch})`, 'gi');
  return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

// Show Error Message on load failure
function showErrorMessage() {
  const container = document.querySelector('.app-container');
  container.innerHTML = `
    <div style="grid-column: 1 / -1; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; padding: 40px; text-align:center;">
      <i data-lucide="alert-triangle" style="width: 64px; height: 64px; color: var(--accent-ai); margin-bottom: 24px;"></i>
      <h2 style="font-family: var(--font-display); font-size:28px; margin-bottom: 12px;">Local Server Connection Offline</h2>
      <p style="color: var(--text-secondary); max-width: 500px; line-height: 1.6; margin-bottom: 24px;">
        To browse your daily briefings and perform dynamic interactive read/unread toggles, please launch the application server using <code style="background:rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">python server.py</code>.
      </p>
      <button onclick="window.location.reload()" style="background:var(--accent-r); border:none; padding:12px 24px; border-radius:8px; color:white; font-weight:600; cursor:pointer;">
        Retry Connection
      </button>
    </div>
  `;
  initLucide();
}
