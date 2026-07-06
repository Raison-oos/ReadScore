document.addEventListener('DOMContentLoaded', () => {

  const input = document.getElementById('classCodeInput');
  const enterBtn = document.getElementById('enterBtn');

  /* ===== Design-only button ripple feedback ===== */
  document.querySelectorAll('.glass-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      // If the button is physically disabled by HTML, do nothing
      if (btn.disabled) return;

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

  /* Subtle lift-in stagger for the input and button on load */
  [input, enterBtn].forEach((el, i) => {
    if (!el) return; // Guard clause in case elements aren't found
    el.style.opacity = '0';
    el.style.transform = 'translateY(6px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    setTimeout(() => {
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 260 + i * 90);
  });

});