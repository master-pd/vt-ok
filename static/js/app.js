// TikTok Bot Admin Panel - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initSidebar();
    initCharts();
    initTables();
    initModals();
    initForms();
    initNotifications();
    initTheme();
    initStats();
    initRealTimeUpdates();
});

// Sidebar Toggle
function initSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            document.body.appendChild(overlay);
            document.body.style.overflow = 'hidden';
        });
    }
    
    document.addEventListener('click', function(e) {
        if (sidebar.classList.contains('active') && 
            !sidebar.contains(e.target) && 
            !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('active');
            if (overlay.parentNode) {
                overlay.remove();
            }
            document.body.style.overflow = '';
        }
    });
}

// Charts Initialization
function initCharts() {
    // Revenue Chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        new Chart(revenueCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Revenue',
                    data: [1200, 1900, 3000, 5000, 2000, 3000, 4500, 3500, 4800, 6000, 7500, 9000],
                    borderColor: '#ff0050',
                    backgroundColor: 'rgba(255, 0, 80, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff',
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    }
                }
            }
        });
    }
    
    // Users Chart
    const usersCtx = document.getElementById('usersChart');
    if (usersCtx) {
        new Chart(usersCtx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'New Users',
                    data: [65, 59, 80, 81, 56, 55, 40],
                    backgroundColor: 'rgba(0, 242, 234, 0.8)',
                    borderColor: '#00f2ea',
                    borderWidth: 2
                }, {
                    label: 'Active Users',
                    data: [28, 48, 40, 19, 86, 27, 90],
                    backgroundColor: 'rgba(255, 0, 80, 0.8)',
                    borderColor: '#ff0050',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    }
                }
            }
        });
    }
    
    // Orders Chart
    const ordersCtx = document.getElementById('ordersChart');
    if (ordersCtx) {
        new Chart(ordersCtx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Processing', 'Pending', 'Failed'],
                datasets: [{
                    data: [300, 50, 100, 20],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(0, 242, 234, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(220, 53, 69, 0.8)'
                    ],
                    borderColor: [
                        '#28a745',
                        '#00f2ea',
                        '#ffc107',
                        '#dc3545'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            padding: 20
                        }
                    }
                }
            }
        });
    }
}

// Tables Initialization
function initTables() {
    // DataTables initialization
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        if ($.fn.DataTable) {
            $(table).DataTable({
                language: {
                    search: "_INPUT_",
                    searchPlaceholder: "Search...",
                    lengthMenu: "_MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    infoEmpty: "Showing 0 to 0 of 0 entries",
                    infoFiltered: "(filtered from _MAX_ total entries)",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                },
                pageLength: 25,
                responsive: true,
                order: [[0, 'desc']],
                dom: '<"table-header"lf>rt<"table-footer"ip>'
            });
        }
    });
    
    // Table row actions
    document.querySelectorAll('.table-action').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const action = this.dataset.action;
            const row = this.closest('tr');
            const id = row.dataset.id;
            
            switch(action) {
                case 'view':
                    viewItem(id);
                    break;
                case 'edit':
                    editItem(id);
                    break;
                case 'delete':
                    deleteItem(id);
                    break;
                case 'approve':
                    approveItem(id);
                    break;
                case 'reject':
                    rejectItem(id);
                    break;
            }
        });
    });
}

// Modals Initialization
function initModals() {
    // Open modal
    document.querySelectorAll('[data-modal]').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            openModal(modalId);
        });
    });
    
    // Close modal
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(button => {
        button.addEventListener('click', function() {
            closeModal(this.closest('.modal'));
        });
    });
    
    // Close modal on overlay click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                closeModal(modal);
            });
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Forms Initialization
function initForms() {
    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
            showLoading(this);
        });
    });
    
    // File upload preview
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const preview = document.getElementById(this.dataset.preview);
            if (preview && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
    
    // Form switches
    document.querySelectorAll('.form-switch input').forEach(switchInput => {
        switchInput.addEventListener('change', function() {
            const status = this.checked ? 'active' : 'inactive';
            updateStatus(this.dataset.target, status);
        });
    });
    
    // Search forms
    document.querySelectorAll('.search-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = this.querySelector('input').value;
            searchItems(query);
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const required = form.querySelectorAll('[required]');
    
    required.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'This field is required');
        } else {
            hideError(input);
        }
    });
    
    // Email validation
    const emailInputs = form.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        if (input.value && !isValidEmail(input.value)) {
            isValid = false;
            showError(input, 'Please enter a valid email address');
        }
    });
    
    // Password confirmation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        isValid = false;
        showError(confirmPassword, 'Passwords do not match');
    }
    
    return isValid;
}

function showError(input, message) {
    const formGroup = input.closest('.form-group');
    formGroup.classList.add('has-error');
    
    let errorElement = formGroup.querySelector('.form-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        formGroup.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

function hideError(input) {
    const formGroup = input.closest('.form-group');
    formGroup.classList.remove('has-error');
    
    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
        errorElement.remove();
    }
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showLoading(form) {
    const button = form.querySelector('button[type="submit"]');
    if (button) {
        const originalText = button.textContent;
        button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
        button.disabled = true;
        
        // Restore button after 5 seconds (in case of error)
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 5000);
    }
}

// Notifications System
function initNotifications() {
    // Toast notifications
    window.showToast = function(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${getToastIcon(type)}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        document.body.appendChild(toast);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
        
        // Auto remove
        setTimeout(() => {
            toast.remove();
        }, duration);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
    };
    
    // Notification bell
    const notificationBell = document.querySelector('.notification-bell');
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            fetchNotifications();
            this.classList.toggle('active');
        });
    }
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Theme Management
function initTheme() {
    const themeToggle = document.querySelector('.theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Set initial theme
    document.body.classList.toggle('dark-mode', currentTheme === 'dark');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const isDark = document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            updateThemeIcon(isDark);
        });
        
        updateThemeIcon(currentTheme === 'dark');
    }
}

function updateThemeIcon(isDark) {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// Statistics Management
function initStats() {
    // Update stats periodically
    setInterval(updateStats, 30000); // Every 30 seconds
    
    // Initial update
    updateStats();
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            const stat = card.dataset.stat;
            if (stats[stat]) {
                const valueElement = card.querySelector('.stat-value');
                if (valueElement) {
                    const oldValue = parseFloat(valueElement.textContent.replace(/[^0-9.-]+/g, ''));
                    const newValue = stats[stat].value;
                    
                    valueElement.textContent = formatStatValue(stat, newValue);
                    
                    // Show change if exists
                    if (stats[stat].change !== undefined) {
                        updateStatChange(card, stats[stat].change);
                    }
                    
                    // Animate change
                    animateValueChange(valueElement, oldValue, newValue);
                }
            }
        });
        
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

function formatStatValue(stat, value) {
    switch(stat) {
        case 'revenue':
            return `$${value.toLocaleString()}`;
        case 'users':
        case 'orders':
        case 'views':
            return value.toLocaleString();
        case 'success_rate':
            return `${value}%`;
        default:
            return value;
    }
}

function updateStatChange(card, change) {
    let changeElement = card.querySelector('.stat-change');
    if (!changeElement) {
        changeElement = document.createElement('div');
        changeElement.className = 'stat-change';
        card.appendChild(changeElement);
    }
    
    changeElement.textContent = change >= 0 ? `+${change}%` : `${change}%`;
    changeElement.className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
}

function animateValueChange(element, oldValue, newValue) {
    if (oldValue === newValue) return;
    
    const duration = 1000;
    const start = Date.now();
    
    function update() {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        const current = oldValue + (newValue - oldValue) * progress;
        
        element.textContent = formatStatValue(element.closest('.stat-card').dataset.stat, current);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Real-time Updates
function initRealTimeUpdates() {
    // WebSocket connection for real-time updates
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    
    try {
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket connected');
        };
        
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        socket.onclose = function() {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(initRealTimeUpdates, 3000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
    } catch (error) {
        console.error('WebSocket initialization failed:', error);
    }
}

function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'new_order':
            showToast(`New order: ${data.order_id}`, 'info');
            updateOrdersTable(data.order);
            break;
        case 'order_update':
            showToast(`Order ${data.order_id} updated: ${data.status}`, 'info');
            updateOrderStatus(data.order_id, data.status);
            break;
        case 'new_user':
            showToast(`New user registered: ${data.username}`, 'success');
            updateUsersTable(data.user);
            break;
        case 'payment_received':
            showToast(`Payment received: $${data.amount}`, 'success');
            updateRevenue(data.amount);
            break;
        case 'system_alert':
            showToast(`System alert: ${data.message}`, 'warning');
            break;
    }
}

function updateOrdersTable(order) {
    const table = document.querySelector('.orders-table');
    if (table && $.fn.DataTable) {
        const tableApi = $(table).DataTable();
        tableApi.row.add([
            order.id,
            order.video_id,
            order.view_count,
            order.status,
            order.created_at,
            getOrderActions(order.id)
        ]).draw();
    }
}

function updateOrderStatus(orderId, status) {
    const row = document.querySelector(`tr[data-id="${orderId}"]`);
    if (row) {
        const statusCell = row.querySelector('.order-status');
        if (statusCell) {
            statusCell.textContent = status;
            statusCell.className = `order-status status-${status}`;
        }
    }
}

function updateUsersTable(user) {
    // Similar to updateOrdersTable
}

function updateRevenue(amount) {
    // Update revenue stat
}

function getOrderActions(orderId) {
    return `
        <div class="table-actions">
            <button class="btn btn-sm btn-outline" data-action="view" data-id="${orderId}">
                <i class="fas fa-eye"></i>
            </button>
            <button class="btn btn-sm btn-outline" data-action="edit" data-id="${orderId}">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline btn-danger" data-action="delete" data-id="${orderId}">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
}

// Search Functionality
function searchItems(query) {
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('/users')) {
        searchUsers(query);
    } else if (currentPage.includes('/orders')) {
        searchOrders(query);
    } else if (currentPage.includes('/payments')) {
        searchPayments(query);
    }
}

async function searchUsers(query) {
    try {
        const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`);
        const users = await response.json();
        renderSearchResults(users, 'users');
    } catch (error) {
        showToast('Failed to search users', 'error');
    }
}

async function searchOrders(query) {
    try {
        const response = await fetch(`/api/orders/search?q=${encodeURIComponent(query)}`);
        const orders = await response.json();
        renderSearchResults(orders, 'orders');
    } catch (error) {
        showToast('Failed to search orders', 'error');
    }
}

function renderSearchResults(results, type) {
    const container = document.querySelector('.search-results');
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<div class="empty-state">No results found</div>';
        return;
    }
    
    let html = '';
    results.forEach(item => {
        html += getSearchResultItem(item, type);
    });
    
    container.innerHTML = html;
    container.classList.add('active');
}

function getSearchResultItem(item, type) {
    switch(type) {
        case 'users':
            return `
                <div class="search-result-item">
                    <div class="result-avatar">${item.username.charAt(0).toUpperCase()}</div>
                    <div class="result-content">
                        <div class="result-title">@${item.username}</div>
                        <div class="result-subtitle">${item.email}</div>
                    </div>
                    <div class="result-actions">
                        <button class="btn btn-sm btn-outline" onclick="viewUser(${item.id})">View</button>
                    </div>
                </div>
            `;
        case 'orders':
            return `
                <div class="search-result-item">
                    <div class="result-icon"><i class="fas fa-shopping-cart"></i></div>
                    <div class="result-content">
                        <div class="result-title">Order #${item.id}</div>
                        <div class="result-subtitle">${item.video_url}</div>
                    </div>
                    <div class="result-actions">
                        <button class="btn btn-sm btn-outline" onclick="viewOrder(${item.id})">View</button>
                    </div>
                </div>
            `;
        default:
            return '';
    }
}

// Export functionality
function exportData(format, type) {
    const query = new URLSearchParams(window.location.search);
    query.set('format', format);
    
    window.open(`/api/${type}/export?${query.toString()}`, '_blank');
}

// Print functionality
function printPage() {
    window.print();
}

// CSV Import
function importCSV(file, type) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    
    fetch('/api/import', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Imported ${data.count} items successfully`, 'success');
            location.reload();
        } else {
            showToast(`Import failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showToast('Import failed', 'error');
    });
}

// Date Range Picker
function initDateRangePicker() {
    $('.date-range-picker').daterangepicker({
        opens: 'left',
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        startDate: moment().subtract(29, 'days'),
        endDate: moment(),
        locale: {
            format: 'YYYY-MM-DD'
        }
    }, function(start, end, label) {
        updateDateRange(start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'));
    });
}

function updateDateRange(start, end) {
    const url = new URL(window.location);
    url.searchParams.set('start_date', start);
    url.searchParams.set('end_date', end);
    window.location = url.toString();
}

// Image Upload with Preview
function initImageUpload() {
    document.querySelectorAll('.image-upload').forEach(upload => {
        const input = upload.querySelector('input[type="file"]');
        const preview = upload.querySelector('.image-preview');
        const removeBtn = upload.querySelector('.remove-image');
        
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    if (removeBtn) removeBtn.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
        
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                input.value = '';
                preview.src = '';
                preview.style.display = 'none';
                this.style.display = 'none';
            });
        }
    });
}

// Auto-save forms
function initAutoSave() {
    document.querySelectorAll('.auto-save-form').forEach(form => {
        let timeout;
        
        form.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                saveForm(this);
            }, 1000);
        });
    });
}

async function saveForm(form) {
    const formData = new FormData(form);
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Changes saved', 'success');
        } else {
            showToast('Save failed', 'error');
        }
    } catch (error) {
        showToast('Save failed', 'error');
    }
}

// Bulk Actions
function initBulkActions() {
    const selectAll = document.querySelector('.select-all');
    const checkboxes = document.querySelectorAll('.item-checkbox');
    const bulkActions = document.querySelector('.bulk-actions');
    
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
}

function updateBulkActions() {
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    const bulkActions = document.querySelector('.bulk-actions');
    
    if (checkboxes.length > 0) {
        bulkActions.style.display = 'flex';
        bulkActions.querySelector('.selected-count').textContent = checkboxes.length;
    } else {
        bulkActions.style.display = 'none';
    }
}

function performBulkAction(action) {
    const selected = Array.from(document.querySelectorAll('.item-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selected.length === 0) {
        showToast('No items selected', 'warning');
        return;
    }
    
    if (confirm(`Are you sure you want to ${action} ${selected.length} items?`)) {
        fetch('/api/bulk-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: action,
                items: selected
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(`${selected.length} items ${action}ed successfully`, 'success');
                location.reload();
            } else {
                showToast(`Bulk ${action} failed`, 'error');
            }
        })
        .catch(error => {
            showToast('Action failed', 'error');
        });
    }
}

// Keyboard Shortcuts
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveButton = document.querySelector('button[type="submit"]');
            if (saveButton) saveButton.click();
        }
        
        // Ctrl/Cmd + F to search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input');
            if (searchInput) searchInput.focus();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) closeModal(activeModal);
        }
        
        // F5 to refresh (with confirmation if form has changes)
        if (e.key === 'F5') {
            const forms = document.querySelectorAll('form');
            const hasChanges = Array.from(forms).some(form => {
                const original = form.dataset.original;
                return original && original !== JSON.stringify(getFormData(form));
            });
            
            if (hasChanges && !confirm('You have unsaved changes. Are you sure you want to refresh?')) {
                e.preventDefault();
            }
        }
    });
}

function getFormData(form) {
    const data = {};
    Array.from(form.elements).forEach(element => {
        if (element.name) {
            data[element.name] = element.value;
        }
    });
    return data;
}

// Initialize all when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    const initFunctions = [
        initSidebar,
        initCharts,
        initTables,
        initModals,
        initForms,
        initNotifications,
        initTheme,
        initStats,
        initRealTimeUpdates,
        initDateRangePicker,
        initImageUpload,
        initAutoSave,
        initBulkActions,
        initKeyboardShortcuts
    ];
    
    initFunctions.forEach(func => {
        try {
            func();
        } catch (error) {
            console.error(`Error initializing ${func.name}:`, error);
        }
    });
    
    // Show welcome message for first-time visitors
    if (!localStorage.getItem('welcome_shown')) {
        setTimeout(() => {
            showToast('Welcome to TikTok Bot Admin Panel! 🎉', 'success', 10000);
            localStorage.setItem('welcome_shown', 'true');
        }, 1000);
    }
});

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showToast('An error occurred. Please check console for details.', 'error');
});

// Unhandled promise rejection
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showToast('An async error occurred.', 'error');
});