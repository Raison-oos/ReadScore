document.addEventListener('DOMContentLoaded', () => {

  const cards = Array.from(document.querySelectorAll('.test-card'));

  /* Stagger the entrance animation per card (design only) */
  cards.forEach((card, i) => {
    card.style.animationDelay = (i * 0.06) + 's';
  });

  /* ===== Single-select highlight (click card body to focus it) =====
     Purely visual — doesn't affect what data gets sent anywhere. */
  cards.forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.icon-btn') || e.target.closest('form')) return;
      cards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });

  /* ===== Delete test: confirm, then let the real form submission
     happen. The exit animation only plays after the user confirms —
     the actual deletion is a real POST request to the server, not
     something JS fakes locally. ===== */
  document.querySelectorAll('.delete-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const card = form.closest('.test-card');
      const testCode = card ? card.dataset.testCode : 'this test';

      if (!window.confirm(`Delete ${testCode}? This cannot be undone.`)) {
        e.preventDefault();
        return;
      }

      if (card) {
        card.classList.add('removing');
      }
      // form submits normally after this — no e.preventDefault(),
      // so the browser actually sends the POST request to Django
    });
  });

  /* ===== Export test record: brief visual confirmation on the icon.
     The actual file download is handled by the browser navigating to
     the real href — this just adds a flash of feedback. ===== */
  document.querySelectorAll('.export-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.style.transition = 'background 0.15s ease, border-color 0.15s ease, color 0.15s ease';
      btn.style.background = '#EAF3EC';
      btn.style.borderColor = '#BFE0CB';
      btn.style.color = '#1F7A4D';
      setTimeout(() => {
        btn.style.background = '';
        btn.style.borderColor = '';
        btn.style.color = '';
      }, 500);
    });
  });

  /* ===== Glass button ripple feedback (Create Test button) ===== */
  document.querySelectorAll('.glass-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const rect = btn.getBoundingClientRect();
      const ripple = document.createElement('span');
      const size = Math.max(rect.width, rect.height) * 1.6;

      ripple.style.position = 'absolute';
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      ripple.style.borderRadius = '50%';
      ripple.style.background = 'rgba(255,255,255,0.45)';
      ripple.style.pointerEvents = 'none';
      ripple.style.transform = 'scale(0)';
      ripple.style.opacity = '1';
      ripple.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
      ripple.style.zIndex = '1';

      btn.appendChild(ripple);
      requestAnimationFrame(() => {
        ripple.style.transform = 'scale(1)';
        ripple.style.opacity = '0';
      });
      setTimeout(() => ripple.remove(), 520);
    });
  });

});