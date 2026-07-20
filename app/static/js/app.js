document.addEventListener("click", (event) => {
  const copyBtn = event.target.closest("[data-copy]");
  if (copyBtn) {
    const text = copyBtn.getAttribute("data-copy");
    navigator.clipboard.writeText(text).then(() => {
      const original = copyBtn.textContent;
      copyBtn.textContent = "Copied";
      copyBtn.classList.add("copied");
      setTimeout(() => {
        copyBtn.textContent = original;
        copyBtn.classList.remove("copied");
      }, 1500);
    });
    return;
  }

  const editBtn = event.target.closest("[data-edit-toggle]");
  if (editBtn) {
    const row = editBtn.closest(".url-row");
    row.classList.add("editing");
    row.querySelector(".edit-form").classList.add("active");
    row.querySelector(".edit-form input[type='url']").focus();
    return;
  }

  const cancelBtn = event.target.closest("[data-edit-cancel]");
  if (cancelBtn) {
    const row = cancelBtn.closest(".url-row");
    row.classList.remove("editing");
    row.querySelector(".edit-form").classList.remove("active");
    return;
  }

  const deleteBtn = event.target.closest("[data-delete-toggle]");
  if (deleteBtn) {
    if (deleteBtn.dataset.confirming !== "true") {
      event.preventDefault();
      deleteBtn.dataset.confirming = "true";
      deleteBtn.dataset.originalText = deleteBtn.textContent;
      deleteBtn.textContent = "Confirm?";
      deleteBtn.classList.add("danger");
      resetOtherDeleteButtons(deleteBtn);
    }
    // Second click: confirming is already "true", let the form submit normally.
    return;
  }

  // Any click outside an armed delete button resets it.
  resetOtherDeleteButtons(null);
});

function resetOtherDeleteButtons(exceptBtn) {
  document.querySelectorAll('[data-delete-toggle][data-confirming="true"]').forEach((btn) => {
    if (btn !== exceptBtn) {
      btn.textContent = btn.dataset.originalText || "Delete";
      btn.dataset.confirming = "false";
      btn.classList.remove("danger");
    }
  });
}
