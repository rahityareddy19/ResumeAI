/**
 * ResumeAI — Frontend Application Logic
 * Handles file uploads, API communication, dashboard stats,
 * dynamic results rendering with score bars, status badges, and CSV export.
 */

const API_BASE = window.location.origin;

// ── State ───────────────────────────────────────────────────────────────────
let jdUploaded = false;
let resumesUploaded = false;
let selectedResumeFiles = null;

// ── DOM References ──────────────────────────────────────────────────────────
const jdTextArea       = document.getElementById("jd-text");
const jdFileInput      = document.getElementById("jd-file");
const jdUploadZone     = document.getElementById("jd-upload-zone");
const jdFileInfo       = document.getElementById("jd-file-info");
const jdStatus         = document.getElementById("jd-status");
const btnUploadJD      = document.getElementById("btn-upload-jd");

const resumeFileInput  = document.getElementById("resume-files");
const resumeUploadZone = document.getElementById("resume-upload-zone");
const resumeFileList   = document.getElementById("resume-file-list");
const resumeStatus     = document.getElementById("resume-status");
const btnUploadResumes = document.getElementById("btn-upload-resumes");

const btnAnalyze       = document.getElementById("btn-analyze");
const loadingIndicator = document.getElementById("loading-indicator");

const dashboardSection = document.getElementById("dashboard-section");
const resultsSection   = document.getElementById("results-section");
const resultsSummary   = document.getElementById("results-summary");
const resultsBody      = document.getElementById("results-body");
const candidateCards   = document.getElementById("candidate-cards");

// ── Upload Zone Event Handlers ──────────────────────────────────────────────
function setupUploadZone(zone, fileInput) {
    zone.addEventListener("click", () => fileInput.click());

    zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
    });

    zone.addEventListener("dragleave", () => {
        zone.classList.remove("dragover");
    });

    zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
        fileInput.files = e.dataTransfer.files;
        fileInput.dispatchEvent(new Event("change"));
    });
}

setupUploadZone(jdUploadZone, jdFileInput);
setupUploadZone(resumeUploadZone, resumeFileInput);

// JD file selection feedback
jdFileInput.addEventListener("change", () => {
    if (jdFileInput.files.length > 0) {
        const file = jdFileInput.files[0];
        jdFileInfo.hidden = false;
        jdFileInfo.innerHTML = `<span>📄</span> <strong>${file.name}</strong> <span style="color:var(--text-muted)">(${formatFileSize(file.size)})</span>`;
        // Clear text area since we're using file
        jdTextArea.value = "";
    }
});

// Resume files selection feedback
resumeFileInput.addEventListener("change", () => {
    selectedResumeFiles = resumeFileInput.files;
    renderResumeFileList();
});

function renderResumeFileList() {
    if (!selectedResumeFiles || selectedResumeFiles.length === 0) {
        resumeFileList.hidden = true;
        return;
    }
    resumeFileList.hidden = false;
    resumeFileList.innerHTML = "";

    for (let i = 0; i < selectedResumeFiles.length; i++) {
        const file = selectedResumeFiles[i];
        const item = document.createElement("div");
        item.className = "file-item";
        item.style.animationDelay = `${i * 0.05}s`;
        item.innerHTML = `
            <span class="file-item-name">📄 ${file.name}</span>
            <span class="file-item-size">${formatFileSize(file.size)}</span>
        `;
        resumeFileList.appendChild(item);
    }
}

// ── Upload Job Description ──────────────────────────────────────────────────
async function uploadJD() {
    const text = jdTextArea.value.trim();
    const file = jdFileInput.files[0];

    if (!text && !file) {
        showStatus(jdStatus, "Please enter text or upload a file.", "error");
        return;
    }

    btnUploadJD.disabled = true;
    const formData = new FormData();

    if (text) {
        formData.append("jd_text", text);
    } else {
        formData.append("jd_file", file);
    }

    try {
        const res = await fetch(`${API_BASE}/upload-jd`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) {
            showStatus(jdStatus, data.error || "Upload failed.", "error");
            return;
        }

        jdUploaded = true;
        showStatus(jdStatus, `✅ ${data.message} (${data.length} characters)`, "success");
    } catch (err) {
        showStatus(jdStatus, `Network error: ${err.message}`, "error");
    } finally {
        btnUploadJD.disabled = false;
    }
}

// ── Upload Resumes ──────────────────────────────────────────────────────────
async function uploadResumes() {
    if (!selectedResumeFiles || selectedResumeFiles.length === 0) {
        showStatus(resumeStatus, "Please select resume files first.", "error");
        return;
    }

    btnUploadResumes.disabled = true;
    const formData = new FormData();

    for (let i = 0; i < selectedResumeFiles.length; i++) {
        formData.append("resume_files", selectedResumeFiles[i]);
    }

    try {
        const res = await fetch(`${API_BASE}/upload-resumes`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) {
            showStatus(resumeStatus, data.error || "Upload failed.", "error");
            return;
        }

        resumesUploaded = true;
        let msg = `✅ ${data.message}`;
        if (data.warnings && data.warnings.length > 0) {
            msg += ` ⚠️ Warnings: ${data.warnings.join(", ")}`;
        }
        showStatus(resumeStatus, msg, "success");
    } catch (err) {
        showStatus(resumeStatus, `Network error: ${err.message}`, "error");
    } finally {
        btnUploadResumes.disabled = false;
    }
}

// ── Analyze Resumes ─────────────────────────────────────────────────────────
async function analyzeResumes() {
    if (!jdUploaded) {
        showStatus(jdStatus, "Please upload a Job Description first (Step 1).", "error");
        return;
    }
    if (!resumesUploaded) {
        showStatus(resumeStatus, "Please upload resumes first (Step 2).", "error");
        return;
    }

    // Show loading
    btnAnalyze.disabled = true;
    loadingIndicator.hidden = false;
    dashboardSection.hidden = true;
    resultsSection.hidden = true;

    try {
        const res = await fetch(`${API_BASE}/analyze`, {
            method: "POST",
        });
        const data = await res.json();

        if (!res.ok) {
            loadingIndicator.hidden = true;
            btnAnalyze.disabled = false;
            alert(data.error || "Analysis failed.");
            return;
        }

        // Render dashboard and results
        renderDashboard(data);
        renderResults(data.candidates);
    } catch (err) {
        alert(`Analysis failed: ${err.message}`);
    } finally {
        loadingIndicator.hidden = true;
        btnAnalyze.disabled = false;
    }
}

// ── Render Dashboard Stats ──────────────────────────────────────────────────
function renderDashboard(data) {
    dashboardSection.hidden = false;

    // Animate counter values
    animateCounter("stat-total", data.total_candidates || 0);
    animateCounter("stat-selected", data.selected || 0);
    animateCounter("stat-average", data.average_score || 0);
    animateCounter("stat-top", data.top_score || 0);
}

function animateCounter(elementId, targetValue) {
    const el = document.getElementById(elementId);
    const duration = 800;
    const start = performance.now();
    const startVal = 0;

    el.classList.add("counting");

    function step(timestamp) {
        const progress = Math.min((timestamp - start) / duration, 1);
        // Ease-out curve
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(startVal + (targetValue - startVal) * eased);
        el.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            el.textContent = targetValue;
            setTimeout(() => el.classList.remove("counting"), 200);
        }
    }

    requestAnimationFrame(step);
}

// ── Render Results ──────────────────────────────────────────────────────────
function renderResults(candidates) {
    resultsSection.hidden = false;
    resultsSummary.textContent = `${candidates.length} candidate(s) analyzed and ranked`;

    // Clear previous
    resultsBody.innerHTML = "";
    candidateCards.innerHTML = "";

    // Populate table
    candidates.forEach((c, index) => {
        const scoreClass = getScoreClass(c.score);
        const barClass = getBarClass(c.score);
        const rankClass = c.rank <= 3 ? `rank-${c.rank}` : "rank-other";
        const comp = c.component_scores || {};
        const medal = getMedal(c.rank);
        const statusClass = c.status === "Selected" ? "status-selected" : "status-rejected";
        const statusIcon = c.status === "Selected" ? "✓" : "✗";

        // Limit skills shown in table
        const matchedCompact = renderSkillPills(c.matched_skills || [], "matched", 3);
        const missingCompact = renderSkillPills(c.missing_skills || [], "missing", 3);

        const certClass = (c.certificates || 0) > 0 ? "" : "cert-zero";

        const tr = document.createElement("tr");
        tr.style.animationDelay = `${index * 0.08}s`;
        tr.innerHTML = `
            <td>
                <span class="rank-badge ${rankClass}">${c.rank}</span>
                ${medal ? `<span class="rank-medal">${medal}</span>` : ""}
            </td>
            <td><strong>${escapeHtml(c.name)}</strong></td>
            <td>
                <div class="score-cell">
                    <span class="score-value ${scoreClass}">${c.score}</span>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill ${barClass}" data-width="${c.score}%"></div>
                    </div>
                </div>
            </td>
            <td><span class="status-badge ${statusClass}">${statusIcon} ${c.status}</span></td>
            <td><span class="cert-badge ${certClass}">🏅 ${c.certificates || 0}</span></td>
            <td><div class="skills-compact">${matchedCompact}</div></td>
            <td><div class="skills-compact">${missingCompact}</div></td>
            <td><span class="assessment-text">${escapeHtml(c.reason)}</span></td>
        `;
        resultsBody.appendChild(tr);
    });

    // Populate detail cards
    candidates.forEach((c, index) => {
        const card = createCandidateCard(c, index);
        candidateCards.appendChild(card);
    });

    // Animate score bars
    requestAnimationFrame(() => {
        setTimeout(() => {
            document.querySelectorAll(".score-bar-fill, .component-bar-fill").forEach((bar) => {
                const width = bar.getAttribute("data-width");
                if (width) bar.style.width = width;
            });
        }, 150);
    });

    // Scroll to dashboard
    dashboardSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSkillPills(skills, type, maxShow) {
    if (!skills || skills.length === 0) {
        return `<span class="skill-pill ${type}" style="opacity:0.5">None</span>`;
    }

    const shown = skills.slice(0, maxShow);
    const remaining = skills.length - maxShow;

    let html = shown
        .map((s) => `<span class="skill-pill ${type}">${escapeHtml(s)}</span>`)
        .join("");

    if (remaining > 0) {
        html += `<span class="skills-more">+${remaining}</span>`;
    }

    return html;
}

function createCandidateCard(candidate, index) {
    const c = candidate;
    const comp = c.component_scores || {};
    const scoreClass = getScoreClass(c.score);
    const cardColorClass = getCardColorClass(c.score);
    const medal = getMedal(c.rank);
    const statusClass = c.status === "Selected" ? "status-selected" : "status-rejected";
    const statusIcon = c.status === "Selected" ? "✓" : "✗";

    const card = document.createElement("div");
    card.className = `candidate-card ${cardColorClass}`;
    card.style.animationDelay = `${index * 0.1}s`;

    let matchedTags = (c.matched_skills || [])
        .map((s) => `<span class="skill-tag matched">✓ ${escapeHtml(s)}</span>`)
        .join("");
    let missingTags = (c.missing_skills || [])
        .map((s) => `<span class="skill-tag missing">✗ ${escapeHtml(s)}</span>`)
        .join("");

    card.innerHTML = `
        <div class="candidate-card-header">
            <div class="candidate-card-left">
                <span class="rank-badge ${c.rank <= 3 ? 'rank-' + c.rank : 'rank-other'}">${c.rank}</span>
                ${medal ? `<span style="font-size:1.3rem">${medal}</span>` : ""}
                <span class="candidate-name">${escapeHtml(c.name)}</span>
                <span class="status-badge ${statusClass}">${statusIcon} ${c.status}</span>
            </div>
            <span class="candidate-score-big ${scoreClass}">${c.score}</span>
        </div>

        <p class="assessment-text" style="max-width:none;margin-bottom:4px;">${escapeHtml(c.reason)}</p>

        <div style="display:flex;gap:12px;align-items:center;margin-top:8px;">
            <span class="cert-badge ${(c.certificates || 0) > 0 ? '' : 'cert-zero'}">🏅 ${c.certificates || 0} Certificate${(c.certificates || 0) !== 1 ? 's' : ''}</span>
        </div>

        ${matchedTags ? `
        <div class="candidate-section-title">Matched Skills</div>
        <div class="skills-tags">${matchedTags}</div>
        ` : ""}

        ${missingTags ? `
        <div class="candidate-section-title">Missing Skills</div>
        <div class="skills-tags">${missingTags}</div>
        ` : ""}

        <div class="component-bars">
            <div class="component-bar">
                <div class="component-bar-label">Skills</div>
                <div class="component-bar-value ${getScoreClass(comp.skills)}">${comp.skills || 0}%</div>
                <div class="component-bar-track">
                    <div class="component-bar-fill ${getBarClass(comp.skills)}" data-width="${comp.skills || 0}%"></div>
                </div>
            </div>
            <div class="component-bar">
                <div class="component-bar-label">Experience</div>
                <div class="component-bar-value ${getScoreClass(comp.experience)}">${comp.experience || 0}%</div>
                <div class="component-bar-track">
                    <div class="component-bar-fill ${getBarClass(comp.experience)}" data-width="${comp.experience || 0}%"></div>
                </div>
            </div>
            <div class="component-bar">
                <div class="component-bar-label">Projects</div>
                <div class="component-bar-value ${getScoreClass(comp.projects)}">${comp.projects || 0}%</div>
                <div class="component-bar-track">
                    <div class="component-bar-fill ${getBarClass(comp.projects)}" data-width="${comp.projects || 0}%"></div>
                </div>
            </div>
        </div>
    `;

    return card;
}

// ── CSV Export ───────────────────────────────────────────────────────────────
async function exportCSV() {
    try {
        const res = await fetch(`${API_BASE}/export-csv`);
        if (!res.ok) {
            const data = await res.json();
            alert(data.error || "Export failed.");
            return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "resume_screening_results.csv";
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert(`Export failed: ${err.message}`);
    }
}

// ── Utility Functions ───────────────────────────────────────────────────────
function showStatus(el, message, type) {
    el.hidden = false;
    el.className = `status-msg ${type}`;
    el.textContent = message;

    if (type === "success") {
        setTimeout(() => { el.hidden = true; }, 8000);
    }
}

function getMedal(rank) {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return null;
}

function getScoreClass(score) {
    if (score >= 75) return "score-excellent";
    if (score >= 55) return "score-good";
    if (score >= 35) return "score-average";
    return "score-poor";
}

function getBarClass(score) {
    if (score >= 75) return "bar-excellent";
    if (score >= 55) return "bar-good";
    if (score >= 35) return "bar-average";
    return "bar-poor";
}

function getCardColorClass(score) {
    if (score >= 75) return "card-excellent";
    if (score >= 55) return "card-good";
    if (score >= 35) return "card-average";
    return "card-poor";
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
