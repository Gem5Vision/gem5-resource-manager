const alertPlaceholder = document.getElementById('liveAlertPlaceholder');

const appendAlert = (errorHeader, message, type) => {
  const alertDiv = document.createElement('div');

  alertDiv.classList.add("alert", `alert-${type}`, "alert-dismissible", "fade", "show", "d-flex", "flex-column", "shadow-sm");
  alertDiv.setAttribute("role", "alert");

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

  alertPlaceholder.append(alertDiv);
  
  setTimeout(function() {
    bootstrap.Alert.getOrCreateInstance(document.querySelector(".alert")).close();
  }, 3000);
}

function loadPrevSession(event) {
  event.preventDefault();
  const prevSession = localStorage.getItem("URI");
  if (!prevSession) {
    appendAlert('Error!', 'No Saved Session!', 'danger');
  } else {
    const url = '/editor?uri=' + encodeURIComponent(prevSession); 
    window.location = url;
  }
}

function handleMongoDBLogin(event, saveStatus) {
  event.preventDefault();
  const uri = document.getElementById('uri').value;
  const collection = document.getElementById('collection').value;
  const database = document.getElementById('database').value;
  const alias = document.getElementById('alias').value;

  const validateInputs = [{type : "Collection", value : collection}, { type : "Database", value : database}, {type : "URI", value : uri}];

  let error = false;

  if (saveStatus) {
    localStorage.setItem("URI", uri);
  }

  for (let i = 0; i < validateInputs.length; i++) {
    if (validateInputs[i].value === "") {
      appendAlert("Error", `Cannot Proceed Without ${validateInputs[i].type} Value!`, 'danger');
      error = true;
    }
  }

  if (error) {
    return;
  }

  const params = new URLSearchParams();
  params.append('uri', encodeURIComponent(uri));
  params.append('collection', collection);
  params.append('database', database);
  params.append('alias', alias);

  const url = `/validateURI?${params.toString()}`;
  fetch(url,
  {
      method: 'GET',
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then((res) => {
    console.log("URI Validation Response Status: " + res.status);
    
    if (res.status === 400) {
      appendAlert('Error!', 'Cannot Proceed With Empty URI!', 'danger');
    }
    
    if (res.redirected) {
      window.location = res.url;
    }
  })
} 

function handleJSONLogin(event, saveStatus) {
  event.preventDefault();
  const activeTab = document.querySelector(".nav-link.active").getAttribute("id");
  console.log(activeTab);

  if (activeTab === "remote-tab") {
    handleRemoteJSON();
  }

  if (activeTab === "upload-tab") {
    handleUploadJSON();
  }

  return;
}

function handleRemoteJSON() {
  const url = document.getElementById("jsonRemoteURL").value;

  if (url === "") {
    appendAlert('Error!', 'Cannot Proceed With Empty URL!', 'danger');
    return;
  }

  const flask_url = "/validateJSON?q=" + encodeURIComponent(url);
  fetch(flask_url, {
    method: 'GET',
  })
  .then((res) => {
    console.log("JSON Remote Response Status: " + res.status);
    
    if (res.status === 400) {
      appendAlert('Error!', 'Invalid JSON File URL!', 'danger');
    }
    
    if (res.redirected) {
      window.location = res.url;
    }
  })
}

function handleUploadJSON() {
  const jsonFile = document.getElementById("jsonFile");
  const file = jsonFile.files[0];

  if (jsonFile === "") {
    appendAlert('Error!', 'Cannot Proceed Without Uploading a File!', 'danger');
    return;
  }

  const form = new FormData();
  form.append("file", file);

  const flask_url = "/validateJSON?q=";
  fetch(flask_url, {
    method: 'POST',
    body: form
  })
  .then((res) => {
    console.log("JSON Upload Response Status: " + res.status);
    
    if (res.status === 400) {
      appendAlert('Error!', 'Invalid JSON File Upload!', 'danger');
    }
    
    if (res.redirected) {
      window.location = res.url;
    }
  })
}