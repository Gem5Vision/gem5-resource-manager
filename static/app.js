function update(e) {
    e.preventDefault()
    let json = JSON.parse(document.getElementById('editor').value)
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
    let json = JSON.parse(document.getElementById('editor').value)
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

function deleteRes (e){
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
                        document.getElementById('editor').value = JSON.stringify(data, null, 4)
                        document.getElementById('update').disabled = true
                        document.getElementById('add').disabled = false
                        document.getElementById('delete').disabled = true
                    })
            } else {
                // remove _id from data
                delete data._id
                document.getElementById('editor').value = JSON.stringify(data, null, 4)
                document.getElementById('update').disabled = false
                document.getElementById('add').disabled = true
                document.getElementById('delete').disabled = false
            }
        })
}