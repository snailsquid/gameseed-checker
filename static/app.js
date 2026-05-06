/**
 * GAMESEED Participant Checker - pywebview JavaScript
 * Handles UI interactions and API calls to Flask backend
 */

// Store file paths
let mobileFilePath = null;
let pcFilePath = null;

window.currentResults = null;
window.appHistory = [];
let history = [];

// Expose functions immediately
function renderHistory() {
    console.log('renderHistory called, history length:', history.length);
    const historyList = document.getElementById('history-list');
    if (!historyList) {
        console.log('history-list element not found!');
        return;
    }

    if (history.length === 0) {
        historyList.innerHTML = '<div class="history-empty" style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 20px;">No history yet</div>';
        return;
    }

    let html = '';
    for (let i = 0; i < history.length; i++) {
        const entry = history[i];
        const statusClass = entry.verified ? 'history-item-verified' : 'history-item-notverified';
        const statusText = entry.verified ? 'Verified' : 'Not Verify';
        html += `<div class="history-item">
            <div class="history-item-row">
                <div class="history-item-info">
                    <div class="history-item-team">${escapeHtml(entry.team)}</div>
                    <div class="history-item-status">
                        <span class="${statusClass}">${statusText}</span>
                        <span>${entry.category}</span>
                    </div>
                </div>
                <button class="history-delete-btn" onclick="deleteHistoryItem(${i})">×</button>
            </div>
        </div>`;
    }
    historyList.innerHTML = html;
}

function deleteHistoryItem(index) {
    history.splice(index, 1);
    window.appHistory = history;
    renderHistory();
}

function addToHistory(results) {
    const verified = results.filter(r => r.verified);
    if (verified.length === 0) return;

    const teams = {};
    for (const r of verified) {
        const team = r.team || '(No Team)';
        if (!teams[team]) {
            teams[team] = { team, verified: true, category: r.source };
        }
    }

    for (const teamName in teams) {
        history.unshift(teams[team]);
        if (history.length > 50) history.pop();
    }
    window.appHistory = history;

    renderHistory();
}

window.addToHistory = addToHistory;
window.deleteHistoryItem = deleteHistoryItem;
window.renderHistory = renderHistory;

async function selectFile(kind) {
    try {
        const result = await pywebview.api.open_file_dialog();
        if (result && result.length > 0) {
            const filePath = result[0];

            const endpoint = kind === 'mobile' ? '/api/load-mobile' : '/api/load-pc';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: filePath})
            });
            const data = await response.json();

            if (data.success) {
                if (kind === 'mobile') {
                    mobileFilePath = filePath;
                    document.getElementById('mobile-count').textContent = `(${data.count})`;
                } else {
                    pcFilePath = filePath;
                    document.getElementById('pc-count').textContent = `(${data.count})`;
                }
                updateHeaderStatus();
            } else {
                document.getElementById(`${kind}-count`).textContent = '';
            }
        }
    } catch (err) {
        console.error('Error selecting file:', err);
    }
}

function updateHeaderStatus() {
    const hasMobile = mobileFilePath !== null;
    const hasPc = pcFilePath !== null;
    const statusEl = document.getElementById('status');

    if (hasMobile && hasPc) {
        statusEl.textContent = 'Both CSV loaded';
    } else if (hasMobile) {
        statusEl.textContent = 'Mobile CSV loaded';
    } else if (hasPc) {
        statusEl.textContent = 'PC CSV loaded';
    } else {
        statusEl.textContent = 'No CSV loaded';
    }
}

async function loadSavedPaths() {
    try {
        const response = await fetch('/api/get-saved-paths');
        const data = await response.json();

        if (data.any_loaded) {
            if (data.mobile_path) {
                const res = await fetch('/api/load-mobile', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: data.mobile_path})
                });
                const result = await res.json();
                if (result.success) {
                    mobileFilePath = data.mobile_path;
                    document.getElementById('mobile-count').textContent = `(${result.count})`;
                }
            }

            if (data.pc_path) {
                const res = await fetch('/api/load-pc', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: data.pc_path})
                });
                const result = await res.json();
                if (result.success) {
                    pcFilePath = data.pc_path;
                    document.getElementById('pc-count').textContent = `(${result.count})`;
                }
            }
            updateHeaderStatus();
        }
    } catch (err) {
        console.error('Error loading saved paths:', err);
    }
}

/**
 * Check participants against loaded CSVs
 */
async function checkParticipants() {
    const namesText = document.getElementById('names-input').value;
    
    if (!namesText.trim()) {
        alert('Please enter names to check');
        return;
    }
    
    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({names: namesText})
        });
        const result = await response.json();
        
        if (result.error) {
            alert('Error: ' + result.error);
            return;
        }
        
        displayResults(result);
    } catch (err) {
        console.error('Error checking participants:', err);
        alert('Failed to check participants');
    }
}

/**
 * Display results matching original Tkinter format
 * @param {Object} data - API response data
 */
function displayResults(data) {
    const stats = data.stats;
    window.currentResults = data.results || [];

    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-found').textContent = stats.registered_count;
    document.getElementById('stat-notfound').textContent = stats.not_registered_count;
    document.getElementById('stat-mobile').textContent = stats.mobile_count;
    document.getElementById('stat-pc').textContent = stats.pc_count;

    const results = window.currentResults;
    const allResults = document.getElementById('all-results');

    let tableRows = '';
    results.forEach(r => {
        const platform = r.source || '-';
        const team = r.team || '-';
        const rowClass = r.match_type === 'fuzzy' ? ' class="fuzzy-match"' : '';

        tableRows += `<tr${rowClass}>
            <td>${escapeHtml(r.name)}</td>
            <td>${escapeHtml(platform)}</td>
            <td>${escapeHtml(team)}</td>
        </tr>`;
    });

    allResults.innerHTML = `<table class="results-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Platform</th>
                <th>Team</th>
            </tr>
        </thead>
        <tbody>${tableRows}</tbody>
    </table>`;

    const notRegistered = results.filter(r => !r.verified);
    let copyText = '';

    if (notRegistered.length > 0) {
        copyText = `❌ Not Registered (${notRegistered.length})\n` + '─'.repeat(32) + '\nAtas nama:\n' +
            notRegistered.map(r => `  • ${r.name}`).join('\n') +
            '\n\nBisa melakukan pendaftaran melalui form ya kak\nuntuk melanjutkan tahap verifikasi.';
    } else if (results.length > 0) {
        copyText = '✅ Verified\nMohon ditunggu team ID nya ya kak 🙌';
    } else {
        copyText = 'Nothing to see here';
    }

    document.getElementById('results-box').textContent = copyText;
}

function renderHistory() {
    const historyList = document.getElementById('history-list');
    if (!historyList) {
        console.log('history-list element not found');
        return;
    }

    if (history.length === 0) {
        historyList.innerHTML = '<div class="history-empty" style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 20px;">No history yet</div>';
        return;
    }

    let html = '';
    for (let i = 0; i < history.length; i++) {
        const entry = history[i];
        const statusClass = entry.verified ? 'history-item-verified' : 'history-item-notverified';
        const statusText = entry.verified ? 'Verified' : 'Not Verify';
        html += `<div class="history-item">
            <div class="history-item-row">
                <div class="history-item-info">
                    <div class="history-item-team">${escapeHtml(entry.team)}</div>
                    <div class="history-item-status">
                        <span class="${statusClass}">${statusText}</span>
                        <span>${entry.category}</span>
                    </div>
                </div>
                <button class="history-delete-btn" onclick="deleteHistoryItem(${i})">×</button>
            </div>
        </div>`;
    }
    historyList.innerHTML = html;
}

function deleteHistoryItem(index) {
    history.splice(index, 1);
    window.appHistory = history;
    renderHistory();
}

function addToHistory(results) {
    const verified = results.filter(r => r.verified);
    if (verified.length === 0) return;

    const teams = {};
    for (const r of verified) {
        const team = r.team || '(No Team)';
        if (!teams[team]) {
            teams[team] = { team, verified: true, category: r.source };
        }
    }

    for (const teamName in teams) {
        // Skip if team already in history
        if (history.some(h => h.team === teamName)) continue;
        history.unshift(teams[teamName]);
        if (history.length > 50) history.pop();
    }
    window.appHistory = history;

    renderHistory();
}

// Make functions globally accessible for inline scripts
window.addToHistory = addToHistory;
window.deleteHistoryItem = deleteHistoryItem;

function copyHistory() {
    if (window.appHistory.length === 0) return;

    const text = window.appHistory.map(h => `${h.team}\t${h.verified ? 'Verified' : 'Not Verify'}\t\t${h.category}`).join('\n');
    try {
        navigator.clipboard.writeText(text);
        alert('History copied!');
    } catch (err) {
        console.error('Error copying history:', err);
    }
}
window.copyHistory = copyHistory;

/**
 * Escape HTML for safe rendering
 * @param {string} text - Text to escape
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Clear results and reset stats
 */
function clearResults() {
    document.getElementById('names-input').value = '';
    document.getElementById('results-box').textContent = 'Nothing to see here';
    document.getElementById('all-results').innerHTML = '';
    
    // Reset stats
    document.getElementById('stat-total').textContent = '--';
    document.getElementById('stat-found').textContent = '--';
    document.getElementById('stat-notfound').textContent = '--';
    document.getElementById('stat-mobile').textContent = '--';
    document.getElementById('stat-pc').textContent = '--';
    
    // Reset file status
    mobileFilePath = null;
    pcFilePath = null;
    document.getElementById('mobile-count').textContent = '';
    document.getElementById('pc-count').textContent = '';
    updateHeaderStatus();
}

/**
 * Copy results to clipboard
 */
function copyResults() {
    const resultsText = document.getElementById('results-box').textContent;

    if (!resultsText) {
        return;
    }

    if (window.currentResults && window.currentResults.length > 0) {
        addToHistory(window.currentResults);
    }

    navigator.clipboard.writeText(resultsText).then(() => {
        const hint = document.querySelector('.copy-hint');
        hint.textContent = 'Copied!';
        setTimeout(() => hint.textContent = 'Copy', 1000);
    }).catch(err => {
        console.error('Error copying to clipboard:', err);
    });
}

// Initialize event handlers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Mobile Browse button
    const mobileBrowseBtn = document.getElementById('mobile-browse');
    if (mobileBrowseBtn) {
        mobileBrowseBtn.addEventListener('click', () => selectFile('mobile'));
    }
    
    // PC Browse button
    const pcBrowseBtn = document.getElementById('pc-browse');
    if (pcBrowseBtn) {
        pcBrowseBtn.addEventListener('click', () => selectFile('pc'));
    }
    
    // Check button
    const checkBtn = document.getElementById('check-btn');
    if (checkBtn) {
        checkBtn.addEventListener('click', checkParticipants);
    }
    
    // Clear button
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearResults);
    }
    
    // Copy button
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyResults);
    }

    // Copy history button
    const copyHistoryBtn = document.getElementById('copy-history-btn');
    if (copyHistoryBtn) {
        copyHistoryBtn.addEventListener('click', copyHistory);
    }

    renderHistory();
    loadSavedPaths();
});