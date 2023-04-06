var editor
var originalModel
var modifiedModel

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' } });
require(["vs/editor/editor.main"], () => {
    originalModel = monaco.editor.createModel(`{\n}`, 'json');
    modifiedModel = monaco.editor.createModel(`{\n}`, 'json');
    editor = monaco.editor.createDiffEditor(document.getElementById('editor'), {
        theme: 'vs-dark',
        language: 'json'
    });
    editor.setModel({
        original: originalModel,
        modified: modifiedModel
    });
    fetch('/schema').then((res) => res.json())
        .then((data) => {
            monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                trailingCommas: "error",
                comments: "error",
                validate: true,
                schemas: [{
                    uri: "http://myserver/foo-schema.json",
                    fileMatch: ["*"],
                    schema: data
                }]
            });
        })
});

function checkErrors() {
    // only check modified model
    let errors = monaco.editor.getModelMarkers({ resource: modifiedModel.uri })
    if (errors.length > 0) {
        console.log(errors)
        let str = ''
        errors.forEach((error) => {
            str += error.message + '\n'
        })
        alert(str)
        return true
    }
    return false
}

function update(e) {
    e.preventDefault()
    if (checkErrors()) {
        return
    }
    let json = JSON.parse(modifiedModel.getValue())
    console.log(json)
    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(json)
    }).then((res) => res.json())
        .then((data) => {
            console.log(data)
            find(e)
        })
}

function add(e) {
    e.preventDefault()
    if (checkErrors()) {
        return
    }
    let json = JSON.parse(modifiedModel.getValue())
    console.log(json)
    fetch('/insert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(json)
    }).then((res) => res.json())
        .then((data) => {
            console.log(data)
            find(e)
        })
}

function deleteRes(e) {
    e.preventDefault()
    console.log('delete')
    let id = document.getElementById('id').value
    fetch('/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
    }).then((res) => res.json())
        .then((data) => {
            console.log(data)
            find(e)
        })
}

function find(e) {
    e.preventDefault()
    fetch('/find', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: document.getElementById('id').value
        })
    })
        .then((res) => res.json())
        .then((data) => {
            if (data == null) {
                fetch('/keys',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            category: document.getElementById('category').value
                        })
                    })
                    .then((res) => res.json())
                    .then((data) => {
                        console.log(data)
                        delete data._id
                        data['id'] = document.getElementById('id').value
                        data['category'] = document.getElementById('category').value
                        originalModel.setValue(JSON.stringify(data, null, 4))
                        modifiedModel.setValue(JSON.stringify(data, null, 4))
                        document.getElementById('update').disabled = true
                        document.getElementById('add').disabled = false
                        document.getElementById('delete').disabled = true
                    })
            } else {
                // remove _id from data
                delete data._id
                originalModel.setValue(JSON.stringify(data, null, 4))
                modifiedModel.setValue(JSON.stringify(data, null, 4))
                // document.getElementById('editor').value = JSON.stringify(data, null, 4)
                document.getElementById('update').disabled = false
                document.getElementById('add').disabled = true
                document.getElementById('delete').disabled = false
            }
        })
}

window.onload = () => {
    fetch('/categories').then((res) => res.json())
        .then((data) => {
            console.log(data)
            let select = document.getElementById('category')
            data.forEach((category) => {
                let option = document.createElement('option')
                option.value = category
                option.innerHTML = category
                select.appendChild(option)
            })
        })
}

const myModal = new bootstrap.Modal('#ConfirmModal', {
    keyboard: false
})

let confirmButton = document.getElementById('confirm')

function showModal(event, callback) {
    event.preventDefault();
    myModal.show();
    confirmButton.onclick = () => {
        callback(event);
        myModal.hide();
    }
}