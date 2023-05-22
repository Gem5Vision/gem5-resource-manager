window.onload = () => {
  fetch("/getSavedSessionsAliasList")
  .then((res) => res.json())
  .then((data) => {
    let select = document.getElementById("sessions-dropdown");
    if (data.length === 0) {
      data = ["No Existing Files"];
      document.getElementById("showSavedSessionModal").disabled = true;
      return;
    }
    data.forEach((files) => {
      let option = document.createElement("option");
      option.value = files;
      option.innerHTML = files;
      select.appendChild(option);
    });
  })
}

const loadSessionBtn = document.getElementById("loadSession");
loadSessionBtn.disabled = true;

let password = document.getElementById("session-password");
password.addEventListener("input", () => {
  loadSessionBtn.disabled = password.value === "";
});

function showSavedSessionModal() {
  const savedSessionModal = new bootstrap.Modal(document.getElementById('savedSessionModal'), { focus: true, keyboard: false });
  savedSessionModal.show();
}

function loadSession() {
  bootstrap.Modal.getInstance(document.getElementById("savedSessionModal")).hide();

  toggleInteractables(true);

  fetch("/loadSession", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      alias: document.getElementById("sessions-dropdown").value,
      password: document.getElementById("session-password").value
    })
  })
  .then((res) => {
    document.getElementById("session-password").value = "";

    toggleInteractables(false);

    if (res.status !== 200) {
      res.json()
      .then((data) => {
        appendAlert('Error!', 'invalidStatus', `${data["error"]}`, 'danger');
      })
    }

    if (res.redirected) {
      window.location = res.url
    }
  })
}
