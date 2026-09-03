 

const apiUrl = '';

async function fetchWithHandling(endpoint, options = {}) {
    try {
        const res = await fetch(endpoint, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error("API Error:", err);
        alert("Operation failed: " + err.message);
        return null;
    }
}


const userGrid = document.getElementById('user-grid');
const modal = document.getElementById('user-modal');
const userForm = document.getElementById('user-form');
const addUserBtn = document.getElementById('add-user-btn');
const closeBtn = document.getElementById('close-user-modal');


let isEditing = false;


document.addEventListener('DOMContentLoaded', loadUsers);

async function loadUsers() {
    userGrid.innerHTML = '<p style="text-align:center;width:100%">Loading roster...</p>';
    const data = await fetchWithHandling('/list_users');
    if (data && data.users) {
        renderUsers(data.users);
    }
}

function renderUsers(users) {
    userGrid.innerHTML = '';
    if (users.length === 0) {
        userGrid.innerHTML = '<p style="text-align:center;width:100%">No players found. Add one!</p>';
        return;
    }

    users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';
        const userColor = user.color || '#3b82f6';
        card.innerHTML = `
            <div class="user-avatar" style="color: ${userColor}"><i class="${user.avatar || 'fas fa-robot'}"></i></div>
            <h3 class="user-name">${user.name}</h3>
            <div class="user-stats">
                <div class="stat stat-played">
                    <span class="stat-val">${user.games_played}</span>
                    <span class="stat-label">Total Games</span>
                </div>
            </div>
            <div class="card-actions">
                <button class="action-btn" onclick="viewHistory(${user.id}, '${user.name.replace(/'/g, "\\'")}')" style="background:var(--sabana-blue); color:white; width:100%; margin-bottom:8px">
                    <i class="fas fa-history"></i> Full History
                </button>
                <div style="display:flex; gap:8px; width:100%">
                    <button class="action-btn" onclick="editUser(${user.id})" style="flex:1"><i class="fas fa-edit"></i> Edit</button>
                    <button class="action-btn delete-btn" onclick="deleteUser(${user.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
        userGrid.appendChild(card);
    });
}


function updatePreview() {
    const avatarRadio = document.querySelector('input[name="avatar"]:checked');
    if (!avatarRadio) return;
    
    const avatar = avatarRadio.value;
    const color = document.getElementById('user-color').value;
    
    const previewEl = document.getElementById('hero-preview');
    const nameInput = document.getElementById('user-name');
    
    if (previewEl) {
        previewEl.innerHTML = `<i class="${avatar}"></i>`;
        previewEl.style.color = color;
    }
    if (nameInput) {
        nameInput.style.color = color;
    }
}


function randomizeCharacter() {
    const avatars = document.querySelectorAll('input[name="avatar"]');
    avatars[Math.floor(Math.random() * avatars.length)].checked = true;

    const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#a855f7', '#ec4899', '#1e1b4b'];
    document.getElementById('user-color').value = colors[Math.floor(Math.random() * colors.length)];
    
    updatePreview();
}


function launchConfetti() {
    const canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    let particles = [];
    for (let i = 0; i < 150; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            size: Math.random() * 10 + 5,
            color: `hsl(${Math.random() * 360}, 70%, 60%)`,
            speed: Math.random() * 5 + 2,
            angle: Math.random() * 6.28
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.y += p.speed;
            p.x += Math.sin(p.angle) * 2;
            ctx.fillStyle = p.color;
            ctx.fillRect(p.x, p.y, p.size, p.size);
        });
        particles = particles.filter(p => p.y < canvas.height);
        if (particles.length > 0) requestAnimationFrame(animate);
    }
    animate();
}


document.addEventListener('input', (e) => {
    if (e.target.id === 'user-name' || e.target.id === 'user-color') updatePreview();
});

document.addEventListener('change', (e) => {
    if (e.target.name === 'avatar') updatePreview();
});

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('color-dot')) {
        const color = e.target.getAttribute('data-color');
        document.getElementById('user-color').value = color;
        updatePreview();
    }
    if (e.target.closest('#randomize-btn')) {
        randomizeCharacter();
    }
});


addUserBtn.onclick = () => openModal();
if (closeBtn) closeBtn.onclick = () => closeModal();
window.onclick = (e) => { if (e.target === modal) closeModal(); };

function openModal(user = null) {
    isEditing = !!user;
    document.getElementById('user-id').value = user ? user.id : '';
    document.getElementById('user-name').value = user ? user.name : '';

    const avatarVal = user ? user.avatar : 'fas fa-robot';
    const radio = document.querySelector(`input[name="avatar"][value="${avatarVal}"]`);
    if (radio) radio.checked = true;

    const colorVal = user ? user.color : '#3b82f6';
    document.getElementById('user-color').value = colorVal;

    modal.style.display = 'flex';
    updatePreview();
}

function closeModal() {
    modal.style.display = 'none';
    userForm.reset();
}


userForm.onsubmit = async (e) => {
    e.preventDefault();
    const id = document.getElementById('user-id').value;
    const name = document.getElementById('user-name').value;
    const avatar = document.querySelector('input[name="avatar"]:checked').value;
    const color = document.getElementById('user-color').value;

    launchConfetti();

    setTimeout(async () => {
        if (isEditing) {
            await fetchWithHandling('/update_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, name, avatar, color })
            });
        } else {
            await fetchWithHandling('/create_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, avatar, color })
            });
        }
        closeModal();
        loadUsers();
    }, 1000);
};

window.editUser = async (id) => {
    const data = await fetchWithHandling('/get_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    });
    if (data && data.user) {
        openModal(data.user);
    }
};

window.deleteUser = async (id) => {
    if (confirm('Are you sure you want to retire this hero?')) {
        await fetchWithHandling('/delete_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        loadUsers();
    }
};


const historyModal = document.getElementById('history-modal');
const closeHistoryBtn = document.getElementById('close-history');
const historyList = document.getElementById('history-list');

window.viewHistory = async (userId, userName) => {
    document.getElementById('history-modal-title').textContent = `History: ${userName}`;
    historyList.innerHTML = '<p>Loading records...</p>';
    historyModal.style.display = 'flex';

    const data = await fetchWithHandling('/list_game_history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    if (data && data.history) renderHistory(data.history);
};

function renderHistory(records) {
    if (records.length === 0) {
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-chart-line"></i>
                <p>No games played yet.</p>
            </div>`;
        return;
    }

    const normalized = records.map((record) => {
        const totalSteps = toNumber(record.total_steps);
        const completedSteps = toNumber(record.completed_steps);
        return {
            ...record,
            won: isWon(record.won),
            mistakes: toNumber(record.mistakes),
            total_steps: totalSteps,
            completed_steps: completedSteps,
            duration_seconds: toNumber(record.duration_seconds),
            completion_pct: totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0,
            trajectory_label: record.trajectory_name || (record.trajectory_id ? `Trajectory ${record.trajectory_id}` : 'Unassigned')
        };
    });

    const totalPlays = normalized.length;
    const wins = normalized.filter((r) => r.won).length;
    const winRate = Math.round((wins / totalPlays) * 100);
    const avgCompletion = Math.round(normalized.reduce((sum, r) => sum + r.completion_pct, 0) / totalPlays);
    const avgDuration = Math.round(normalized.reduce((sum, r) => sum + r.duration_seconds, 0) / totalPlays);
    const totalMistakes = normalized.reduce((sum, r) => sum + r.mistakes, 0);

    const usage = normalized.reduce((acc, r) => {
        acc[r.trajectory_label] = (acc[r.trajectory_label] || 0) + 1;
        return acc;
    }, {});
    const maxUsage = Math.max(...Object.values(usage));
    const usageRows = Object.entries(usage)
        .sort((a, b) => b[1] - a[1])
        .map(([name, count]) => `
            <div class="usage-row">
                <span>${escapeHtml(name)}</span>
                <div class="usage-bar-track"><div class="usage-bar" style="width:${Math.max(8, (count / maxUsage) * 100)}%"></div></div>
                <strong>${count}</strong>
            </div>`)
        .join('');

    const trend = [...normalized].reverse().slice(-8);
    const trendBars = trend.map((r) => `
        <div class="trend-bar" title="${escapeHtml(r.trajectory_label)}: ${r.completion_pct}%">
            <span style="height:${Math.max(8, r.completion_pct)}%"></span>
        </div>`)
        .join('');

    const recentRows = normalized.slice(0, 8).map(r => {
        const date = formatDate(r.timestamp);
        const duration = formatDuration(r.duration_seconds);
        const statusClass = r.won ? 'stat-won' : 'stat-lost';
        const statusLabel = r.won ? 'COMPLETED' : 'FAILED';
        return `<div class="history-item">
            <div class="history-meta">
                <span class="history-date">${date}</span>
                <span class="history-status ${statusClass}">${statusLabel}</span>
            </div>
            <div class="history-trajectory">${escapeHtml(r.trajectory_label)}</div>
            <div class="history-stats">
                <div class="h-stat"><span class="h-val">${r.mistakes}</span><span class="h-label">Mistakes</span></div>
                <div class="h-stat"><span class="h-val">${r.completed_steps}/${r.total_steps}</span><span class="h-label">Steps</span></div>
                <div class="h-stat"><span class="h-val">${duration}</span><span class="h-label">Duration</span></div>
            </div>
        </div>`;
    }).join('');

    historyList.innerHTML = `
        <div class="history-analytics">
            <div class="analytics-card">
                <span class="analytics-label">Total Plays</span>
                <strong>${totalPlays}</strong>
            </div>
            <div class="analytics-card">
                <span class="analytics-label">Success Rate</span>
                <strong>${winRate}%</strong>
            </div>
            <div class="analytics-card">
                <span class="analytics-label">Avg. Completion</span>
                <strong>${avgCompletion}%</strong>
            </div>
            <div class="analytics-card">
                <span class="analytics-label">Avg. Time</span>
                <strong>${formatDuration(avgDuration)}</strong>
            </div>
            <div class="analytics-card">
                <span class="analytics-label">Mistakes</span>
                <strong>${totalMistakes}</strong>
            </div>
        </div>
        <div class="history-visual-grid">
            <section class="history-panel">
                <h3>Progress Trend</h3>
                <div class="trend-chart">${trendBars}</div>
            </section>
            <section class="history-panel">
                <h3>Trajectory Usage</h3>
                <div class="usage-chart">${usageRows}</div>
            </section>
        </div>
        <h3 class="recent-heading">Recent Activity</h3>
        ${recentRows}`;
}

function toNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function isWon(value) {
    return value === true || value === 1 || value === '1' || String(value).toLowerCase() === 'true';
}

function formatDuration(seconds) {
    const safeSeconds = Math.max(0, toNumber(seconds));
    return Math.floor(safeSeconds / 60) + 'm ' + (safeSeconds % 60) + 's';
}

function formatDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleString();
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[char]));
}
if (closeHistoryBtn) closeHistoryBtn.onclick = () => { historyModal.style.display = 'none'; };
