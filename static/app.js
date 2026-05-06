/**
 * GAMESEED Participant Checker - pywebview JavaScript
 * Handles UI interactions and API calls to Flask backend
 */

// Store file paths
let mobileFilePath = null;
let pcFilePath = null;

const SOURCE_PADDING = 12;

/**
 * Open file dialog for Mobile or PC CSV
 * @param {string} kind - 'mobile' or 'pc'
 */
async function selectFile(kind) {
    try {
        const result = await pywebview.api.open_file_dialog();
        if (result && result.length > 0) {
            const filePath = result[0];
            
            // Send to Flask backend
            const endpoint = kind === 'mobile' ? '/api/load-mobile' : '/api/load-pc';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: filePath})
            });
            const data = await response.json();
            
            // Update status
            if (data.success) {
                if (kind === 'mobile') {
                    mobileFilePath = filePath;
                    localStorage.setItem('mobilePath', filePath);
                    document.getElementById('mobile-count').textContent = `(${data.count})`;
                } else {
                    pcFilePath = filePath;
                    localStorage.setItem('pcPath', filePath);
                    document.getElementById('pc-count').textContent = `(${data.count})`;
                }
            } else {
                document.getElementById(`${kind}-count`).textContent = '';
            }
        }
    } catch (err) {
        console.error('Error selecting file:', err);
    }
}

/**
 * Load saved CSV paths from localStorage
 */
async function loadSavedPaths() {
    const savedMobile = localStorage.getItem('mobilePath');
    const savedPc = localStorage.getItem('pcPath');
    
    if (savedMobile) {
        try {
            const response = await fetch('/api/load-mobile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: savedMobile})
            });
            const data = await response.json();
            if (data.success) {
                mobileFilePath = savedMobile;
                document.getElementById('mobile-count').textContent = `(${data.count})`;
            }
        } catch (err) {
            console.error('Error loading saved mobile path:', err);
        }
    }
    
    if (savedPc) {
        try {
            const response = await fetch('/api/load-pc', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: savedPc})
            });
            const data = await response.json();
            if (data.success) {
                pcFilePath = savedPc;
                document.getElementById('pc-count').textContent = `(${data.count})`;
            }
        } catch (err) {
            console.error('Error loading saved pc path:', err);
        }
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

    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-found').textContent = stats.registered_count;
    document.getElementById('stat-notfound').textContent = stats.not_registered_count;
    document.getElementById('stat-mobile').textContent = stats.mobile_count;
    document.getElementById('stat-pc').textContent = stats.pc_count;

    const results = data.results || [];
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
    localStorage.removeItem('mobilePath');
    localStorage.removeItem('pcPath');
    document.getElementById('mobile-count').textContent = '';
    document.getElementById('pc-count').textContent = '';
}

/**
 * Copy results to clipboard
 */
async function copyResults() {
    const resultsText = document.getElementById('results-box').textContent;
    
    if (!resultsText) {
        return;
    }
    
    try {
        await navigator.clipboard.writeText(resultsText);
        alert('Results copied to clipboard!');
    } catch (err) {
        console.error('Error copying to clipboard:', err);
    }
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
    
    loadSavedPaths();
});