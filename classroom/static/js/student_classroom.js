document.addEventListener('DOMContentLoaded', () => {

  const input    = document.getElementById('classCodeInput');
  const enterBtn = document.getElementById('enterBtn');

  /* ===== Design-only button ripple feedback ===== */
  document.querySelectorAll('.glass-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (btn.disabled) return;

      const rect   = btn.getBoundingClientRect();
      const ripple = document.createElement('span');
      const size   = Math.max(rect.width, rect.height) * 1.6;

      ripple.style.cssText = [
        'position:absolute',
        `width:${size}px`,
        `height:${size}px`,
        `left:${e.clientX - rect.left - size / 2}px`,
        `top:${e.clientY - rect.top - size / 2}px`,
        'border-radius:50%',
        'background:rgba(255,255,255,0.45)',
        'pointer-events:none',
        'transform:scale(0)',
        'opacity:1',
        'transition:transform 0.5s ease,opacity 0.5s ease',
        'z-index:1'
      ].join(';');

      btn.appendChild(ripple);
      requestAnimationFrame(() => {
        ripple.style.transform = 'scale(1)';
        ripple.style.opacity   = '0';
      });
      setTimeout(() => ripple.remove(), 520);
    });
  });

  /* Subtle lift-in stagger for the input and button on load (single card state) */
  [input, enterBtn].forEach((el, i) => {
    if (!el) return;
    el.style.opacity   = '0';
    el.style.transform = 'translateY(6px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    setTimeout(() => {
      el.style.opacity   = '1';
      el.style.transform = 'translateY(0)';
    }, 260 + i * 90);
  });

  /* ===== Card-grid view: add-card → entry overlay toggle ===== */
  const addTestBtn    = document.getElementById('addTestBtn');
  const entryOverlay  = document.getElementById('entryOverlay');
  const backBtn       = document.getElementById('backBtn');

  if (addTestBtn && entryOverlay) {
    // Open overlay
    addTestBtn.addEventListener('click', () => {
      entryOverlay.classList.add('visible');
    });

    // Close on backdrop click (outside role-card)
    entryOverlay.addEventListener('click', (e) => {
      if (e.target === entryOverlay) {
        entryOverlay.classList.remove('visible');
      }
    });

    // Close on back button
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        entryOverlay.classList.remove('visible');
      });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') entryOverlay.classList.remove('visible');
    });
  }

});