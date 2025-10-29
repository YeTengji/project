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

// Offcanvas Control
function showOffcanvas(triggerID, offcanvasID){
    const showOffcanvas = document.getElementById(triggerID);
    if (showOffcanvas && showOffcanvas.value === 'true') {
        const offcanvasElement = document.getElementById(offcanvasID);
        const offcanvas = new bootstrap.Offcanvas(offcanvasElement);
        offcanvas.show()
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
    const selectAllDays = document.getElementById('addEventFormSelectAllDays')
    const clearAllDays = document.getElementById('addEventFormClearAllDays');
    const dayField = document.getElementById('addEventFormDayField')
    const daysOfWeekInput = document.querySelectorAll('input[name="day_of_week"]')
    if (!startSelect || !endSelect || !selectAllDays || !clearAllDays || !dayField || daysOfWeekInput.length === 0) { return }

    selectAllDays.addEventListener('click', () => {
        daysOfWeekInput.forEach(el => { el.disabled = false; el.checked = true; });
        dayField.disabled = true;
    });

    clearAllDays.addEventListener('click', () => {
        daysOfWeekInput.forEach(el => { el.disabled = false; el.checked = false; });
        dayField.disabled = false;
    });

    daysOfWeekInput.forEach(el => {
        el.addEventListener('change', () => {
            const anyChecked = Array.from(daysOfWeekInput).some(el => el.checked);
            dayField.value = '';
            dayField.disabled = anyChecked;
        });
    });

    dayField.addEventListener('change', () => {
        if (dayField.value) {
            daysOfWeekInput.forEach(el => el.disabled = true);
        } else {
            daysOfWeekInput.forEach(el => el.disabled = false);
        }
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

// --- Share Calendar Carousel ---
function shareCalendarCarousel() {
    const carouselElement = document.querySelector('#carouselSharedImages');
    if (carouselElement) {
        const carousel = new bootstrap.Carousel(carouselElement, {
            interval: 2000,
            pause: 'hover',
            wrap: true
        });

        carouselElement.addEventListener('slid.bs.carousel', (event) => {
            const activeIndex = event.to;
            const buttons = document.querySelectorAll('.carousel-sync-btn');

            buttons.forEach(btn => {
                btn.classList.remove('active');
                if (parseInt(btn.dataset.slideIndex) === activeIndex) {
                    btn.classList.add('active');
                }
            });
        });
    }
}

// --- Form Field Focus ---
function formFieldFocus({ triggerID = null, fieldID, triggerType = 'modal'}) {
    const field = document.getElementById(fieldID)
    if (!field) return;

    const eventMap = {
        modal: 'shown.bs.modal',
        offcanvas: 'shown.bs.offcanvas'
    };

    const eventName = eventMap[triggerType];

    if (triggerID && eventName) {
        const trigger = document.getElementById(triggerID);
        trigger?.addEventListener(eventName, () => {
            field.focus();
        });
    } else {
        field.focus();
    }
}

// Delete Calendar Shares Modals
function deleteCalendarShareRequest() {
    const modal = document.getElementById('deleteCalendarShareRequestModal');
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const username = button.getAttribute('data-username');
        const requestID = button.getAttribute('data-request-id');
        const requestStatus = button.getAttribute('data-request-status')
        const form = modal.querySelector('#deleteCalendarShareRequestModalForm')
        const baseURL = form.getAttribute('data-base-url').replace(/0$/, requestID);

        form.action = baseURL;

        let message = '';
        switch (requestStatus) {
            case '0':
                message = `Remove request sent to ${username}?`;
                break;
            case '1':
                message = `Cancel request sent to ${username}?`;
                break;
            case '2':
                message = `Stop sharing calendar with ${username}?`;
                break;
        }

        modal.querySelector('#deleteCalendarShareRequestModalMessage').textContent = message;

    });
}

function deleteAcceptedCalendarShare() {
    const modal = document.getElementById('deleteAcceptedCalendarShareModal')
    const form = document.getElementById('deleteAcceptedCalendarShareModalForm')
    const message = document.getElementById('deleteAcceptedCalendarShareModalMessage')
    if (!modal) return;

    modal.addEventListener('show.bs.modal', event => {
        const button = event.relatedTarget;
        const owner = button.getAttribute('data-owner');
        const requestID = button.getAttribute('data-request-id');
        const baseURL = form.getAttribute('data-base-url');

        form.action =baseURL.replace(/0$/, requestID);
        message.textContent = `Stop viewing ${owner}'s schedule?`;
    });
}

// Clock
let lastSecond = null;

function updateClock() {
    const now = new Date();
    const sec = now.getSeconds();
    const min = now.getMinutes();
    const hr = now.getHours();

    seconds = document.getElementById('second');
    minutes = document.getElementById('minute');
    hours = document.getElementById('hour');
    if (!seconds || !minutes || ! hours) return;

    if (lastSecond === 59 && sec === 0) {
        seconds.style.transition = 'none';
    } else {
        seconds.style.transition = 'transform 0.2s cubic-bezier(0.68, -0.55, 0.27, 1.55)';
    }
    seconds.style.transform = `rotate(${sec * 6}deg)`;
    minutes.style.transform = `rotate(${min * 6}deg)`;
    hours.style.transform = `rotate(${(hr % 12) * 30 + min * 0.5}deg)`;

    lastSecond = sec;
}

setInterval(updateClock, 1000);
updateClock();

// Notepad
function updateNotepad() {
    const notepad = document.getElementById('notepad')
    const notepadBody = document.getElementById('notepadBody');
    const csrf_token = notepad.getAttribute('data-csrf')
    if (!notepad || !notepadBody) return;

    function getNotepadData() {
        const title = document.getElementById('notepadTitle')?.innerText.trim() || "";
        const items = Array.from(document.querySelectorAll('#notepadBody li')).map( li => {
            const checkbox = li.querySelector('input[type="checkbox"]');
            const span = li.querySelector('span');
            return {
                text: span?.innerText.trim() || "",
                checked: checkbox?.checked || false
            };
        });
        return {
            title,
            body: items
        };
    }

    async function saveNotepad() {
        const note = getNotepadData();
        console.log(JSON.stringify(note));
        try {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token
                },
                body: JSON.stringify(note)
            });
            if (!response.ok) throw new Error('Failed to save note');
            console.log('Note saved successfully!');
        } catch (err) {
            console.error('Save error:', err);
        }
    }

    function placeCaretAtEnd(el) {
        const range = document.createRange();
        const sel = window.getSelection();
        range.selectNodeContents(el);
        range.collapse(false);
        sel.removeAllRanges();
        sel.addRange(range);
    }

    function attachCaretBehavior(span) {
        span.addEventListener('focus', () => placeCaretAtEnd(span));
    }

    notepadBody.querySelectorAll('span[contenteditable]').forEach(attachCaretBehavior);

    notepadBody.addEventListener('change', function (e) {
        if (e.target.matches('input[type="checkbox"]')) {
            const span = e.target.nextElementSibling;
            if (span && span.tagName === 'SPAN') {
                span.classList.toggle('checked', e.target.checked);
            }
        }
    });

    notepadBody.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();

            const currentLi = e.target.closest('li');
            if (!currentLi) return;

            const newLi = document.createElement('li');
            newLi.innerHTML = `
                <input type='checkbox' class='form-check-input me-2'>
                <span contenteditable='true'></span>
                <button class="btn btn-sm btn-link delete-line" title="Delete item">
                    <i class="bi bi-x-lg"></i>
                </button>
            `;
            notepadBody.insertBefore(newLi, currentLi.nextSibling);

            const newSpan = newLi.querySelector('span');
            attachCaretBehavior(newSpan);
            newSpan.focus();
        }
        if (e.key === 'Backspace') {
            const span = e.target;
            if (span.tagName !== 'SPAN' || !span.isContentEditable) return;

            const selection = window.getSelection()
            const caretAtStart = selection.anchorOffset === 0;

            if (span.innerText.trim() === "" && caretAtStart) {
                e.preventDefault();
                const li = span.closest('li');
                if (li && notepadBody.children.length > 1) {
                    const prev = li.previousElementSibling?.querySelector('span');
                    li.remove();
                    if (prev) prev.focus();
                }
            }
        }
    });

    notepadBody.addEventListener('click', function (e) {
        const deleteBtn = e.target.closest('.delete-line');
        if (deleteBtn) {
            const li = deleteBtn.closest('li');
            if (li && notepadBody.children.length > 1) {
                li.classList.add('fade-out')
                setTimeout(() => li.remove(), 200);
            } else if (li) {
                const span = li.querySelector('span');
                const checkbox = li.querySelector('input[type="checkbox"]');
                if (span) span. innerText = '';
                if (checkbox) checkbox.checked = false;
            }
        }
    });

    notepad.addEventListener('focusout', () => {
        setTimeout(() => {
            if (!notepad.contains(document.activeElement)) {
                saveNotepad();
            }
        }, 50);
    });

    window.addEventListener('beforeunload', () => {
        const note = getNotepadData();
        fetch('/api/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(note),
            keepalive: true
        });
    });
}

// Main?
document.addEventListener("DOMContentLoaded", () => {
    formFieldFocus({ fieldID: 'loginFormIdentifierField' });
    formFieldFocus({
        triggerID: 'shareCalendarRequestModal',
        fieldID: 'share_calendar_request_form_identifier_field',
        triggerType: 'modal'
    });
    formFieldFocus({ fieldID: 'change-password-form-current-password' });
    formFieldFocus({ fieldID: 'forgotPasswordFormField'});
    formFieldFocus({ fieldID: 'verifyPasswordResetCodeFormField'});
    formFieldFocus({ fieldID: 'reset-password-form-password' });
    formFieldFocus({
        triggerID: 'addEventOffcanvas',
        fieldID: 'addEventFormTitleField',
        triggerType: 'offcanvas'
    });
    autoDismissAlerts();
    themeSwitcher();
    showModal('showUserProfileModal', 'userProfileModal');
    showModal('signUpModalTrigger', 'signUpModal');
    showOffcanvas('addEventTrigger', 'addEventOffcanvas')
    loginTheme();
    injectCountryTimezone('signup-form-country', 'signup-form-time-zone');
    injectCountryTimezone('user-profile-form-country', 'user-profile-form-time-zone');
    addEventFormFunctions();
    shareCalendarCarousel();
    deleteCalendarShareRequest();
    deleteAcceptedCalendarShare();
    updateNotepad();
});
