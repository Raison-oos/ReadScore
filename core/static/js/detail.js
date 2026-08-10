/* detail.js — interactions for the unified About / FAQ / Contact page */
document.addEventListener('DOMContentLoaded', function () {

  /* -----------------------------------------------------------
     Scroll reveal
  ----------------------------------------------------------- */
  var revealEls = document.querySelectorAll('.d-reveal');
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.10, rootMargin: '0px 0px -36px 0px' });

  revealEls.forEach(function (el, i) {
    el.style.transitionDelay = Math.min(i % 4, 3) * 55 + 'ms';
    revealObserver.observe(el);
  });

  /* -----------------------------------------------------------
     FAQ accordion
  ----------------------------------------------------------- */
  document.querySelectorAll('.d-accordion-trigger').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var expanded = trigger.getAttribute('aria-expanded') === 'true';
      trigger.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    });
  });

});
