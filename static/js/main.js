// Flash Alert Auto Dismiss
function autoDismissAlerts(timeout = 3000) {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove("show");
            alert.classList.add("fade");
            setTimeout(() => alert.remove(), 500);
        }, timeout);
    });
}

// Theme Switcher
function themeSwitcher() {
    const toggleBtn = document.getElementById('theme-toggle');
    const isAuthenticated = toggleBtn.getAttribute('data-auth') === 'true';
    const csrf_token = toggleBtn.getAttribute('data-csrf');
    
    toggleBtn.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);

        // Update Icon Color
        toggleBtn.classList.remove('btn-dark', 'btn-light');
        toggleBtn.classList.add(newTheme === 'dark' ? 'btn-light' : 'btn-dark');

        const signUpForm = document.querySelector('#signUpModal form');
        const themeInput = signUpForm?.querySelector('[name="theme"]');
        if (themeInput) {
            themeInput.value = newTheme;
        }

        // Send Theme to App
        if (isAuthenticated === true) {
            fetch('/update-theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify({ theme: newTheme })
            });
        }
    });
}

// Show User Profile Modal If Errors
function showUserProfileModal() {
    const showModal = document.getElementById('showUserProfileModal');
    if (showModal && showModal.value === 'true') {
        const modalElement = document.getElementById('userProfileModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show()
    }
}

document.addEventListener("DOMContentLoaded", () => {
    autoDismissAlerts();
    themeSwitcher();
    showUserProfileModal();
});
