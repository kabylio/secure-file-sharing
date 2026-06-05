/**
 * Secure File Sharing System - Frontend Application
 * Handles authentication, file operations, and UI interactions
 */

const API_BASE = '';
let currentToken = localStorage.getItem('token');
let currentUser = null;
let toastQueue = [];
let searchQuery = '';
let currentFilter = 'all';

// ═══════════════════════════════════════════════════════════════
// DOM ELEMENTS
// ═══════════════════════════════════════════════════════════════

const elements = {
    authContainer: document.getElementById('auth-container'),
    mainContent: document.getElementById('main-content'),
    navbar: document.getElementById('navbar'),
    navLinks: document.getElementById('nav-links'),
    navUser: document.getElementById('nav-user'),
    userName: document.getElementById('user-name'),
    logoutBtn: document.getElementById('logout-btn'),

    // Auth forms
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    authMessage: document.getElementById('auth-message'),
    authTabs: document.querySelectorAll('.auth-tab'),

    // Upload
    uploadZone: document.getElementById('upload-zone'),
    fileInput: document.getElementById('file-input'),
    uploadDetails: document.getElementById('upload-details'),
    uploadFilename: document.getElementById('upload-filename'),
    uploadFilesize: document.getElementById('upload-filesize'),
    uploadBtn: document.getElementById('upload-btn'),
    uploadProgress: document.getElementById('upload-progress'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    uploadResult: document.getElementById('upload-result'),

    // Pages
    pages: document.querySelectorAll('.page'),
    navLinksItems: document.querySelectorAll('.nav-link'),

    // Modals
    shareModal: document.getElementById('share-modal'),
    detailsModal: document.getElementById('details-modal'),

    // Audit filters
    auditFilters: document.querySelectorAll('.audit-filters .btn')
};

// ═══════════════════════════════════════════════════════════════
// API HELPERS
// ═══════════════════════════════════════════════════════════════

function formatApiError(detail) {
    if (Array.isArray(detail)) {
        return detail.map(item => item.msg || JSON.stringify(item)).join(', ');
    }
    if (detail && typeof detail === 'object') {
        return detail.message || JSON.stringify(detail);
    }
    return detail || 'Request failed';
}

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            ...options.headers
        },
        ...options
    };

    if (!(config.body instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
    }

    if (currentToken) {
        config.headers['Authorization'] = `Bearer ${currentToken}`;
    }

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);

        if (response.status === 401) {
            logout();
            showToast('Session expired. Please log in again.', 'warning');
            return null;
        }

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorMsg = formatApiError(data?.detail) || `HTTP ${response.status}: ${response.statusText}`;
            throw new Error(errorMsg);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Debug: log all API requests
const originalApiRequest = apiRequest;
apiRequest = async function(endpoint, options = {}) {
    console.log('API Request:', endpoint, 'Token:', currentToken ? 'present' : 'missing');
    const result = await originalApiRequest(endpoint, options);
    console.log('API Response:', endpoint, result);
    return result;
};
// ═══════════════════════════════════════════════════════════════
// AUTHENTICATION
// ═══════════════════════════════════════════════════════════════

async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });

    if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(formatApiError(data?.detail) || 'Login failed');
    }

    const data = await response.json();

    currentToken = data.access_token;
    localStorage.setItem('token', currentToken);
    return data;
}

async function register(username, email, password) {
    return apiRequest('/auth/register', {
        method: 'POST',
        body: { username, email, password }
    });
}

async function getCurrentUser() {
    return apiRequest('/auth/me');
}

function logout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('token');
     // Clear upload form state
    elements.fileInput.value = '';
    elements.uploadDetails.classList.add('hidden');
    elements.uploadResult.classList.add('hidden');
    elements.uploadProgress.classList.add('hidden');
    elements.progressFill.style.width = '0%';

    showAuth();
}

function showAuth() {
    elements.authContainer.classList.remove('hidden');
    elements.mainContent.classList.add('hidden');
    elements.navbar.style.display = 'none';
}

function showApp() {
    elements.authContainer.classList.add('hidden');
    elements.mainContent.classList.remove('hidden');
    elements.navbar.style.display = 'flex';
}

function showMessage(message, type = 'error') {
    elements.authMessage.textContent = message;
    elements.authMessage.className = `auth-message ${type}`;
    setTimeout(() => {
        elements.authMessage.textContent = '';
        elements.authMessage.className = 'auth-message';
    }, 5000);
}

function showToast(message, type = 'info', duration = 4000) {
    /**Enhanced toast notification system with queue management */
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.opacity = '1';
    
    const toastContainer = document.body;
    toastContainer.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ═══════════════════════════════════════════════════════════════
// FORM VALIDATION
// ═══════════════════════════════════════════════════════════════

function showFormValidation(inputElement, isValid, message = '') {
    const feedbackEl = inputElement.nextElementSibling;
    
    if (isValid) {
        inputElement.classList.remove('error', 'warning');
        inputElement.classList.add('success');
        if (feedbackEl && feedbackEl.classList.contains('form-feedback')) {
            feedbackEl.textContent = '';
            feedbackEl.className = 'form-feedback';
        }
    } else {
        inputElement.classList.remove('success');
        inputElement.classList.add('error');
        if (feedbackEl && feedbackEl.classList.contains('form-feedback')) {
            feedbackEl.textContent = message;
            feedbackEl.className = 'form-feedback error';
            feedbackEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        }
    }
}

function validateUsername(username) {
    if (!username || username.trim().length < 3) {
        return { valid: false, message: 'Username must be at least 3 characters' };
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        return { valid: false, message: 'Username can only contain letters, numbers, _, and -' };
    }
    return { valid: true, message: 'Username looks good' };
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
        return { valid: false, message: 'Please enter a valid email address' };
    }
    return { valid: true, message: 'Email is valid' };
}

function validatePassword(password) {
    if (!password || password.length < 8) {
        return { valid: false, message: 'Password must be at least 8 characters' };
    }
    if (!/[A-Z]/.test(password)) {
        return { valid: false, message: 'Password must contain at least one uppercase letter' };
    }
    if (!/[0-9]/.test(password)) {
        return { valid: false, message: 'Password must contain at least one number' };
    }
    return { valid: true, message: 'Password is strong' };
}

function validatePasswordMatch(password, confirmPassword) {
    if (password !== confirmPassword) {
        return { valid: false, message: 'Passwords do not match' };
    }
    return { valid: true, message: 'Passwords match' };
}

// ═══════════════════════════════════════════════════════════════
// CONFIRMATION DIALOG
// ═══════════════════════════════════════════════════════════════

function showConfirmDialog(title, message, confirmText = 'Confirm', cancelText = 'Cancel', isDangerous = false) {
    return new Promise((resolve) => {
        const backdrop = document.createElement('div');
        backdrop.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 399; backdrop-filter: blur(2px);';
        
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog scale-in';
        dialog.innerHTML = `
            <div class="confirm-dialog-header">
                <i class="fas ${isDangerous ? 'fa-exclamation-triangle' : 'fa-question-circle'}"></i>
                <h3>${escapeHtml(title)}</h3>
            </div>
            <div class="confirm-dialog-body">
                ${escapeHtml(message)}
            </div>
            <div class="confirm-dialog-footer">
                <button class="btn btn-outline dialog-cancel-btn">${escapeHtml(cancelText)}</button>
                <button class="btn ${isDangerous ? 'btn-danger' : 'btn-primary'} dialog-confirm-btn">${escapeHtml(confirmText)}</button>
            </div>
        `;
        
        const confirmBtn = dialog.querySelector('.dialog-confirm-btn');
        const cancelBtn = dialog.querySelector('.dialog-cancel-btn');
        
        const cleanup = () => {
            backdrop.remove();
            dialog.remove();
        };
        
        confirmBtn.addEventListener('click', () => {
            cleanup();
            resolve(true);
        });
        
        cancelBtn.addEventListener('click', () => {
            cleanup();
            resolve(false);
        });
        
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                cleanup();
                resolve(false);
            }
        });
        
        document.body.appendChild(backdrop);
        document.body.appendChild(dialog);
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ═══════════════════════════════════════════════════════════════
// FILE OPERATIONS
// ═══════════════════════════════════════════════════════════════

async function uploadFile(file, signFile = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sign', signFile ? 'true' : 'false');

    elements.uploadProgress.classList.remove('hidden');
    elements.uploadResult.classList.add('hidden');
    elements.progressFill.style.width = '10%';
    elements.progressText.textContent = 'Preparing file...';

    try {
        const progressFills = [
            { percent: 30, text: 'Encrypting with AES-256-GCM...' },
            { percent: 60, text: 'Uploading to server...' },
            { percent: 90, text: 'Verifying integrity...' },
            { percent: 100, text: 'Complete!' }
        ];

        // Simulate progress while uploading
        let progressIndex = 0;
        const progressInterval = setInterval(() => {
            if (progressIndex < progressFills.length) {
                const { percent, text } = progressFills[progressIndex];
                elements.progressFill.style.width = percent + '%';
                elements.progressText.textContent = text;
                progressIndex++;
            }
        }, 500);

        const response = await fetch(`${API_BASE}/files/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${currentToken}` },
            body: formData
        });

        clearInterval(progressInterval);
        elements.progressFill.style.width = '100%';
        elements.progressText.textContent = 'Upload complete!';

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(formatApiError(data?.detail) || 'Upload failed');
        }

        elements.uploadResult.classList.remove('hidden');
        elements.uploadResult.classList.add('success');

        elements.uploadResult.classList.remove('error');
        elements.uploadResult.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <strong>✓ File encrypted and uploaded successfully!</strong><br>
            <small>File hash: ${data.file_hash.substring(0, 32)}...</small><br>
            <small>${signFile ? '✓ File digitally signed' : ''}</small>
        `;

        showToast('File uploaded successfully!', 'success');

        setTimeout(() => {
            showPage('dashboard');
            loadDashboard();
        }, 2000);

        return data;
    } catch (error) {
        elements.uploadResult.classList.remove('hidden');
        elements.uploadResult.classList.add('error');
        elements.uploadResult.classList.remove('success');
        elements.uploadResult.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <strong>Upload failed:</strong> <br>
            ${escapeHtml(error.message)}
        `;
        elements.progressFill.style.width = '0%';
        elements.progressText.textContent = 'Upload failed';
        
        showToast(error.message, 'error');
        throw error;
    } finally {
        elements.uploadBtn.disabled = false;
        elements.uploadBtn.classList.remove('loading');
    }
}

async function downloadFile(fileId, filename) {
    const toastId = showToast('Downloading file...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/files/${fileId}/download`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (!response.ok) {
            const data = await response.json().catch(() => null);
            throw new Error(formatApiError(data?.detail) || 'Download failed');
        }

        const blob = await response.blob();
        
        if (blob.size === 0) {
            throw new Error('Downloaded file is empty. The file may be corrupted.');
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast(`✓ "${filename}" downloaded and decrypted successfully`, 'success');
    } catch (error) {
        showToast(`Download failed: ${error.message}`, 'error');
    }
}

async function shareFile(fileId, recipientUsername, canDownload = true) {
    return apiRequest(`/files/${fileId}/share`, {
        method: 'POST',
        body: {
            recipient_username: recipientUsername,
            can_download: canDownload,
            can_view: true
        }
    });
}

async function deleteFile(fileId) {
    return apiRequest(`/files/${fileId}`, { method: 'DELETE' });
}

async function verifySignature(fileId) {
    return apiRequest(`/files/${fileId}/verify`);
}

// ═══════════════════════════════════════════════════════════════
// DATA LOADING
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
    try {
        const [myFiles, sharedFiles, auditStats] = await Promise.all([
            apiRequest('/files/my-files'),
            apiRequest('/files/shared-with-me'),
            apiRequest('/audit/stats')
        ]);

        // Update stats
        document.getElementById('stat-total-files').textContent = myFiles?.length || 0;
        document.getElementById('stat-shared-with-me').textContent = sharedFiles?.length || 0;
        document.getElementById('stat-uploads').textContent = auditStats?.total_uploads || 0;
        document.getElementById('stat-downloads').textContent = auditStats?.total_downloads || 0;

        // Recent uploads
        const recentUploadsEl = document.getElementById('recent-uploads');
        if (myFiles && myFiles.length > 0) {
            recentUploadsEl.innerHTML = myFiles.slice(0, 5).map(f => `
                <div class="file-list-item">
                    <i class="fas fa-file"></i>
                    <div class="file-info">
                        <div class="file-name-sm">${escapeHtml(f.original_filename)}</div>
                        <div class="file-date">${formatDate(f.created_at)}</div>
                    </div>
                </div>
            `).join('');
        } else {
            recentUploadsEl.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No uploads yet</p>';
        }

        // Recent activity
        const logs = await apiRequest('/audit/logs/my?limit=5');
        const recentActivityEl = document.getElementById('recent-activity');
        if (logs && logs.length > 0) {
            recentActivityEl.innerHTML = logs.map(l => `
                <div class="audit-list-item ${l.success ? 'success' : 'failed'}">
                    <i class="fas fa-${getEventIcon(l.event_type)}"></i>
                    <div style="flex: 1;">
                        <div>${escapeHtml(l.event_description)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${formatDate(l.created_at)}</div>
                    </div>
                </div>
            `).join('');
        } else {
            recentActivityEl.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No activity yet</p>';
        }
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

async function loadMyFiles() {
    try {
        // Reset pagination
        paginationState.myFiles = { skip: 0, limit: 20, total: 0, hasMore: true, loading: false };
        filterState.myFiles = { type: '', size: '', date: '' };
        allFiles.myFiles = [];
        
        // NEW (fixed):
const response = await apiRequest('/files/my-files?skip=0&limit=20');

// Handle both array and paginated object responses
if (Array.isArray(response)) {
    // Direct array response
    allFiles.myFiles = response;
    paginationState.myFiles.total = response.length;
    paginationState.myFiles.hasMore = false;
    displayMyFiles();
    setupInfiniteScroll();
} else if (response && response.items) {
    // Paginated object response
    allFiles.myFiles = response.items;
    paginationState.myFiles.total = response.total || 0;
    paginationState.myFiles.hasMore = response.has_more !== false;
    displayMyFiles();
    setupInfiniteScroll();
} else {
    const grid = document.getElementById('my-files-grid');
    const empty = document.getElementById('my-files-empty');
    grid.innerHTML = '';
    empty.classList.remove('hidden');
}
    } catch (error) {
        console.error('Load files error:', error);
    }
}

async function loadSharedFiles() {
    try {
        // Reset pagination
        paginationState.sharedFiles = { skip: 0, limit: 20, total: 0, hasMore: true, loading: false };
        filterState.sharedFiles = { type: '', size: '', date: '', owner: '' };
        allFiles.sharedFiles = [];
        
        const response = await apiRequest('/files/shared-with-me?skip=0&limit=20');

        
        if (Array.isArray(response)) {
    allFiles.sharedFiles = response;
    paginationState.sharedFiles.total = response.length;
    paginationState.sharedFiles.hasMore = false;
    displaySharedFiles();
    setupInfiniteScroll();
} else if (response && response.items) {
    allFiles.sharedFiles = response.items;
    paginationState.sharedFiles.total = response.total || 0;
    paginationState.sharedFiles.hasMore = response.has_more !== false;
    displaySharedFiles();
    setupInfiniteScroll();
} else {
    const grid = document.getElementById('shared-files-grid');
    const empty = document.getElementById('shared-files-empty');
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    }
    } catch (error) {
        console.error('Load shared error:', error);
    }
}

async function loadAuditLogs(filter = 'all') {
    try {
        const logs = await apiRequest('/audit/logs?limit=100');
        const tbody = document.getElementById('audit-table-body');

        if (!logs) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No logs available</td></tr>';
            return;
        }

        const filtered = filter === 'all' ? logs : logs.filter(l => l.event_type === filter);

        tbody.innerHTML = filtered.map(l => `
            <tr>
                <td>${formatDate(l.created_at)}</td>
                <td><span class="status-badge ${l.success ? 'success' : 'failed'}">${l.event_type}</span></td>
                <td>${escapeHtml(l.event_description)}</td>
                <td>${l.ip_address || 'N/A'}</td>
                <td><span class="status-badge ${l.success ? 'success' : 'failed'}">${l.success ? 'Success' : 'Failed'}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Load audit error:', error);
    }
}

// ═══════════════════════════════════════════════════════════════
// MODAL HANDLERS
// ═══════════════════════════════════════════════════════════════

let currentShareFileId = null;

function openShareModal(fileId, filename) {
    currentShareFileId = fileId;
    document.getElementById('share-file-name').textContent = `Sharing: ${filename}`;
    document.getElementById('share-username').value = '';
    elements.shareModal.classList.remove('hidden');
}

function closeShareModal() {
    elements.shareModal.classList.add('hidden');
    currentShareFileId = null;
    selectedShareUser = null;
    document.getElementById('share-username').value = '';
    document.getElementById('user-search-results').classList.add('hidden');
}

async function openDetailsModal(fileId) {
    try {
        const file = await apiRequest(`/files/${fileId}`);
        
        // Populate all detail fields
        document.getElementById('detail-filename').textContent = file.original_filename;
        document.getElementById('detail-filesize').textContent = formatFileSize(file.file_size);
        document.getElementById('detail-filetype').textContent = file.mime_type || 'Unknown';
        document.getElementById('detail-hash').textContent = (file.file_hash || '').substring(0, 16) + '...';
        document.getElementById('detail-owner').textContent = file.owner_username || 'You';
        document.getElementById('detail-created').textContent = formatDate(file.created_at);
        
        // Show signature status if file is signed
        const signatureEl = document.getElementById('detail-signature');
        if (file.file_signature) {
            signatureEl.style.display = 'flex';
        } else {
            signatureEl.style.display = 'none';
        }
        
        elements.detailsModal.classList.remove('hidden');
    } catch (error) {
        showToast('Failed to load file details: ' + error.message, 'error');
    }
}

function closeDetailsModal() {
    elements.detailsModal.classList.add('hidden');
}

async function confirmDelete(fileId, filename) {
    const confirmed = await showConfirmDialog(
        'Delete File?',
        `Are you sure you want to delete "${filename}"? This action cannot be undone and the file will be permanently deleted from the server.`,
        'Delete',
        'Cancel',
        true
    );

    if (confirmed) {
        try {
            // Show loading state
            showToast('Deleting file...', 'info');
            await deleteFile(fileId);
            showToast(`"${filename}" deleted successfully`, 'success');
            loadMyFiles();
            loadDashboard();
        } catch (error) {
            showToast(`Delete failed: ${error.message}`, 'error');
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════════════════════════

function showPage(pageName) {
    elements.pages.forEach(p => p.classList.add('hidden'));
    document.getElementById(`page-${pageName}`).classList.remove('hidden');

    elements.navLinksItems.forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // Load page data
    switch(pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'files':
            loadMyFiles();
            break;
        case 'shared':
            loadSharedFiles();
            break;
        case 'audit':
            loadAuditLogs();
            break;
        case 'upload':
         // Reset upload form when visiting upload page
        elements.fileInput.value = '';
        elements.uploadDetails.classList.add('hidden');
        elements.uploadResult.classList.add('hidden');
        elements.uploadProgress.classList.add('hidden');
        elements.progressFill.style.width = '0%';
        break;    
    }
}

function showToast(message, type = 'info', duration = 4000) {
    // Create container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Determine icon based on type
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const icon = icons[type] || icons['info'];
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="Close notification">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Close button handler
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    });
    
    // Auto-remove after duration
    const timeout = setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
    
    // Clear timeout if manually closed
    closeBtn.addEventListener('click', () => clearTimeout(timeout));
    
    return toast;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleString();
}

function getFileIcon(mimeType) {
    if (!mimeType) return 'fa-file';
    if (mimeType.startsWith('image/')) return 'fa-file-image';
    if (mimeType.startsWith('video/')) return 'fa-file-video';
    if (mimeType.startsWith('audio/')) return 'fa-file-audio';
    if (mimeType.includes('pdf')) return 'fa-file-pdf';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'fa-file-word';
    if (mimeType.includes('excel') || mimeType.includes('sheet')) return 'fa-file-excel';
    if (mimeType.includes('zip') || mimeType.includes('compressed')) return 'fa-file-archive';
    if (mimeType.startsWith('text/')) return 'fa-file-alt';
    return 'fa-file';
}

function getEventIcon(eventType) {
    const icons = {
        'LOGIN_ATTEMPT': 'fa-sign-in-alt',
        'FILE_UPLOAD': 'fa-upload',
        'FILE_DOWNLOAD': 'fa-download',
        'FILE_SHARE': 'fa-share-alt',
        'FAILED_ACCESS': 'fa-exclamation-triangle'
    };
    return icons[eventType] || 'fa-circle';
}

// User search for sharing
let selectedShareUser = null;
let searchTimeout = null;

async function searchUsers(query) {
    if (query.length < 2) {
        document.getElementById('user-search-results').classList.add('hidden');
        return;
    }
    
    try {
        const users = await apiRequest(`/auth/users/search?query=${encodeURIComponent(query)}`);
        const resultsEl = document.getElementById('user-search-results');
        
        if (users && users.length > 0) {
            resultsEl.innerHTML = users.map(u => `
                <div class="search-result-item" data-username="${escapeHtml(u.username)}" data-userid="${u.id}">
                    <div class="username">${escapeHtml(u.username)}</div>
                    <div class="email">${escapeHtml(u.email)}</div>
                </div>
            `).join('');
            resultsEl.classList.remove('hidden');
            
            // Add click handlers
            resultsEl.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    selectedShareUser = item.dataset.username;
                    document.getElementById('share-username').value = selectedShareUser;
                    resultsEl.classList.add('hidden');
                });
            });
        } else {
            resultsEl.innerHTML = '<div class="search-result-item"><div class="username">No users found</div></div>';
            resultsEl.classList.remove('hidden');
        }
    } catch (error) {
        console.error('User search error:', error);
    }
}

// Update share modal input
document.getElementById('share-username').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    selectedShareUser = null;
    searchTimeout = setTimeout(() => searchUsers(e.target.value.trim()), 300);
});

// Close search results when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('#share-username') && !e.target.closest('#user-search-results')) {
        document.getElementById('user-search-results').classList.add('hidden');
    }
});

// ═══════════════════════════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════

// Auth tabs
elements.authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        elements.authTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const tabName = tab.dataset.tab;
        if (tabName === 'login') {
            elements.loginForm.classList.remove('hidden');
            elements.registerForm.classList.add('hidden');
        } else {
            elements.loginForm.classList.add('hidden');
            elements.registerForm.classList.remove('hidden');
        }
    });
});

// Login form
elements.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    if (!username.trim() || !password.trim()) {
        showToast('Please fill in all fields', 'warning');
        return;
    }

    // Show loading state
    const submitBtn = elements.loginForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        await login(username, password);
        currentUser = await getCurrentUser();
        elements.userName.textContent = currentUser.username;
        showApp();
        showPage('dashboard');
        showToast(`Welcome back, ${currentUser.username}!`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Register form
elements.registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    // Validate inputs
    const usernameValidation = validateUsername(username);
    const emailValidation = validateEmail(email);
    const passwordValidation = validatePassword(password);

    if (!usernameValidation.valid) {
        showToast(usernameValidation.message, 'warning');
        return;
    }
    if (!emailValidation.valid) {
        showToast(emailValidation.message, 'warning');
        return;
    }
    if (!passwordValidation.valid) {
        showToast(passwordValidation.message, 'warning');
        return;
    }

    // Show loading state
    const submitBtn = elements.registerForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        await register(username, email, password);
        showToast('Registration successful! Please log in with your credentials.', 'success');

        // Switch to login tab and pre-fill username
        elements.authTabs[0].click();
        document.getElementById('login-username').value = username;
        document.getElementById('login-password').focus();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Logout
elements.logoutBtn.addEventListener('click', logout);

// Navigation
elements.navLinksItems.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        showPage(link.dataset.page);
    });
});

// Upload zone
elements.uploadZone.addEventListener('click', () => elements.fileInput.click());

elements.uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadZone.classList.add('dragover');
});

elements.uploadZone.addEventListener('dragleave', () => {
    elements.uploadZone.classList.remove('dragover');
});

elements.uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileSelect(files[0]);
});

elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
});

function handleFileSelect(file) {
    elements.uploadDetails.classList.remove('hidden');
    elements.uploadFilename.textContent = file.name;
    elements.uploadFilesize.textContent = formatFileSize(file.size);
    elements.uploadResult.classList.add('hidden');
    elements.uploadProgress.classList.add('hidden');
    elements.progressFill.style.width = '0%';
}

elements.uploadBtn.addEventListener('click', async () => {
    const file = elements.fileInput.files[0];
    if (!file) {
        showToast('Please select a file first', 'warning');
        return;
    }

    // Validate file size (e.g., max 500MB)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('File size exceeds 500MB limit', 'error');
        return;
    }

    const signFile = document.getElementById('sign-file').checked;
    
    // Show loading state
    elements.uploadBtn.disabled = true;
    elements.uploadBtn.classList.add('loading');

    try {
        await uploadFile(file, signFile);
    } catch (error) {
        // Error already handled in uploadFile
        console.error('Upload error:', error);
    } finally {
        elements.uploadBtn.disabled = false;
        elements.uploadBtn.classList.remove('loading');
    }
});

// Share modal
document.getElementById('share-confirm').addEventListener('click', async () => {
    const usernameInput = document.getElementById('share-username').value.trim();
    const username = selectedShareUser || usernameInput;
    const canDownload = document.getElementById('share-download').checked;
    const confirmBtn = document.getElementById('share-confirm');
    const originalText = confirmBtn.innerHTML;

    if (!username) {
        showToast('Please select a user to share with', 'warning');
        return;
    }

    // Show loading state
    confirmBtn.classList.add('loading');
    confirmBtn.disabled = true;

    try {
        await shareFile(currentShareFileId, username, canDownload);
        showToast(`File shared with ${username} successfully!`, 'success');
        closeShareModal();
        loadMyFiles();
    } catch (error) {
        const errorMsg = error.message || 'Failed to share file';
        showToast(errorMsg, 'error');
    } finally {
        confirmBtn.classList.remove('loading');
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = originalText;
    }
});

document.getElementById('share-cancel').addEventListener('click', closeShareModal);
document.getElementById('modal-close').addEventListener('click', closeShareModal);

// Details modal
document.getElementById('details-close').addEventListener('click', closeDetailsModal);
document.getElementById('details-close-btn').addEventListener('click', closeDetailsModal);

// Audit filters
elements.auditFilters.forEach(btn => {
    btn.addEventListener('click', () => {
        elements.auditFilters.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        loadAuditLogs(btn.dataset.filter);
    });
});

// Close modals on outside click
window.addEventListener('click', (e) => {
    if (e.target === elements.shareModal) closeShareModal();
    if (e.target === elements.detailsModal) closeDetailsModal();
});

// ═══════════════════════════════════════════════════════════════
// SEARCH AND FILTER
// ═══════════════════════════════════════════════════════════════

// Global filter state
let filterState = {
    myFiles: {
        type: '',
        size: '',
        date: ''
    },
    sharedFiles: {
        type: '',
        size: '',
        date: '',
        owner: ''
    }
};

// Infinite scroll state
let paginationState = {
    myFiles: { skip: 0, limit: 20, total: 0, hasMore: true, loading: false },
    sharedFiles: { skip: 0, limit: 20, total: 0, hasMore: true, loading: false }
};

let allFiles = {
    myFiles: [],
    sharedFiles: []
};

function createSearchInput() {
    /**Add search bar to file pages */
    const searchHTML = `
        <div style="margin-bottom: 1rem; display: flex; gap: 0.5rem;">
            <input type="text" id="search-input" placeholder="🔍 Search files..." 
                style="flex: 1; padding: 0.5rem 1rem; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text);">
        </div>
    `;
    return searchHTML;
}

function filterAndSearchFiles(files, query) {
    if (!query) return files;
    const lowerQuery = query.toLowerCase();
    return files.filter(file => 
        file.original_filename.toLowerCase().includes(lowerQuery) ||
        file.owner_username?.toLowerCase().includes(lowerQuery)
    );
}

function getFileExtension(filename) {
    return filename.split('.').pop().toLowerCase();
}

function getFileTypeCategory(mimeType, filename) {
    const ext = getFileExtension(filename);
    
    // Document types
    if (['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'ppt', 'pptx'].includes(ext)) {
        return 'document';
    }
    // Image types
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
        return 'image';
    }
    // Video types
    if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'].includes(ext)) {
        return 'video';
    }
    // Audio types
    if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma'].includes(ext)) {
        return 'audio';
    }
    // Archive types
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext)) {
        return 'archive';
    }
    return 'other';
}

function applyFilters(files, filters) {
    return files.filter(file => {
        // Type filter
        if (filters.type) {
            const fileType = getFileTypeCategory(file.mime_type, file.original_filename);
            if (fileType !== filters.type) return false;
        }
        
        // Size filter
        if (filters.size) {
            const sizeInMB = file.file_size / (1024 * 1024);
            if (filters.size === 'small' && sizeInMB >= 1) return false;
            if (filters.size === 'medium' && (sizeInMB < 1 || sizeInMB > 50)) return false;
            if (filters.size === 'large' && sizeInMB <= 50) return false;
        }
        
        // Date filter
        if (filters.date) {
            const fileDate = new Date(file.created_at);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (filters.date === 'today') {
                const fileDay = new Date(fileDate);
                fileDay.setHours(0, 0, 0, 0);
                if (fileDay.getTime() !== today.getTime()) return false;
            } else if (filters.date === 'week') {
                const weekAgo = new Date(today);
                weekAgo.setDate(weekAgo.getDate() - 7);
                if (fileDate < weekAgo) return false;
            } else if (filters.date === 'month') {
                const monthAgo = new Date(today);
                monthAgo.setMonth(monthAgo.getMonth() - 1);
                if (fileDate < monthAgo) return false;
            } else if (filters.date === 'year') {
                const yearAgo = new Date(today);
                yearAgo.setFullYear(yearAgo.getFullYear() - 1);
                if (fileDate < yearAgo) return false;
            }
        }
        
        // Owner filter (for shared files)
        if (filters.owner) {
            const ownerLower = filters.owner.toLowerCase();
            if (!file.owner_username?.toLowerCase().includes(ownerLower)) return false;
        }
        
        return true;
    });
}

function setupFilterListeners() {
    // My Files Filters
    const toggleFiltersBtnMy = document.getElementById('toggle-filters-my');
    const clearFiltersBtnMy = document.getElementById('clear-filters-my');
    const filterContainerMy = document.getElementById('my-files-filters');
    
    if (toggleFiltersBtnMy) {
        toggleFiltersBtnMy.addEventListener('click', () => {
            if (filterContainerMy.style.display === 'none') {
                filterContainerMy.style.display = 'block';
                toggleFiltersBtnMy.textContent = '🔽 Hide Filters';
            } else {
                filterContainerMy.style.display = 'none';
                toggleFiltersBtnMy.textContent = '🔼 Show Filters';
            }
        });
    }
    
    if (clearFiltersBtnMy) {
        clearFiltersBtnMy.addEventListener('click', () => {
            filterState.myFiles = { type: '', size: '', date: '' };
            document.getElementById('filter-type-my').value = '';
            document.getElementById('filter-size-my').value = '';
            document.getElementById('filter-date-my').value = '';
            loadMyFiles();
        });
    }
    
    // Filter change listeners for My Files
    const typeSelectMy = document.getElementById('filter-type-my');
    const sizeSelectMy = document.getElementById('filter-size-my');
    const dateSelectMy = document.getElementById('filter-date-my');
    
    if (typeSelectMy) {
        typeSelectMy.addEventListener('change', (e) => {
            filterState.myFiles.type = e.target.value;
            loadMyFiles();
        });
    }
    if (sizeSelectMy) {
        sizeSelectMy.addEventListener('change', (e) => {
            filterState.myFiles.size = e.target.value;
            loadMyFiles();
        });
    }
    if (dateSelectMy) {
        dateSelectMy.addEventListener('change', (e) => {
            filterState.myFiles.date = e.target.value;
            loadMyFiles();
        });
    }
    
    // Shared Files Filters
    const toggleFiltersBtnShared = document.getElementById('toggle-filters-shared');
    const clearFiltersBtnShared = document.getElementById('clear-filters-shared');
    const filterContainerShared = document.getElementById('shared-files-filters');
    
    if (toggleFiltersBtnShared) {
        toggleFiltersBtnShared.addEventListener('click', () => {
            if (filterContainerShared.style.display === 'none') {
                filterContainerShared.style.display = 'block';
                toggleFiltersBtnShared.textContent = '🔽 Hide Filters';
            } else {
                filterContainerShared.style.display = 'none';
                toggleFiltersBtnShared.textContent = '🔼 Show Filters';
            }
        });
    }
    
    if (clearFiltersBtnShared) {
        clearFiltersBtnShared.addEventListener('click', () => {
            filterState.sharedFiles = { type: '', size: '', date: '', owner: '' };
            document.getElementById('filter-type-shared').value = '';
            document.getElementById('filter-size-shared').value = '';
            document.getElementById('filter-owner-shared').value = '';
            loadSharedFiles();
        });
    }
    
    // Filter change listeners for Shared Files
    const typeSelectShared = document.getElementById('filter-type-shared');
    const sizeSelectShared = document.getElementById('filter-size-shared');
    const ownerInputShared = document.getElementById('filter-owner-shared');
    
    if (typeSelectShared) {
        typeSelectShared.addEventListener('change', (e) => {
            filterState.sharedFiles.type = e.target.value;
            loadSharedFiles();
        });
    }
    if (sizeSelectShared) {
        sizeSelectShared.addEventListener('change', (e) => {
            filterState.sharedFiles.size = e.target.value;
            loadSharedFiles();
        });
    }
    if (ownerInputShared) {
        ownerInputShared.addEventListener('input', (e) => {
            filterState.sharedFiles.owner = e.target.value;
            loadSharedFiles();
        });
    }
}

// ═══════════════════════════════════════════════════════════════
// INFINITE SCROLL
// ═══════════════════════════════════════════════════════════════

async function loadMoreMyFiles() {
    if (paginationState.myFiles.loading || !paginationState.myFiles.hasMore) return;
    
    paginationState.myFiles.loading = true;
    const loadingEl = document.getElementById('infinite-scroll-my');
    if (loadingEl) loadingEl.style.display = 'block';
    
    try {
        const skip = paginationState.myFiles.skip + paginationState.myFiles.limit;
        // NEW:
        const response = await apiRequest(`/files/my-files?skip=${skip}&limit=${paginationState.myFiles.limit}`);

        if (Array.isArray(response)) {
        allFiles.myFiles = allFiles.myFiles.concat(response);
        paginationState.myFiles.hasMore = response.length === paginationState.myFiles.limit;
        displayMyFiles();
        } else if (response && response.items) {
        allFiles.myFiles = allFiles.myFiles.concat(response.items);
        paginationState.myFiles.hasMore = response.has_more !== false;
        displayMyFiles();
        }

    } catch (error) {
        console.error('Error loading more files:', error);
    } finally {
        paginationState.myFiles.loading = false;
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

async function loadMoreSharedFiles() {
    if (paginationState.sharedFiles.loading || !paginationState.sharedFiles.hasMore) return;
    
    paginationState.sharedFiles.loading = true;
    const loadingEl = document.getElementById('infinite-scroll-shared');
    if (loadingEl) loadingEl.style.display = 'block';
    
    try {
        const skip = paginationState.sharedFiles.skip + paginationState.sharedFiles.limit;
        const response = await apiRequest(`/files/shared-with-me?skip=${skip}&limit=${paginationState.sharedFiles.limit}`);
        
        if (Array.isArray(response)) {
            allFiles.sharedFiles = allFiles.sharedFiles.concat(response);
            paginationState.sharedFiles.hasMore = response.length === paginationState.sharedFiles.limit;
            displaySharedFiles();
        } else if (response && response.items) {
            allFiles.sharedFiles = allFiles.sharedFiles.concat(response.items);
            paginationState.sharedFiles.skip = skip;
            paginationState.sharedFiles.hasMore = response.has_more !== false;
            displaySharedFiles();
        }
    } catch (error) {
        console.error('Error loading more shared files:', error);
    } finally {
        paginationState.sharedFiles.loading = false;
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

function displayMyFiles() {
    const grid = document.getElementById('my-files-grid');
    const empty = document.getElementById('my-files-empty');
    
    // Apply filters to all files
    let filteredFiles = applyFilters(allFiles.myFiles, filterState.myFiles);
    
    if (filteredFiles.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        if (allFiles.myFiles.length === 0) {
            empty.innerHTML = `
                <i class="fas fa-cloud-upload-alt"></i>
                <p>No files uploaded yet</p>
                <small>Start by uploading a file from the <strong>Upload</strong> page.<br>Files are encrypted with AES-256-GCM for security.</small>
            `;
        } else {
            empty.innerHTML = `
                <i class="fas fa-search"></i>
                <p>No files match your filters</p>
                <small>Try adjusting your search or filter settings.</small>
            `;
        }
        return;
    }
    
    empty.classList.add('hidden');
    grid.innerHTML = filteredFiles.map(f => `
        <div class="file-card">
            <div class="file-icon"><i class="fas ${getFileIcon(f.mime_type)}"></i></div>
            <div class="file-name">${escapeHtml(f.original_filename)}</div>
            <div class="file-meta">${formatFileSize(f.file_size)} · ${formatDate(f.created_at)}</div>
            <div class="file-actions">
                <button class="btn btn-sm btn-primary" onclick="downloadFile('${f.id}', '${escapeHtml(f.original_filename).replace(/'/g, "\\'")}')">
                    <i class="fas fa-download"></i> Download
                </button>
                <button class="btn btn-sm btn-outline" onclick="openShareModal('${f.id}', '${escapeHtml(f.original_filename).replace(/'/g, "\\'")}')">
                    <i class="fas fa-share-alt"></i> Share
                </button>
                <button class="btn btn-sm btn-outline" onclick="openDetailsModal('${f.id}')">
                    <i class="fas fa-info"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="confirmDelete('${f.id}', '${escapeHtml(f.original_filename).replace(/'/g, "\\'")}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function displaySharedFiles() {
    const grid = document.getElementById('shared-files-grid');
    const empty = document.getElementById('shared-files-empty');
    
    // Apply filters to all files
    let filteredFiles = applyFilters(allFiles.sharedFiles, filterState.sharedFiles);
    
    if (filteredFiles.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        if (allFiles.sharedFiles.length === 0) {
            empty.innerHTML = `
                <i class="fas fa-inbox"></i>
                <p>No files shared with you yet</p>
                <small>When someone shares a file with you, it will appear here.<br>Shared files are end-to-end encrypted.</small>
            `;
        } else {
            empty.innerHTML = `
                <i class="fas fa-search"></i>
                <p>No files match your filters</p>
                <small>Try adjusting your search or filter settings.</small>
            `;
        }
        return;
    }
    
    empty.classList.add('hidden');
    grid.innerHTML = filteredFiles.map(f => `
        <div class="file-card">
            <div class="file-icon"><i class="fas ${getFileIcon(f.mime_type)}"></i></div>
            <div class="file-name">${escapeHtml(f.original_filename)}</div>
            <div class="file-meta">From: ${escapeHtml(f.owner_username)} · ${formatFileSize(f.file_size)}</div>
            <div class="file-actions">
                <button class="btn btn-sm btn-primary" onclick="downloadFile('${f.id}', '${escapeHtml(f.original_filename).replace(/'/g, "\\'")}')">
                    <i class="fas fa-download"></i> Download
                </button>
                <button class="btn btn-sm btn-outline" onclick="openDetailsModal('${f.id}')">
                    <i class="fas fa-info"></i> Details
                </button>
            </div>
        </div>
    `).join('');
}

function setupInfiniteScroll() {
    // My Files infinite scroll
    const myFilesGrid = document.getElementById('my-files-grid');
    if (myFilesGrid) {
        const myFilesObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && paginationState.myFiles.hasMore) {
                    loadMoreMyFiles();
                }
            });
        }, { threshold: 0.5 });
        
        myFilesObserver.observe(document.getElementById('infinite-scroll-my') || myFilesGrid);
    }
    
    // Shared Files infinite scroll
    const sharedFilesGrid = document.getElementById('shared-files-grid');
    if (sharedFilesGrid) {
        const sharedFilesObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && paginationState.sharedFiles.hasMore) {
                    loadMoreSharedFiles();
                }
            });
        }, { threshold: 0.5 });
        
        sharedFilesObserver.observe(document.getElementById('infinite-scroll-shared') || sharedFilesGrid);
    }
}

// ═══════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════════════════

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Prevent shortcuts when typing in input fields
        if (event.target.tagName === 'INPUT' && event.key !== 'Escape') {
            return;
        }

        switch(event.key) {
            case '/':
                event.preventDefault();
                // Focus search input based on current page
                const currentPage = document.querySelector('.page:not(.hidden)');
                if (currentPage) {
                    const searchInput = currentPage.querySelector('input[type="text"][placeholder*="Search"]');
                    if (searchInput) {
                        searchInput.focus();
                        showToast('🔍 Search focused', 'info');
                    }
                }
                break;

            case '?':
                event.preventDefault();
                showKeyboardShortcutsHelp();
                break;

            case 'Escape':
                // Close any open modals
                if (!elements.shareModal.classList.contains('hidden')) {
                    closeShareModal();
                }
                if (!elements.detailsModal.classList.contains('hidden')) {
                    closeDetailsModal();
                }
                showToast('Modals closed', 'info');
                break;

            case 'd':
            case 'D':
                if (event.ctrlKey || event.metaKey) return; // Ignore Ctrl+D (browser bookmark)
                event.preventDefault();
                // Download first visible file card
                const downloadBtn = document.querySelector('.page:not(.hidden) .file-card:first-child .btn-primary');
                if (downloadBtn) {
                    downloadBtn.click();
                    showToast('⬇️ Downloading first file...', 'info');
                } else {
                    showToast('❌ No files available to download', 'warning');
                }
                break;

            case 's':
            case 'S':
                if (event.ctrlKey || event.metaKey) return; // Ignore Ctrl+S (browser save)
                event.preventDefault();
                // Share first visible file card
                const shareBtn = document.querySelector('.page:not(.hidden) .file-card:first-child [onclick*="Share"]');
                if (shareBtn) {
                    shareBtn.click();
                    showToast('📤 Share modal opened for first file...', 'info');
                } else {
                    showToast('❌ No files available to share', 'warning');
                }
                break;

            case 'Delete':
                event.preventDefault();
                // Delete first visible file card
                const deleteBtn = document.querySelector('.page:not(.hidden) .file-card:first-child .btn-danger');
                if (deleteBtn) {
                    deleteBtn.click();
                    showToast('🗑️ Delete prompt opened for first file...', 'info');
                } else {
                    showToast('❌ No files available to delete', 'warning');
                }
                break;

            case 'h':
            case 'H':
                if (!event.ctrlKey && !event.metaKey && !event.altKey) {
                    event.preventDefault();
                    showKeyboardShortcutsHelp();
                }
                break;
        }
    });
}

function showKeyboardShortcutsHelp() {
    const helpContent = `
        <div style="font-family: monospace; line-height: 1.8;">
            <h3 style="margin-top: 0; color: var(--primary);">Keyboard Shortcuts</h3>
            <div style="display: grid; gap: 0.5rem; font-size: 0.9rem;">
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">/</kbd>
                    <span>Focus search bar</span>
                </div>
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">D</kbd>
                    <span>Download first file</span>
                </div>
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">S</kbd>
                    <span>Share first file</span>
                </div>
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">Delete</kbd>
                    <span>Delete first file</span>
                </div>
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">Esc</kbd>
                    <span>Close modals</span>
                </div>
                <div style="display: grid; grid-template-columns: 80px 1fr; gap: 1rem;">
                    <kbd style="background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px;">?</kbd>
                    <span>Show this help (or press H)</span>
                </div>
            </div>
            <p style="margin-top: 1rem; color: var(--text-muted); font-size: 0.85rem;">
                ✨ Use shortcuts to navigate faster!<br>
                💡 Shortcuts are disabled while typing in search fields
            </p>
        </div>
    `;

    // Create help modal
    const helpModal = document.createElement('div');
    helpModal.className = 'modal';
    helpModal.style.display = 'flex';
    helpModal.innerHTML = `
        <div class="modal-content" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);">
            <div class="modal-header">
                <h3><i class="fas fa-keyboard"></i> Keyboard Shortcuts</h3>
                <button style="background: none; border: none; color: var(--text); font-size: 1.5rem; cursor: pointer;">&times;</button>
            </div>
            <div class="modal-body" style="max-width: 400px;">
                ${helpContent}
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary">Got it!</button>
            </div>
        </div>
    `;

    // Close button handlers
    const closeBtn = helpModal.querySelector('.modal-header button');
    const confirmBtn = helpModal.querySelector('.btn-primary');
    
    closeBtn.addEventListener('click', () => helpModal.remove());
    confirmBtn.addEventListener('click', () => helpModal.remove());
    
    // Close on outside click
    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) helpModal.remove();
    });

    document.body.appendChild(helpModal);
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

async function init() {
    if (currentToken) {
        try {
            currentUser = await getCurrentUser();
            if (currentUser) {
                elements.userName.textContent = currentUser.username;
                showApp();
                showPage('dashboard');
                setupFilterListeners();
                setupKeyboardShortcuts();
            } else {
                logout();
            }
        } catch (error) {
            logout();
        }
    } else {
        showAuth();
    }
}




// Make functions available for inline onclick handlers
window.downloadFile = downloadFile;
window.openShareModal = openShareModal;
window.openDetailsModal = openDetailsModal;
window.confirmDelete = confirmDelete;
window.shareFile = shareFile;
window.deleteFile = deleteFile;
window.verifySignature = verifySignature;
window.closeShareModal = closeShareModal;
window.closeDetailsModal = closeDetailsModal;

// Start the app
init();
