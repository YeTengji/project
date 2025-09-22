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

        // Optional: update button style or icon
        toggleBtn.classList.toggle('btn-dark');
        toggleBtn.classList.toggle('btn-light');

        // Optional: send theme to backend via fetch
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

document.addEventListener("DOMContentLoaded", () => {
    autoDismissAlerts();
    themeSwitcher();
});