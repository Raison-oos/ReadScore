document.addEventListener('DOMContentLoaded', () => {

  /* ===== Count-up animation toward the REAL score passed from Django,
     via the data-final-score attribute — not a hardcoded sample value. ===== */
  const scoreCard = document.getElementById('scoreCard');
  const percentEl = document.getElementById('percentNumber');
  const levelEl = document.getElementById('levelText');

  const finalScore = parseFloat(scoreCard.dataset.finalScore) || 0;

  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  function animateCount(el, to, duration) {
    const start = performance.now();
    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);
      el.textContent = Math.round(eased * to);
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = Math.round(to);
        onCountComplete();
      }
    }
    requestAnimationFrame(tick);
  }

  function onCountComplete() {
    requestAnimationFrame(() => levelEl.classList.add('show'));
    scoreCard.classList.add('revealed');
    setTimeout(() => scoreCard.classList.remove('revealed'), 650);
  }

  setTimeout(() => animateCount(percentEl, finalScore, 1200), 300);

  /* ===== Stagger the question rows in on load ===== */
  document.querySelectorAll('.question-row').forEach((row, i) => {
    row.style.animationDelay = (0.15 + i * 0.07) + 's';
  });

  /* ===== Expand / collapse each question's answer ===== */
  document.querySelectorAll('.expand-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('.question-row');
      const answer = row.querySelector('.q-answer');
      const isOpen = btn.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(isOpen));
      answer.style.maxHeight = isOpen ? answer.scrollHeight + 'px' : '0px';
    });
  });

  /* ===== Glass button ripple feedback (Done) ===== */
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