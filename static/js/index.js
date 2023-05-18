function loadPrevSession(event) {
  event.preventDefault();
  const savedSession = JSON.parse(sessionStorage.getItem("savedSession"));
  if (!savedSession) {
    appendAlert('Error!', 'savedSession', 'No Saved Session!', 'danger');
    return;
  }
  
  if (!["mongodb", "json"].includes(savedSession["client"])) {
    appendAlert('Error!', 'invalidSessionType', 'Saved Session of Invalid Client Type!', 'danger');
    return;
  }

  if (savedSession["client"] === "mongodb") {
    toggleInteractables(true);
    fetch("/validateMongoDB",
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          uri: savedSession["uri"],
          collection: savedSession["collection"],
          database: savedSession["database"],
          alias: savedSession["alias"]
        })
      })
      .then((res) => {
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
  } else {
    toggleInteractables(true);
    
    fetch(`/existingJSON?filename=${savedSession["filename"]}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then((res) => {
      toggleInteractables(false);

      if (res.status !== 200) {
        appendAlert('Error!', 'jsonSession', 'JSON Session Did Not Resume!', 'danger');
      }

      if (res.redirected) {
        window.location = res.url;
      }
    })
  } 
}
