document.addEventListener('DOMContentLoaded', function() {
    
    const urlForm = document.getElementById('url-form');
    if (urlForm) {
        urlForm.addEventListener('submit', function(event) {
            const urlInput = document.getElementById('url-input');
            const customUrlToggle = document.getElementById('customUrlToggle');
            const aliasInput = document.getElementById('alias-input');
            
            if (!urlInput.value.trim()) {
                event.preventDefault();
                showAlert('Please enter a URL', 'danger');
                return;
            }
            if (customUrlToggle && customUrlToggle.checked) {
                const customUrl = aliasInput.value.trim();
                if (!customUrl) {
                    event.preventDefault();
                    showAlert('Please enter a custom URL or turn off the custom URL option', 'danger');
                    aliasInput.focus();
                    return;
                }
                if (customUrl.length < 3) {
                    event.preventDefault();
                    showAlert('Custom URL must be at least 3 characters long', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                if (customUrl.length > 30) {
                    event.preventDefault();
                    showAlert('Custom URL must be no more than 30 characters long', 'danger');
                    aliasInput.focus();
                    return;
                }
                
                if (!/^[a-zA-Z0-9_-]+$/.test(customUrl)) {
                    event.preventDefault();
                    showAlert('Custom URL can only contain letters, numbers, hyphens, and underscores', 'danger');
                    aliasInput.focus();
                    return;
                }
                
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

    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const shortUrlInput = document.getElementById('short-url-input');
            
            if (shortUrlInput) {
                shortUrlInput.select();
                shortUrlInput.setSelectionRange(0, 99999); 
                
                
                navigator.clipboard.writeText(shortUrlInput.value)
                    .then(() => {
                        showAlert('Copied to clipboard!', 'success');
                    })
                    .catch(err => {
                        console.error('Failed to copy: ', err);
                        showAlert('Failed to copy URL', 'danger');
                    });
            }
        });
    }

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });
    
    const urlInput = document.getElementById('url-input');
    const aliasInput = document.getElementById('alias-input');
    const customUrlToggle = document.getElementById('customUrlToggle');
    
    if (urlInput && aliasInput) {
        urlInput.addEventListener('blur', function() {
            if (customUrlToggle && customUrlToggle.checked && !aliasInput.value.trim()) {
                const url = urlInput.value.trim();
                if (url) {
                    try {
                        let suggestion = '';
                        
                        const urlObj = new URL(url.startsWith('http') ? url : 'http://' + url);
                        const hostname = urlObj.hostname.replace('www.', '');
                        
                        suggestion = hostname.split('.')[0];
                        
                        suggestion = suggestion
                            .replace(/[^a-zA-Z0-9_-]/g, '-')  
                            .replace(/-+/g, '-')              
                            .replace(/^-|-$/g, '')            
                            .toLowerCase();
                        if (suggestion.length < 3) {
                            suggestion += '-' + Math.floor(Math.random() * 900 + 100);
                        }
                        
                        suggestion = suggestion.substring(0, 30);
                        
                        aliasInput.value = suggestion;
                    } catch (e) {
                        console.log('Could not generate URL suggestion:', e);
                    }
                }
            }
        });
    }
    
    if (aliasInput) {
        aliasInput.addEventListener('input', function() {
            const customUrl = this.value.trim();
            const feedbackElement = document.getElementById('custom-url-feedback');
            
            if (!feedbackElement && customUrl) {
                const newFeedback = document.createElement('div');
                newFeedback.id = 'custom-url-feedback';
                newFeedback.className = 'form-text mt-1';
                this.parentNode.after(newFeedback);
            }
            
            const feedback = document.getElementById('custom-url-feedback');
            
            if (feedback && customUrl) {
                
                if (customUrl.length < 3) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Custom URL must be at least 3 characters long';
                    return;
                }
                
                if (!/^[a-zA-Z0-9_-]+$/.test(customUrl)) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Only letters, numbers, hyphens, and underscores allowed';
                    return;
                }
                
                const reservedWords = ['api', 'admin', 'static', 'health', 'shorten', 'logout', 'login', 'register'];
                if (reservedWords.includes(customUrl.toLowerCase())) {
                    feedback.className = 'form-text text-danger mt-1';
                    feedback.innerHTML = '<i class="fas fa-exclamation-triangle"></i> This is a reserved word and cannot be used';
                    return;
                }
                
                feedback.className = 'form-text text-success mt-1';
                feedback.innerHTML = '<i class="fas fa-check-circle"></i> Custom URL looks good!';
            } else if (feedback) {
                
                feedback.innerHTML = '';
            }
        });
    }
});

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
        
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    }
}
