document.addEventListener('DOMContentLoaded', () => {

  /* ===== Add / delete question cards (formset management) =====
     This is the only JS-driven logic left. Saving, passage validation,
     question/answer validation, and Bloom's classification are all
     handled server-side by Django on form submit. */

  const qaList = document.getElementById('qaList');
  const addBtn = document.getElementById('addQuestionBtn');
  const totalForms = document.getElementById('id_questions-TOTAL_FORMS');
  const template = document.getElementById('emptyFormTemplate');

  function renumberVisible() {
    qaList.querySelectorAll('.qa-card').forEach((card, i) => {
      card.querySelector('.qa-card-index').textContent = i + 1;
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
    totalForms.value = cards.length;
    renumberVisible();
  }

  function attachDelete(card) {
    card.querySelector('.btn-delete').addEventListener('click', () => {
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

  qaList.querySelectorAll('.qa-card').forEach(attachDelete);

  addBtn.addEventListener('click', () => {
    const newIndex = qaList.querySelectorAll('.qa-card').length;
    const html = template.innerHTML.replace(/__prefix__/g, newIndex);

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html.trim();
    const card = wrapper.firstElementChild;

    qaList.appendChild(card);
    attachDelete(card);
    reindexForms();
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
  });

  /* ===== Prevent double-submit ===== */
  const builderForm = document.getElementById('builderForm');
  const createBtn = document.querySelector('.btn-create');

  builderForm.addEventListener('submit', () => {
    createBtn.disabled = true;
    createBtn.textContent = 'Saving...';
  });

});