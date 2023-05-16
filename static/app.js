const loadingContainer = document.getElementById("loading-container");
const loginButton = document.getElementById("login");
const alertPlaceholder = document.getElementById('liveAlertPlaceholder');

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

const interactiveElems = document.querySelectorAll('button, input, select');

function toggleInteractables(isBlocking) {
  if (isBlocking) {
    loadingContainer.classList.add("d-flex");
    interactiveElems.forEach(elems => {
      elems.disabled = true;
    });
    window.scrollTo(0, 0);
    return;
  } 

  setTimeout(() => {
    loadingContainer.classList.remove("d-flex");
    interactiveElems.forEach(elems => {
      elems.disabled = false;
    });
  }, 250);
}

function loadPrevSession(event) {
  event.preventDefault();
  const prevSession = localStorage.getItem("savedSession");
  if (!prevSession) {
    appendAlert('Error!', 'prevSession', 'No Saved Session!', 'danger');
  } else {
    window.location = prevSession;
  }
}

function handleMongoDBLogin(event) {
  event.preventDefault();
  const activeTab = document.querySelector(".nav-link.active").getAttribute("id");

  activeTab === "enter-uri-tab" ? handleEnteredURI() : handleGenerateURI();

  return;
}

function handleEnteredURI() {
  const uri = document.getElementById('uri').value;
  const collection = document.getElementById('collection').value;
  const database = document.getElementById('database').value;
  const alias = document.getElementById('alias').value;
  const emptyInputs = [{ type: "Collection", value: collection }, { type: "Database", value: database }, { type: "URI", value: uri }];
  let error = false;

  for (let i = 0; i < emptyInputs.length; i++) {
    if (emptyInputs[i].value === "") {
      appendAlert("Error", `${emptyInputs[i].type}`, `Cannot Proceed Without ${emptyInputs[i].type} Value!`, 'danger');
      error = true;
    }
  }

  if (error) {
    return;
  }

  handleMongoURLFetch(uri, collection, database, alias);
}

function handleGenerateURI() {
  const connection = document.getElementById('connection').checked;
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const collection = document.getElementById('collectionGenerate').value;
  const database = document.getElementById('databaseGenerate').value;
  const host = document.getElementById('host').value;
  const alias = document.getElementById('aliasGenerate').value;
  const options = document.getElementById('options').value.split(",");
  let generatedURI = "";
  const emptyInputs = [{ type: "Host", value: host }, { type: "Collection", value: collection }, { type: "Database", value: database }];
  let error = false;

  for (let i = 0; i < emptyInputs.length; i++) {
    if (emptyInputs[i].value === "") {
      appendAlert("Error", `${emptyInputs[i].type}`, `Cannot Proceed Without ${emptyInputs[i].type} Value!`, 'danger');
      error = true;
    }
  }

  if (error) {
    return;
  }

  generatedURI = connection ? "mongodb+srv://" : "mongodb://";
  if (username && password) {
    generatedURI += `${encodeURIComponent(username)}:${encodeURIComponent(password)}@`;
  }

  generatedURI += host;

  if (options.length) {
    generatedURI += `/?${options.join("&")}`;
  }

  handleMongoURLFetch(generatedURI, collection, database, alias);
}

function handleMongoURLFetch(uri, collection, database, alias) {
  toggleInteractables(true);

  fetch("/validateMongoDB",
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uri: uri,
        collection: collection,
        database: database,
        alias: alias
      })
    })
    .then((res) => {
      console.log("URI Validation Response Status: " + res.status);
      toggleInteractables(false);

      if (!res.ok) {
        res.json()
          .then(error => {
            appendAlert('Error!', 'mongodbValidationError', `${error.error}`, 'danger');
          });
        return;
      }

      res.redirected ? window.location = res.url : appendAlert('Error!', 'invalidRes', 'Invalid Server Response!', 'danger');
    })
}

function handleJSONLogin(event) {
  event.preventDefault();
  const activeTab = document.querySelector(".nav-link.active").getAttribute("id");
  if (activeTab === "remote-tab") {
    handleRemoteJSON();
  } else if (activeTab === "existing-tab") {
    const filename = document.getElementById("existing-dropdown").value;
    if (filename !== "No Existing Files") {
      toggleInteractables(true);

      fetch(`/existingJSON?filename=${filename}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        .then((res) => {
          console.log("Existing JSON Response Status: " + res.status);
          toggleInteractables(false);

          if (res.status !== 200) {
            appendAlert('Error!', 'invalidURL', 'Invalid JSON File URL!', 'danger');
          }
          if (res.redirected) {
            window.location = res.url;
          }
        })
    }
  } else {
    handleUploadJSON();
  }
  return;
}

function handleRemoteJSON() {
  const url = document.getElementById("jsonRemoteURL").value;
  const filename = document.getElementById("remoteFilename").value;
  const emptyInputs = [{ type: "URL", value: url }, { type: "Filename", value: filename }];
  let error = false;

  for (let i = 0; i < emptyInputs.length; i++) {
    if (emptyInputs[i].value === "") {
      appendAlert("Error", `${emptyInputs[i].type}`, `Cannot Proceed Without ${emptyInputs[i].type} Value!`, 'danger');
      error = true;
    }
  }

  if (error) {
    return;
  }

  const params = new URLSearchParams();
  params.append('filename', filename + ".json");
  params.append('q', url);

  const flask_url = `/validateJSON?${params.toString()}`;

  toggleInteractables(true);

  fetch(flask_url, {
    method: 'GET',
  })
    .then((res) => {
      console.log("JSON Remote Response Status: " + res.status);
      toggleInteractables(false);

      if (res.status === 400) {
        appendAlert('Error!', 'invalidURL', 'Invalid JSON File URL!', 'danger');
      }

      if (res.status === 409) {
        const myModal = new bootstrap.Modal(document.getElementById('conflictResolutionModal'), { focus: true, keyboard: false });
        document.getElementById("header-filename").textContent = `"${filename}"`;
        myModal.show();
      }

      if (res.redirected) {
        window.location = res.url;
      }
    })
}

var filename;

function handleUploadJSON() {
  const jsonFile = document.getElementById("jsonFile");
  const file = jsonFile.files[0];

  if (jsonFile.value === "") {
    appendAlert('Error!', 'emptyUpload', 'Cannot Proceed Without Uploading a File!', 'danger');
    return;
  }

  filename = file.name;

  const form = new FormData();
  form.append("file", file);

  toggleInteractables(true);

  fetch("/validateJSON", {
    method: 'POST',
    body: form
  })
    .then((res) => {
      console.log("JSON Upload Response Status: " + res.status);
      toggleInteractables(false);

      if (res.status === 400) {
        appendAlert('Error!', 'invalidUpload', 'Invalid JSON File Upload!', 'danger');
      }

      if (res.status === 409) {
        const myModal = new bootstrap.Modal(document.getElementById('conflictResolutionModal'), { focus: true, keyboard: false });
        document.getElementById("header-filename").textContent = `"${filename}"`;
        myModal.show();
      }

      if (res.redirected) {
        window.location = res.url;
      }
    })
}

function saveConflictResolution() {
  const conflictResolutionModal = bootstrap.Modal.getInstance(document.getElementById("conflictResolutionModal"));
  const selectedValue = document.querySelector('input[name="conflictRadio"]:checked').id;
  const activeTab = document.querySelector(".nav-link.active").getAttribute("id");

  if (selectedValue === null) {
    appendAlert('Error!', 'nullRadio', 'Fatal! Null Radio!', 'danger');
    return;
  }

  if (selectedValue === "clearInput") {
    if (activeTab === "upload-tab") {
      document.getElementById("jsonFile").value = '';
    }

    if (activeTab === "remote-tab") {
      document.getElementById('remoteFilename').value = '';
      document.getElementById('jsonRemoteURL').value = '';
    }

    conflictResolutionModal.hide();
    handleConflictResolution("clearInput", filename.split(".")[0]);
    return;
  }

  if (selectedValue === "openExisting") {
    conflictResolutionModal.hide();
    handleConflictResolution("openExisting", filename.split(".")[0]);
    return;
  }

  if (selectedValue === "overwrite") {
    conflictResolutionModal.hide();
    handleConflictResolution("overwrite", filename.split(".")[0]);
    return;
  }

  if (selectedValue === "newFilename") {
    const updatedFilename = document.getElementById("updatedFilename").value;
    if (updatedFilename === "") {
      appendAlert('Error!', 'emptyFilename', 'Must Enter A New Name!', 'danger');
      return;
    }

    if (`${updatedFilename}.json` === filename) {
      appendAlert('Error!', 'sameFilenames', 'Cannot Have Same Name as Current!', 'danger');
      return;
    }

    conflictResolutionModal.hide();
    handleConflictResolution("newFilename", updatedFilename);
    return;
  }
}

function handleConflictResolution(resolution, filename) {
  const params = new URLSearchParams();
  params.append('resolution', resolution);
  params.append('filename', filename !== "" ? filename + ".json" : "");

  const flask_url = `/resolveConflict?${params.toString()}`;
  
  toggleInteractables(true);

  fetch(flask_url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then((res) => {
      console.log("JSON Upload Response Status: " + res.status);
      toggleInteractables(false);

      if (res.status === 204) {
        console.log("Input Cleared, Cached File Deleted, Resources Unset");
        return;
      }

      if (res.status !== 200) {
        appendAlert('Error!', 'didNotRedirect', 'Server Did Not Redirect!', 'danger');
        return;
      }

      if (res.redirected) {
        window.location = res.url;
      }
    })
}

window.onload = () => {
  if (window.location.pathname === "/login/json") {
    fetch('/existingFiles', {
      method: 'GET',
    })
      .then((res) => res.json())
      .then((data) => {
        let select = document.getElementById("existing-dropdown");
        if (data.length === 0) {
          data = ["No Existing Files"];
        }
        data.forEach((files) => {
          let option = document.createElement("option");
          option.value = files;
          option.innerHTML = files;
          select.appendChild(option);
        });
      });
  }
}
