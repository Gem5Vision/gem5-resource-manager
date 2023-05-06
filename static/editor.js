var editor;
var originalModel;
var modifiedModel;

require.config({
  paths: {
    vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs",
  },
});
require(["vs/editor/editor.main"], () => {
  originalModel = monaco.editor.createModel(`{\n}`, "json");
  modifiedModel = monaco.editor.createModel(`{\n}`, "json");
  editor = monaco.editor.createDiffEditor(document.getElementById("editor"), {
    theme: "vs-dark",
    language: "json",
    automaticLayout: true,
  });
  editor.setModel({
    original: originalModel,
    modified: modifiedModel,
  });
  fetch("/schema")
    .then((res) => res.json())
    .then((data) => {
      monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
        trailingCommas: "error",
        comments: "error",
        validate: true,
        schemas: [
          {
            uri: "http://json-schema.org/draft-07/schema",
            fileMatch: ["*"],
            schema: data,
          },
        ],
      });
    });
});

function checkErrors() {
  let errors = monaco.editor.getModelMarkers({ resource: modifiedModel.uri });
  if (errors.length > 0) {
    console.log(errors);
    let str = "";
    errors.forEach((error) => {
      str += error.message + "\n";
    });
    alert(str);
    return true;
  }
  return false;
}

function update(e) {
  e.preventDefault();
  if (checkErrors()) {
    return;
  }
  let json = JSON.parse(modifiedModel.getValue());
  let id = document.getElementById("id").value;
  console.log(json);
  fetch("/update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id: id, resource: json }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      find(e);
    });
}

function add(e) {
  e.preventDefault();
  if (checkErrors()) {
    return;
  }
  let json = JSON.parse(modifiedModel.getValue());
  console.log(json);
  fetch("/insert", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(json),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      find(e);
    });
}

function addVersion(e) {
  e.preventDefault();
  console.log("add version");
  if (checkErrors()) {
    return;
  }
  addVersions();
  let json = JSON.parse(modifiedModel.getValue());
  console.log(json["resource_version"]);
  fetch("/checkExists", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      id: json["id"],
      resource_version: json["resource_version"],
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data["exists"]);
      if (data["exists"] == true) {
        alert("Resource version already exists");
      } else {
        fetch("/insert", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(json),
        })
          .then((res) => res.json())
          .then((data) => {
            console.log(data);
            find(e);
          });
      }
    });
}

function deleteRes(e) {
  e.preventDefault();
  console.log("delete");
  let id = document.getElementById("id").value;
  let resource_version = JSON.parse(originalModel.getValue())[
    "resource_version"
  ];
  console.log(resource_version);
  fetch("/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id: id, resource_version: resource_version }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      find(e);
    });
}

let didChange = false;
document.getElementById("id").onchange = function () {
  console.log("id changed");
  didChange = true;
};

function addVersions() {
  let select = document.getElementById("version-dropdown");
  select.innerHTML = "Latest";
  fetch("/versions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      id: document.getElementById("id").value,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      let select = document.getElementById("version-dropdown");
      if (data.length == 0) {
        data = [{ resource_version: "Latest" }];
      }
      data.forEach((version) => {
        let option = document.createElement("option");
        option.value = version["resource_version"];
        option.innerText = version["resource_version"];
        select.appendChild(option);
      });
    });
}

function find(e) {
  e.preventDefault();
  if (didChange) {
    addVersions();
    didChange = false;
  }

  editor.getEditorType() === "vs.editor.ICodeEditor" ? closeSchema() : null;

  fetch("/find", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      id: document.getElementById("id").value,
      resource_version: document.getElementById("version-dropdown").value,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data["exists"] == false) {
        fetch("/keys", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            category: document.getElementById("category").value,
            id: document.getElementById("id").value,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            delete data._id;
            data["id"] = document.getElementById("id").value;
            data["category"] = document.getElementById("category").value;
            originalModel.setValue(JSON.stringify(data, null, 4));
            modifiedModel.setValue(JSON.stringify(data, null, 4));
            document.getElementById("update").disabled = true;
            document.getElementById("add").disabled = false;
            document.getElementById("add_version").disabled = true;
            document.getElementById("delete").disabled = true;
          });
      } else {
        data = data[0];
        console.log(data);
        delete data._id;
        originalModel.setValue(JSON.stringify(data, null, 4));
        modifiedModel.setValue(JSON.stringify(data, null, 4));
        document.getElementById("update").disabled = false;
        document.getElementById("add").disabled = true;
        document.getElementById("delete").disabled = false;
        document.getElementById("add_version").disabled = false;
        document.getElementById("category").value = data.category;
        document.getElementById("version-dropdown").value =
          data.resource_version;
      }
    });
}

window.onload = () => {
  let ver_dropdown = document.getElementById("version-dropdown");
  let option = document.createElement("option");
  option.value = "Latest";
  option.innerHTML = "Latest";
  ver_dropdown.appendChild(option);
  fetch("/categories")
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      let select = document.getElementById("category");
      data.forEach((category) => {
        let option = document.createElement("option");
        option.value = category;
        option.innerHTML = category;
        select.appendChild(option);
      });
    });
};

const myModal = new bootstrap.Modal("#ConfirmModal", {
  keyboard: false,
});

let confirmButton = document.getElementById("confirm");

function showModal(event, callback) {
  event.preventDefault();
  myModal.show();
  confirmButton.onclick = () => {
    callback(event);
    myModal.hide();
  };
}

const schemaButton = document.getElementById('loadSchema');

function openSchema() {
  fetch('/schema', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then((res) => res.json())
  .then((data) => {
    console.log(data);

    editor.dispose();

    editor = monaco.editor.create(document.getElementById("editor"), {
      theme: "vs-dark",
      language: "json",
      automaticLayout: true,
      readOnly: true
    });

    model = monaco.editor.createModel(`{\n}`, "json");
    editor.setModel(model);

    model.setValue(JSON.stringify(data, null, 4));
    document.getElementById("update").disabled = true;
    document.getElementById("add").disabled = true;
    document.getElementById("delete").disabled = true;
    document.getElementById("add_version").disabled = true;

    schemaButton.textContent = "Close Schema";
    schemaButton.onclick = closeSchema;

    const editorTitle = document.getElementById("editor-title");
    editorTitle.children[0].style.display = 'none';
    editorTitle.children[1].textContent = 'Schema (Read Only)';
  });
} 

function closeSchema() {
  schemaButton.textContent = "Load Schema";
  
  editor.dispose();

  editor = monaco.editor.createDiffEditor(document.getElementById("editor"), {
    theme: "vs-dark",
    language: "json",
    automaticLayout: true,
  });
  editor.setModel({
    original: originalModel,
    modified: modifiedModel,
  });

  const editorTitle = document.getElementById("editor-title");
  editorTitle.children[0].style.display = 'unset';
  editorTitle.children[1].textContent = 'Edited';

  schemaButton.onclick = openSchema;
}