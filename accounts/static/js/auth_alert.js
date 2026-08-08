document.addEventListener('DOMContentLoaded', function () {
  var overlay = document.getElementById('alertOverlay');

  if (overlay) {
    var closeBtn = document.getElementById('alertOverlayClose');

    function closeOverlay() {
      overlay.remove();
    }

    closeBtn.addEventListener('click', closeOverlay);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeOverlay();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeOverlay();
    });
  }

  document.querySelectorAll('.toast').forEach(function (toast) {
    function dismiss() {
      toast.classList.add('toast-hide');
      setTimeout(function () { toast.remove(); }, 200);
    }

    var closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) closeBtn.addEventListener('click', dismiss);

    setTimeout(dismiss, 5000);
  });
});
