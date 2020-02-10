from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRED_FILE = os.path.join(BASE_DIR, 'credentials', 'credentials_gmail.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/drive']

store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('{}'.format(CRED_FILE), SCOPES)
    creds = tools.run_flow(flow, store)

GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))


""" Drive API
"""

CRED_FILE = os.path.join(BASE_DIR, 'credentials', 'credentials_gmail.json')
SCOPES = ['https://www.googleapis.com/auth/drive']

store = file.Storage('storage1.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('{}'.format(CRED_FILE), SCOPES)
    creds = tools.run_flow(flow, store)

DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))


CRED_FILE = os.path.join(BASE_DIR, 'credentials', 'client_secret_sheets.json')
SCOPES = ['https://www.googleapis.com/auth/sheets']

store = file.Storage('storage2.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('{}'.format(CRED_FILE), SCOPES)
    creds = tools.run_flow(flow, store)

SHEETS = discovery.build('sheets', 'v4', http=creds.authorize(Http()))
# creds = ServiceAccountCredentials.from_json_keyfile_name(CRED_FILE, SCOPES)
# SHEETS = gspread.authorize(creds)

#results = GMAIL.users().messages().list(userId='me', q='in Deposits in:inbox has:attachment '
#                                                       'from:(ad.missionbend@isgh.org)', maxResults=20).execute()
