// ============================================================
//  BookMySlot – main.js
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss alerts after 5 seconds ─────────────────
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });

  // ── Mobile sidebar toggle ────────────────────────────────
  const sidebar    = document.getElementById('sidebar');
  const menuToggle = document.getElementById('menuToggle');
  const overlay    = document.getElementById('sidebarOverlay');

  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay && overlay.classList.toggle('d-block');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar && sidebar.classList.remove('open');
      overlay.classList.remove('d-block');
    });
  }

  // ── Mark active nav link ─────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    if (a.getAttribute('href') === currentPath) {
      a.classList.add('active');
    }
  });

  // ── Real-time slot availability check ────────────────────
  const hallSelect  = document.getElementById('hall_id');
  const dateInput   = document.getElementById('date');
  const startInput  = document.getElementById('start_time');
  const endInput    = document.getElementById('end_time');
  const resultDiv   = document.getElementById('slot-check-result');

  function checkSlot() {
    if (!hallSelect || !dateInput || !startInput || !endInput || !resultDiv) return;
    const hall  = hallSelect.value;
    const date  = dateInput.value;
    const start = startInput.value;
    const end   = endInput.value;
    if (!hall || !date || !start || !end) return;

    resultDiv.style.display = 'block';
    resultDiv.className     = '';
    resultDiv.textContent   = '⏳ Checking availability…';

    fetch(`/api/check-slot?hall_id=${hall}&date=${date}&start_time=${start}:00&end_time=${end}:00`)
      .then(r => r.json())
      .then(data => {
        if (data.available === true) {
          resultDiv.className   = 'available';
          resultDiv.textContent = '✅ ' + data.message;
        } else if (data.available === false) {
          resultDiv.className   = 'unavailable';
          resultDiv.textContent = '❌ ' + data.message;
        } else {
          resultDiv.style.display = 'none';
        }
      })
      .catch(() => { resultDiv.style.display = 'none'; });
  }

  [hallSelect, dateInput, startInput, endInput].forEach(el => {
    if (el) el.addEventListener('change', checkSlot);
  });

  // ── Set minimum date to today ────────────────────────────
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // ── Confirm dialogs for destructive actions ──────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      const msg = this.getAttribute('data-confirm') || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ── Approve/Reject modal note submit ─────────────────────
  document.querySelectorAll('.btn-approve-action').forEach(btn => {
    btn.addEventListener('click', function () {
      const form  = this.closest('form');
      const note  = this.closest('.modal')?.querySelector('[name="note"]')?.value || '';
      const input = form.querySelector('[name="note"]');
      if (input) input.value = note;
      form.submit();
    });
  });

  // ── Capacity warning in booking form ─────────────────────
  const capacityHint = document.getElementById('capacity-hint');
  const attendeesInput = document.getElementById('attendees');

  if (hallSelect && capacityHint) {
    hallSelect.addEventListener('change', function () {
      const selected = this.options[this.selectedIndex];
      const cap = selected?.dataset?.capacity;
      if (cap) {
        capacityHint.textContent = `Hall capacity: ${cap} persons`;
        capacityHint.style.display = 'block';
        if (attendeesInput) attendeesInput.setAttribute('max', cap);
      }
    });

    attendeesInput && attendeesInput.addEventListener('input', function () {
      const selected = hallSelect.options[hallSelect.selectedIndex];
      const cap = parseInt(selected?.dataset?.capacity || '9999');
      if (parseInt(this.value) > cap) {
        this.value = cap;
        alert(`Maximum capacity is ${cap} persons.`);
      }
    });
  }

  // ── Tooltip init (Bootstrap) ──────────────────────────────
  if (typeof bootstrap !== 'undefined') {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      new bootstrap.Tooltip(el, { trigger: 'hover' });
    });
  }

  // ── Filter table rows by search input ────────────────────
  const tableSearch = document.getElementById('tableSearch');
  if (tableSearch) {
    tableSearch.addEventListener('input', function () {
      const q   = this.value.toLowerCase();
      const tbl = document.querySelector('.bms-table tbody');
      if (!tbl) return;
      tbl.querySelectorAll('tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

});
