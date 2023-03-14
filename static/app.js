var editor
var originalModel
var modifiedModel

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' } });
require(["vs/editor/editor.main"], () => {
    /* editor = monaco.editor.create(document.getElementById('editor'), {
        value: ``,
        language: 'json',
        theme: 'vs-dark',
    }); */
    originalModel = monaco.editor.createModel(``, 'json');
    modifiedModel = monaco.editor.createModel(``, 'json');
    editor = monaco.editor.createDiffEditor(document.getElementById('editor'), {
        theme: 'vs-dark',
        language: 'json',
    });
    editor.setModel({
        original: originalModel,
        modified: modifiedModel
    });
});

function update(e) {
    e.preventDefault()
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
        })
}

function add(e) {
    e.preventDefault()
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
        })
}

function deleteRes(e) {
    e.preventDefault()
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
                fetch('/keys')
                    .then((res) => res.json())
                    .then((data) => {
                        console.log(data)
                        delete data._id
                        data['id'] = document.getElementById('id').value
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