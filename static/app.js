const alertPlaceholder = document.getElementById('liveAlertPlaceholder');

const appendAlert = (message, type) => {
  const wrapper = document.createElement('div')
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible fade show d-flex align-items-center" role="alert">`,
    `   <svg xmlns="http://www.w3.org/2000/svg" class="bi bi-exclamation-triangle-fill flex-shrink-0 me-3" height="1.5rem" viewBox="0 0 16 16" role="img" aria-label="Warning:">`,
    `     <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>`,
    `   </svg>`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    '</div>'
  ].join('')

  alertPlaceholder.append(wrapper)
}

function loadPrevSession(event) {
  event.preventDefault();
  const prevSession = localStorage.getItem("URI");
  if (!prevSession) {
    appendAlert('ERROR! No Saved Session!', 'danger');
    setTimeout(function() {
      bootstrap.Alert.getOrCreateInstance(document.querySelector(".alert")).close();
    }, 3000);
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

  const url = '/validateURI?uri=' + encodeURIComponent(uri);
  fetch(url,
  {
      method: 'GET',
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then((res) => {
    console.log("URI Validation Response Status: " + res.status)
    if (res.status === 400) {
      appendAlert('ERROR! Cannot Proceed With Empty URI!', 'danger');
      setTimeout(function() {
        bootstrap.Alert.getOrCreateInstance(document.querySelector(".alert")).close();
      }, 3000);
    }
    
    if (res.redirected) {
      window.location = res.url;
    }
  })
} 
