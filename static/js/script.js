document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const urlForm = document.getElementById('url-form');
    if (urlForm) {
        urlForm.addEventListener('submit', function(event) {
            const urlInput = document.getElementById('url-input');
            if (!urlInput.value.trim()) {
                event.preventDefault();
                showAlert('Please enter a URL', 'danger');
            }
        });
    }

    // Copy URL to clipboard functionality
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const shortUrlInput = document.getElementById('short-url-input');
            
            if (shortUrlInput) {
                // Select the text in the input
                shortUrlInput.select();
                shortUrlInput.setSelectionRange(0, 99999); // For mobile devices
                
                // Copy the text
                navigator.clipboard.writeText(shortUrlInput.value)
                    .then(() => {
                        // Show success message
                        showAlert('Copied to clipboard!', 'success');
                    })
                    .catch(err => {
                        console.error('Failed to copy: ', err);
                        showAlert('Failed to copy URL', 'danger');
                    });
            }
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });
});

// Function to show alerts
function showAlert(message, type) {
    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    }
}
