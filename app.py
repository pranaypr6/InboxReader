import time
import os
import pickle
from gtts import gTTS
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode, urlsafe_b64encode

SCOPES = ['https://mail.google.com/']

##                                               ##
## MUST HAVE credentials.json in root directory  ##
## TOKEN.PICKLE is created automatically         ##


def gmail_authenticate():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


service = gmail_authenticate()


def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(
            userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages


def read_message(service, message):
    msg = service.users().messages().get(
        userId='me', id=message['id'], format='full').execute()
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    finalText = "You have an unread message from "
    if headers:
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name.lower() == 'from':
                finalText += value
            if name.lower() == "to":
                pass
            if name.lower() == "subject":
                finalText += " about " + value
            if name.lower() == "date":
                finalText += " on " + value
    if parts:
        for part in parts:
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            if mimeType == "text/plain":
                if data:
                    text = urlsafe_b64decode(data).decode()
                    finalText += " " + text
    return finalText


def getUnreadMessages(service):
    return service.users().messages().list(userId='me', q='is:unread').execute()


while True:
    results = getUnreadMessages(service)
    if "messages" in results:
        for msg in results['messages']:
            m = read_message(service, msg)
            print(m)
            myobj = gTTS(text=m, lang="en", slow=False)
            myobj.save("welcome.mp3")
            os.system("welcome.mp3")
            service.users().messages().modify(userId='me', id=msg['id'], body={
                'removeLabelIds': ['UNREAD']}).execute()
    else:
        myobj = gTTS(text="You don't have any new emails",
                     lang="en", slow=False)
        myobj.save("nomails.mp3")
        os.system("nomails.mp3")

    time.sleep(300)
