const alertPlaceholder = document.getElementById('liveAlertPlaceholder');

const appendAlert = (errorHeader, message, type) => {
  const wrapper = document.createElement('div');
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible fade show d-flex flex-column shadow-sm" role="alert">`,
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
    `</div>`
  ].join('');

  alertPlaceholder.append(wrapper);

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

function handleLogin(event, saveStatus) {
  event.preventDefault();
  const uri = document.getElementById('uri').value;

  if (saveStatus) {
    localStorage.setItem("URI", uri);
  }

  if (uri === "") {
    appendAlert('Error!', 'Cannot Proceed With Empty URI!', 'danger');
    return;
  }

  const url = '/validateURI?uri=' + encodeURIComponent(uri);
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
