document.addEventListener('DOMContentLoaded', () => {

  /* ===== Add / delete question cards (formset management) ===== */

  const qaList     = document.getElementById('qaList');
  const addBtn     = document.getElementById('addQuestionBtn');
  const totalForms = document.getElementById('id_questions-TOTAL_FORMS');
  const template   = document.getElementById('emptyFormTemplate');

  function renumberVisible() {
    qaList.querySelectorAll('.qa-card').forEach((card, i) => {
      const idx = card.querySelector('.qa-card-index');
      if (idx) idx.textContent = i + 1;
    });
  }

  function reindexForms() {
    const cards = qaList.querySelectorAll('.qa-card');
    cards.forEach((card, index) => {
      card.querySelectorAll('input, textarea, select, label').forEach(el => {
        ['name', 'id', 'for'].forEach(attr => {
          if (el.hasAttribute(attr)) {
            el.setAttribute(attr, el.getAttribute(attr).replace(/-(\d+)-/, `-${index}-`));
          }
        });
      });
      card.dataset.formIndex = index;
    });
    if (totalForms) totalForms.value = cards.length;
    renumberVisible();
  }

  function attachDelete(card) {
    const btn = card.querySelector('.btn-delete');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const deleteCheckbox = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        card.style.display = 'none';
      } else {
        card.remove();
      }
      reindexForms();
    });
  }

  /* ===== Answer Key collapsible toggle ===== */
  function attachAnswerKeyToggle(card) {
    const toggle = card.querySelector('.ak-toggle');
    const body   = card.querySelector('.ak-body');
    if (!toggle || !body) return;

    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!isOpen));
      body.classList.toggle('ak-open', !isOpen);
    });
  }

  /* Initialise existing cards */
  qaList.querySelectorAll('.qa-card').forEach(card => {
    attachDelete(card);
    attachAnswerKeyToggle(card);
  });

  /* Add new card */
  if (addBtn && template) {
    addBtn.addEventListener('click', () => {
      const newIndex = qaList.querySelectorAll('.qa-card').length;
      const html = template.innerHTML.replace(/__prefix__/g, newIndex);

      const wrapper = document.createElement('div');
      wrapper.innerHTML = html.trim();
      const card = wrapper.firstElementChild;

      qaList.appendChild(card);
      attachDelete(card);
      attachAnswerKeyToggle(card);
      reindexForms();
      card.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  }

  /* ===== Prevent double-submit ===== */
  const builderForm = document.getElementById('builderForm');
  const createBtn   = document.querySelector('.btn-create');
  if (builderForm && createBtn) {
    builderForm.addEventListener('submit', () => {
      createBtn.disabled    = true;
      createBtn.textContent = 'Saving...';
    });
  }

  /* ===== Settings panel collapse ===== */
  const settingsCollapseBtn = document.getElementById('settingsCollapseBtn');
  const settingsBody        = document.getElementById('settingsBody');
  if (settingsCollapseBtn && settingsBody) {
    settingsCollapseBtn.addEventListener('click', () => {
      const isOpen = settingsCollapseBtn.getAttribute('aria-expanded') === 'true';
      settingsCollapseBtn.setAttribute('aria-expanded', String(!isOpen));
      settingsBody.classList.toggle('collapsed', isOpen);
    });
  }

  /* ===== Passage timer show/hide ===== */
  const timerToggle = document.getElementById('togglePassageTimer');
  const timerRow    = document.getElementById('timerRow');
  if (timerToggle && timerRow) {
    timerToggle.addEventListener('change', () => {
      timerRow.classList.toggle('visible', timerToggle.checked);
    });
  }

});