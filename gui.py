import PySimpleGUI as sg
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv("MONGO_URI")


def get_database():
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client["gem5-vision"]["resources"]


collection = get_database()

# get keys from first document
columns = collection.find_one({}).keys()
print(columns)

fields = []
for i in columns:
    fields.append([sg.Text(i), sg.Push(), sg.Multiline(size=(50, 5), key=i)])

fields.append([sg.Push(), sg.Button("Update"), sg.Button("Back")])

layout1 = [[sg.Text("Enter resource id")], [sg.Input()], [sg.Button("Find")]]

layout = [
    [
        sg.Column(layout1, key="-COL1-"),
        sg.Column(
            fields,
            visible=False,
            key="-COL2-",
            scrollable=True,
            vertical_scroll_only=True,
            size=(600, 600),
        ),
    ]
]

window = sg.Window("Window Title", layout)

layout = 1
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Cancel":
        break
    if event == "Back":
        window["-COL2-"].update(visible=False)
        layout = 1
        window["-COL1-"].update(visible=True)
    if event == "Find":
        resource = collection.find_one({"id": values[0]})
        print(resource)
        window[f"-COL{layout}-"].update(visible=False)
        layout = 2
        window[f"-COL{layout}-"].update(visible=True)
    print("You entered ", values[0])

window.close()
