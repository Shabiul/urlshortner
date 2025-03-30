document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const urlForm = document.getElementById('url-form');
    if (urlForm) {
        urlForm.addEventListener('submit', function(event) {
            const urlInput = document.getElementById('url-input');
            const customUrlToggle = document.getElementById('customUrlToggle');
            const aliasInput = document.getElementById('alias-input');
            
            // Check if URL input is empty
            if (!urlInput.value.trim()) {
                event.preventDefault();
                showAlert('Please enter a URL', 'danger');
                return;
            }
            
            // Validate custom URL if the toggle is checked
            if (customUrlToggle && customUrlToggle.checked) {
                const customUrl = aliasInput.value.trim();
                
                // Check if custom URL is empty when toggle is on
                if (!customUrl) {
                    event.preventDefault();
                    showAlert('Please enter a custom URL or turn off the custom URL option', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                // Check minimum length
                if (customUrl.length < 3) {
                    event.preventDefault();
                    showAlert('Custom URL must be at least 3 characters long', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                // Check maximum length
                if (customUrl.length > 30) {
                    event.preventDefault();
                    showAlert('Custom URL must be no more than 30 characters long', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                // Check pattern (letters, numbers, hyphens, underscores)
                if (!/^[a-zA-Z0-9_-]+$/.test(customUrl)) {
                    event.preventDefault();
                    showAlert('Custom URL can only contain letters, numbers, hyphens, and underscores', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                // Check for reserved words
                const reservedWords = ['api', 'admin', 'static', 'health', 'shorten', 'logout', 'login', 'register'];
                if (reservedWords.includes(customUrl.toLowerCase())) {
                    event.preventDefault();
                    showAlert('This custom URL is a reserved word and cannot be used', 'danger');
                    aliasInput.focus();
                    return;
                }
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
    
    // Custom URL slug generator and validator
    const urlInput = document.getElementById('url-input');
    const aliasInput = document.getElementById('alias-input');
    const customUrlToggle = document.getElementById('customUrlToggle');
    
    // Generate custom URL suggestion based on the original URL
    if (urlInput && aliasInput) {
        urlInput.addEventListener('blur', function() {
            // Only suggest if custom URL is enabled and the field is empty
            if (customUrlToggle && customUrlToggle.checked && !aliasInput.value.trim()) {
                const url = urlInput.value.trim();
                if (url) {
                    try {
                        // Extract domain name without protocol and www
                        let suggestion = '';
                        
                        // Try to parse the URL
                        const urlObj = new URL(url.startsWith('http') ? url : 'http://' + url);
                        const hostname = urlObj.hostname.replace('www.', '');
                        
                        // Get first part of domain (before first dot)
                        suggestion = hostname.split('.')[0];
                        
                        // Clean up suggestion (remove invalid characters, limit length)
                        suggestion = suggestion
                            .replace(/[^a-zA-Z0-9_-]/g, '-')  // Replace invalid chars with hyphens
                            .replace(/-+/g, '-')              // Replace multiple hyphens with single
                            .replace(/^-|-$/g, '')            // Remove leading/trailing hyphens
                            .toLowerCase();
                        
                        // Add random numbers if suggestion is too short
                        if (suggestion.length < 3) {
                            suggestion += '-' + Math.floor(Math.random() * 900 + 100);
                        }
                        
                        // Limit length
                        suggestion = suggestion.substring(0, 30);
                        
                        // Set the suggestion
                        aliasInput.value = suggestion;
                    } catch (e) {
                        // URL parsing failed, do nothing
                        console.log('Could not generate URL suggestion:', e);
                    }
                }
            }
        });
    }
    
    // Live validation for custom URL
    if (aliasInput) {
        aliasInput.addEventListener('input', function() {
            const customUrl = this.value.trim();
            const feedbackElement = document.getElementById('custom-url-feedback');
            
            // If feedback element doesn't exist, create it
            if (!feedbackElement && customUrl) {
                const newFeedback = document.createElement('div');
                newFeedback.id = 'custom-url-feedback';
                newFeedback.className = 'form-text mt-1';
                this.parentNode.after(newFeedback);
            }
            
            // Get (or re-get) the feedback element
            const feedback = document.getElementById('custom-url-feedback');
            
            if (feedback && customUrl) {
                // Check for minimum length
                if (customUrl.length < 3) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Custom URL must be at least 3 characters long';
                    return;
                }
                
                // Check pattern
                if (!/^[a-zA-Z0-9_-]+$/.test(customUrl)) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Only letters, numbers, hyphens, and underscores allowed';
                    return;
                }
                
                // Check for reserved words
                const reservedWords = ['api', 'admin', 'static', 'health', 'shorten', 'logout', 'login', 'register'];
                if (reservedWords.includes(customUrl.toLowerCase())) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> This is a reserved word and cannot be used';
                    return;
                }
                
                // All checks passed
                feedback.className = 'form-text text-success mt-1';
                feedback.innerHTML = '<i class="fas fa-check-circle"></i> Custom URL looks good!';
            } else if (feedback) {
                // Clear feedback if field is empty
                feedback.innerHTML = '';
            }
        });
    }
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
