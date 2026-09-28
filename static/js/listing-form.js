// Show only the form sections relevant to the selected listing kind.
// Sections declare the kinds they apply to via data-kinds="job internship ...".
(function () {
  const select = document.querySelector("[data-listing-kind]");
  if (!select) return;

  function sync() {
    document.querySelectorAll("[data-kinds]").forEach(function (el) {
      const kinds = el.dataset.kinds.split(" ");
      el.hidden = !kinds.includes(select.value);
    });
  }

  select.addEventListener("change", sync);
  sync();
})();
