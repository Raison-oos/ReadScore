document.addEventListener('DOMContentLoaded', () => {

  /* ===== Eye toggle: hide / show passage with blink animation =====
     Pure UI — toggles a CSS class and swaps an icon. No data logic. */
  const passagePanel = document.getElementById('passagePanel');
  const eyeToggle = document.getElementById('eyeToggle');
  const eyeIcon = document.getElementById('eyeIcon');
  const passageTitleInline = document.getElementById('passageTitleInline');

  const eyeOpenSVG = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1.5 12C1.5 12 5 5 12 5C19 5 22.5 12 22.5 12C22.5 12 19 19 12 19C5 19 1.5 12 1.5 12Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="12" cy="12" r="3.2" stroke="currentColor" stroke-width="1.6"/>
    </svg>`;

  const eyeClosedSVG = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1.5 12C1.5 12 5 6 12 6C19 6 22.5 12 22.5 12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>
      <path d="M2 13C4.5 15.6 8 17.6 12 17.6C16 17.6 19.5 15.6 22 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M6 15.5L4.7 17.6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      <path d="M18 15.5L19.3 17.6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      <path d="M12 17.6V20" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    </svg>`;

  let isHidden = false;

  if (eyeToggle && passagePanel) {
    eyeToggle.addEventListener('click', () => {
      isHidden = !isHidden;

      eyeIcon.classList.add('blink');
      eyeToggle.setAttribute('aria-pressed', String(isHidden));
      eyeToggle.setAttribute('aria-label', isHidden ? 'Show passage' : 'Hide passage');

      setTimeout(() => {
        eyeIcon.innerHTML = isHidden ? eyeClosedSVG : eyeOpenSVG;
        passagePanel.classList.toggle('collapsed', isHidden);
        passageTitleInline.textContent = isHidden ? 'Hidden' : 'Passage';
      }, 180);

      eyeIcon.addEventListener('animationend', () => {
        eyeIcon.classList.remove('blink');
      }, { once: true });
    });
  }

  /* ===== Answer inputs: visual-only feedback =====
     Toggles the send-icon glow when there's text, and clears a
     previously-shown warning icon once the student starts typing.
     Does NOT decide what counts as "valid" — that's the server's job
     when the form is actually submitted. */
  const questionCards = Array.from(document.querySelectorAll('.question-card'));

  function setupCard(card) {
    const textarea = card.querySelector('.answer-input');
    const sendIcon = card.querySelector('.send-icon');
    const warningIcon = card.querySelector('.q-warning');

    function updateVisualState() {
      const hasText = textarea.value.trim().length > 0;
      sendIcon.classList.toggle('active', hasText);
      if (hasText) {
        warningIcon.classList.remove('show');
        warningIcon.hidden = true;
        card.classList.remove('has-warning');
      }
    }

    textarea.addEventListener('input', updateVisualState);
    updateVisualState();
  }

  questionCards.forEach(setupCard);

});