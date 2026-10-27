/**
 * Food Donation Tracker - Vanilla JavaScript
 * Handles live countdown timers and confirmation dialogs
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Live Countdown Timers
  initCountdowns();

  // Initialize Action Confirmations
  initConfirmDialogs();

  // Set default datetime for new donation safe_until (e.g., 4 hours from now)
  initDateTimeDefaults();
});

/**
 * Initializes and ticks countdown timers on all elements with [data-safe-until]
 */
function initCountdowns() {
  const countdownElements = document.querySelectorAll('[data-safe-until]');
  if (!countdownElements.length) return;

  function updateAllTimers() {
    const now = new Date().getTime();

    countdownElements.forEach(el => {
      const isoString = el.getAttribute('data-safe-until');
      if (!isoString) return;

      const targetTime = new Date(isoString).getTime();
      const diffMs = targetTime - now;

      if (diffMs <= 0) {
        el.textContent = 'Expired';
        el.classList.remove('urgent');
        el.classList.add('badge-status-expired');

        // If there's an associated claim button nearby, disable it
        const card = el.closest('.donation-card') || el.closest('.detail-card');
        if (card) {
          const claimBtn = card.querySelector('.btn-claim');
          if (claimBtn) {
            claimBtn.disabled = true;
            claimBtn.textContent = 'Expired';
            claimBtn.classList.add('disabled');
          }
        }
      } else {
        const totalSeconds = Math.floor(diffMs / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        let displayString = '';
        if (hours > 0) {
          displayString = `${hours}h ${minutes}m left`;
        } else if (minutes > 0) {
          displayString = `${minutes}m ${seconds}s left`;
        } else {
          displayString = `${seconds}s left`;
        }

        el.textContent = displayString;

        // Mark as urgent if under 1 hour remaining
        if (totalSeconds < 3600) {
          el.classList.add('urgent');
        } else {
          el.classList.remove('urgent');
        }
      }
    });
  }

  // Initial update then run every second
  updateAllTimers();
  setInterval(updateAllTimers, 1000);
}

/**
 * Attach confirm dialogs to any form or button with [data-confirm]
 */
function initConfirmDialogs() {
  document.querySelectorAll('[data-confirm]').forEach(element => {
    element.addEventListener('click', (e) => {
      const message = element.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!window.confirm(message)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    });
  });
}

/**
 * Set default value for safe_until input in donation form (4 hours in the future)
 */
function initDateTimeDefaults() {
  const safeUntilInput = document.getElementById('safe_until');
  if (safeUntilInput && !safeUntilInput.value) {
    const now = new Date();
    // Default to 4 hours ahead
    now.setHours(now.getHours() + 4);

    // Format for datetime-local: YYYY-MM-DDTHH:MM
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    safeUntilInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  }
}
