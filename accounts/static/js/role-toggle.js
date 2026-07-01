document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("roleToggle");
  const roleInput = document.getElementById("roleInput");

  if (!toggle || !roleInput) return;

  const options = toggle.querySelectorAll(".role-toggle-option");

  options.forEach(function (option) {
    option.addEventListener("click", function () {
      const role = option.getAttribute("data-role");

      toggle.setAttribute("data-active", role);
      roleInput.value = role;

      options.forEach(function (opt) {
        opt.classList.toggle("is-active", opt === option);
      });
    });
  });
});