document.addEventListener('DOMContentLoaded', () => {

  /* ===== Design-only button feedback (no navigation logic) ===== */
  const buttons = document.querySelectorAll('.glass-btn');

  buttons.forEach(btn => {
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

  /* Design-only: Subtle lift-in transition for the button on load */
  const primaryButton = document.getElementById('createTestBtn');
  if (primaryButton) {
    primaryButton.style.opacity = '0';
    primaryButton.style.transform = 'translateY(6px)';
    primaryButton.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    
    setTimeout(() => {
      primaryButton.style.opacity = '1';
      primaryButton.style.transform = 'translateY(0)';
    }, 260);
  }

});