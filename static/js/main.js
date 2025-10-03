// Flash Alert Auto Dismiss
function autoDismissAlerts(timeout = 5000) {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove("show");
            alert.classList.add("fade");
            setTimeout(() => alert.remove(), 500);
        }, timeout);
    });
}

// Login Theme
function loginTheme() {
    const loginSubmitButton = document.getElementById('login-submit-button');
    if (!loginSubmitButton) return;

    loginSubmitButton.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const loginForm = document.querySelector('#loginFormBlock form');
        const loginThemeInput = loginForm?.querySelector('[name="theme"]');
        if (loginThemeInput) {
            loginThemeInput.value = currentTheme;
        }
    });
}

// Theme Switcher
function themeSwitcher() {
    const toggleBtn = document.getElementById('theme-toggle');
    const isAuthenticated = toggleBtn.getAttribute('data-auth') === 'true';
    const csrf_token = toggleBtn.getAttribute('data-csrf');
    let isSwitching = false;
    toggleBtn.addEventListener('click', () => {
        if (isSwitching) return;
        isSwitching = true;
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);
        document.cookie = `theme=${newTheme}; path=/; max-age=31536000; Secure`;

        // Update Icon Color
        toggleBtn.classList.remove('btn-dark', 'btn-light');
        toggleBtn.classList.add(newTheme === 'dark' ? 'btn-light' : 'btn-dark');

        const signUpForm = document.querySelector('#signUpModal form');
        const signUpThemeInput = signUpForm?.querySelector('[name="theme"]');

        if (signUpThemeInput) {
            signUpThemeInput.value = newTheme;
        }

        // Send Theme to App
        if (isAuthenticated) {
            fetch('/update-theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify({ theme: newTheme })
            });
        }
        setTimeout(() => {isSwitching = false; }, 300)
    });
}

// Modal Control
function showModal(triggerID, modalID) {
    const showModal = document.getElementById(triggerID);
    if (showModal && showModal.value === 'true') {
        const modalElement = document.getElementById(modalID);
        const modal = new bootstrap.Modal(modalElement);
        modal.show()
    }
}

// Toggle Password Visibility
function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    const isHidden = input.type === "password";

    input.type = isHidden ? "text" : "password";
    icon.className = isHidden ? "bi-eye-slash" : "bi bi-eye";
}

// Main?
document.addEventListener("DOMContentLoaded", () => {
    autoDismissAlerts();
    themeSwitcher();
    showModal('showUserProfileModal', 'userProfileModal');
    loginTheme();
});
