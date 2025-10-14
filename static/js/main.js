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

// Autofill Country and Timezone based on Client-side info
function injectCountryTimezone(formCountry, formTimeZone) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const countryField = document.getElementById(formCountry);
    const timeZoneField = document.getElementById(formTimeZone);
    if (!countryField || !timeZoneField) return;

    countryField.addEventListener('change', function () {
        const selectedCountry = this.value;
        fetch('/get-time-zones', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ country: selectedCountry })
        })
        .then(res => res.json())
        .then(data => {
            timeZoneField.innerHTML = '';

            if (data.time_zones.length === 0) {
                timeZoneField.innerHTML = '<option value="">No time zones found</option>';
            } else if (data.readonly) {
                timeZoneField.innerHTML = `<option value="${data.time_zones[0]}">${data.time_zones[0]}</option>`;
            } else {
                data.time_zones.forEach(tz => {
                    const option = document.createElement('option');
                    option.value = tz;
                    option.textContent = tz;
                    timeZoneField.appendChild(option);
                });
            }
        });
    });

    if (formCountry === 'signup-form-country') {
        const locale = navigator.language || navigator.userLanguage || 'en-PH';
        const country = locale.includes('-') ? locale.split('-')[1] : 'PH';

        countryField.value = country.toUpperCase();
        countryField.dispatchEvent(new Event('change'))
    }
}

// --- Add Event Form Functions ---
function addEventFormFunctions() {
    const startSelect = document.getElementById('addEventFormStartField');
    const endSelect = document.getElementById('addEventFormEndField');
    const clearAllDays = document.getElementById('addEventFormClearAllDays');
    const daysOfWeekInput = document.querySelectorAll('input[name="day_of_week"]')
    if (!startSelect || !endSelect || !clearAllDays || !daysOfWeekInput) { return }

    clearAllDays.addEventListener('click', () => {
        daysOfWeekInput.forEach(el => { el.disabled = false; el.checked = false; });
    });

    function filterEndOptions() {
        const startValue = startSelect.value;
        const startIndex = Array.from(endSelect.options).findIndex(opt => opt.value === startValue);

        if (startIndex === -1) return;

        Array.from(endSelect.options).forEach((opt, index) => {
            opt.disabled = index <= startIndex;
        });

        if (endSelect.selectedIndex <= startIndex) {
            endSelect.selectedIndex = startIndex + 1 < endSelect.options.length ? startIndex + 1 : 0;
        }
    }
    startSelect.addEventListener('change', filterEndOptions);
    filterEndOptions();
}

// Main?
document.addEventListener("DOMContentLoaded", () => {
    autoDismissAlerts();
    themeSwitcher();
    showModal('showUserProfileModal', 'userProfileModal');
    loginTheme();
    injectCountryTimezone('signup-form-country', 'signup-form-time-zone');
    injectCountryTimezone('user-profile-form-country', 'user-profile-form-time-zone');
    addEventFormFunctions()
});
