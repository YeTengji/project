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

document.addEventListener("DOMContentLoaded", () => autoDismissAlerts());