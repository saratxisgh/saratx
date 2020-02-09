from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRED_FILE = os.path.join(BASE_DIR, 'credentials', 'credentials_gmail.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/drive']

store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('{}'.format(CRED_FILE), SCOPES)
    creds = tools.run_flow(flow, store)

GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

#results = GMAIL.users().messages().list(userId='me', q='in Deposits in:inbox has:attachment '
#                                                       'from:(ad.missionbend@isgh.org)', maxResults=20).execute()
#deposits = results.get('messages', [])

#print("============>>>>>")
#for deposit in deposits:
#    message = GMAIL.users().messages().get(userId='me', id=deposit['id']).execute()
    #print(message['payload']['filename'])
    #print(">>==<<")
#    for header in message['payload']['headers']:
#        if header['name'] == 'From':
#            print(header['value'])
#    print(">>>==<<<")
    #print(message['payload']['body'])
    #print(">>>>==<<<<")
    #print(message['payload']['parts'])
