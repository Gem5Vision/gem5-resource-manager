const loadingContainer = document.getElementById("loading-container");
const alertPlaceholder = document.getElementById('liveAlertPlaceholder');
const interactiveElems = document.querySelectorAll('button, input, select');

function reset() {
  window.location.href = "/";
}

const appendAlert = (errorHeader, id, message, type) => {
  const alertDiv = document.createElement('div');
  alertDiv.classList.add("alert", `alert-${type}`, "alert-dismissible", "fade", "show", "d-flex", "flex-column", "shadow-sm");
  alertDiv.setAttribute("role", "alert");
  alertDiv.setAttribute("id", id);
  alertDiv.style.maxWidth = "320px";

  alertDiv.innerHTML = [
    `  <div class="d-flex align-items-center main-text-semi">`,
    `    <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" height="1.5rem" class="bi bi-exclamation-octagon-fill me-3" viewBox="0 0 16 16">`,
    `      <path d="M11.46.146A.5.5 0 0 0 11.107 0H4.893a.5.5 0 0 0-.353.146L.146 4.54A.5.5 0 0 0 0 4.893v6.214a.5.5 0 0 0 .146.353l4.394 4.394a.5.5 0 0 0 
              .353.146h6.214a.5.5 0 0 0 .353-.146l4.394-4.394a.5.5 0 0 0 .146-.353V4.893a.5.5 0 0 0-.146-.353L11.46.146zM8 4c.535 0 .954.462.9.995l-.35 
              3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>`,
    `    </svg>`,
    `    <span class="main-text-regular">${errorHeader}</span>`,
    `      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`,
    `    </div>`,
    `  <hr />`,
    `  <div>${message}</div>`,
  ].join('');

  window.scrollTo(0, 0);

  alertPlaceholder.append(alertDiv);

  setTimeout(function () {
    bootstrap.Alert.getOrCreateInstance(document.getElementById(`${id}`)).close();
  }, 5000);
}

function toggleInteractables(isBlocking, excludedOnNotBlockingIds = [], otherBlockingUpdates = () => {}) {
  if (isBlocking) {
    loadingContainer.classList.add("d-flex");
    interactiveElems.forEach(elems => {
      elems.disabled = true;
    });
    window.scrollTo(0, 0);
    otherBlockingUpdates();
    return;
  } 

  setTimeout(() => {
    loadingContainer.classList.remove("d-flex");
    interactiveElems.forEach(elems => {
      !excludedOnNotBlockingIds.includes(elems.id) ? elems.disabled = false : null;
    });
    otherBlockingUpdates();
  }, 250);
}
