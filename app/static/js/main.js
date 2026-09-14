document.addEventListener("submit", function (event) {
    const form = event.target;
    const confirmMessage = form.getAttribute("data-confirm");
    if (confirmMessage && !window.confirm(confirmMessage)) {
        event.preventDefault();
    }
});
