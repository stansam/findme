document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initFlashMessages();
    initDataTables();
    initModals();
});

function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (collapsed) {
        sidebar.classList.add('collapsed');
    }

    if (window.innerWidth <= 768) {
        sidebar.classList.add('collapsed');
    }
}

function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
}

function initDataTables() {
    const sortableTables = document.querySelectorAll('.table-sortable');

    sortableTables.forEach(function(table) {
        const headers = table.querySelectorAll('th[data-sortable]');

        headers.forEach(function(header, index) {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort"></i>';

            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });
}

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAscending = table.dataset.sortOrder !== 'asc';

    rows.sort(function(a, b) {
        const aValue = a.cells[column].textContent.trim();
        const bValue = b.cells[column].textContent.trim();

        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }

        return isAscending ?
            aValue.localeCompare(bValue) :
            bValue.localeCompare(aValue);
    });

    rows.forEach(function(row) {
        tbody.appendChild(row);
    });

    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
}

function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');

    modalTriggers.forEach(function(trigger) {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);

            if (modal) {
                openModal(modal);
            }
        });
    });

    const closeButtons = document.querySelectorAll('.modal-close, [data-modal-close]');

    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                closeModal(modal);
            }
        });
    });
}

function openModal(modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal(modal);
        }
    });
}

function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function toggleUserStatus(userId) {
    if (!confirm('Are you sure you want to change this user\'s status?')) {
        return;
    }

    fetch(`/admin/users/${userId}/toggle-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function changeUserRole(userId) {
    const select = document.getElementById(`role-select-${userId}`);
    const newRole = select.value;

    if (!confirm(`Change user role to ${newRole}?`)) {
        return;
    }

    fetch(`/admin/users/${userId}/change-role`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ role: newRole })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function verifyMissingPerson(personId) {
    if (!confirm('Verify this missing person report?')) {
        return;
    }

    fetch(`/admin/missing-persons/${personId}/verify`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function updatePersonStatus(personId) {
    const select = document.getElementById(`status-select-${personId}`);
    const newStatus = select.value;

    if (!confirm(`Change status to ${newStatus}?`)) {
        return;
    }

    fetch(`/admin/missing-persons/${personId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function verifyReport(reportId) {
    const notes = prompt('Enter verification notes (optional):');

    if (notes === null) {
        return;
    }

    fetch(`/admin/reports/${reportId}/verify`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ notes: notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function rejectReport(reportId) {
    const notes = prompt('Enter rejection reason:');

    if (!notes) {
        showNotification('Rejection reason is required', 'error');
        return;
    }

    fetch(`/admin/reports/${reportId}/reject`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function updateSetting(key, value) {
    fetch('/admin/settings/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ key: key, value: value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function showNotification(message, type = 'info') {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();

    const flash = document.createElement('div');
    flash.className = `flash-message flash-${type}`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'exclamation-circle' : 'info-circle';

    flash.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <button class="close-flash" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    flashContainer.appendChild(flash);

    setTimeout(() => {
        flash.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => flash.remove(), 300);
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.querySelector('.content-wrapper').prepend(container);
    return container;
}

function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

function handleSearch(form) {
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    window.location.href = `${form.action}?${params.toString()}`;
    return false;
}

const slideOutAnimation = `
    @keyframes slideOut {
        from {
            transform: translateY(0);
            opacity: 1;
        }
        to {
            transform: translateY(-1rem);
            opacity: 0;
        }
    }
`;

const style = document.createElement('style');
style.textContent = slideOutAnimation;
document.head.appendChild(style);
