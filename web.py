from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask_sqlalchemy import SQLAlchemy
import os
from app import GMAIL
from app import DRIVE
from app import SHEETS
import re
import base64
import email
from bs4 import BeautifulSoup
from apiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///{}".format(os.path.join(BASE_DIR, "data.db"))
app.config['SECRET_KEY'] = 'this-is-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_folder = db.Column(db.String(255))


class DriveFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.String(255))
    name = db.Column(db.String(255), unique=True)


class DriveFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(255))
    folder_id = db.Column(db.String(255))
    file_name = db.Column(db.String(255))



@app.route("/", methods=['GET', 'POST'])
def index():
    locations = Location.query.all()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        try:
            location = Location(name=name, email=email)
            db.session.add(location)
            db.session.commit()
            flash("Location saved successfully.")
        except Exception as e:
            flash(e)
        return redirect("/")
    return render_template("index.html", locations=locations)


@app.route("/move", methods=['POST'])
def move():
    if request.method == 'POST':
        group = request.form['group']
        from_ = request.form.getlist('from')
        locations = {location.email: location.name for location in Location.query.all()}
        results = GMAIL.users().messages().list(
            userId='me',
            q='in {} in:inbox has:attachment'.format(group),
            maxResults=20)\
            .execute()
        lst = results.get('messages', [])
# labelIds=['UNREAD', 'INBOX']
        final_list = []
        for l in lst:
            temp_dict = {}
            message = GMAIL.users().messages().get(userId='me', id=l['id']).execute()
            payload = message['payload']
            headers = payload['headers']
            parts = payload['parts']
            body = payload['body']
            temp_dict['msg_id'] = l['id']
            temp_dict['snippet'] = message['snippet']

            for header in headers:
                if header['name'] == 'From':
                    raw_email = re.search("<", header['value']).span()
                    email = header['value'][raw_email[1]:len(header['value'])].rstrip(">")
                    temp_dict['email'] = email

                if header['name'] == 'Date':
                    temp_dict['date'] = header['value']

            for part in parts:
                if part['filename']:
                    temp_dict['file_id'] = part['body']['attachmentId']
                    temp_dict['filename'] = part['filename']
            try:
                body = BeautifulSoup(base64.b64decode(
                    bytes(parts[0]['body']['data'].replace("-","+").replace("_","/"), encoding='utf-8')), "lxml")
                temp_dict['body'] = body.body()
            except KeyError:
                temp_dict['body'] = "Test text"
            final_list.append(temp_dict)

        drive = Drive.query.first()
        if not drive:
            parent_folder = DRIVE.files().create(body={
                'name': 'GMAIL_DATA',
                'mimeType': 'application/vnd.google-apps.folder'
            }, fields='id').execute()
            drive = Drive(parent_folder=str(parent_folder.get('id')))
            db.session.add(drive)
            db.session.commit()
        for msg in final_list:
            if msg['email'] in from_:
                if msg['body'] is not None:
                    spreadsheet_params = {
                        'properties': {
                            'title': 'Weekly Deposits'
                        }
                    }
                    spreadsheet = SHEETS.spreadsheets().create(body=spreadsheet_params,
                                                               fields='spreadsheetId').execute()
                    spreadsheet_id = spreadsheet.get('spreadsheetId')
                    data = [{
                        'range': 'A1:E1',
                        'values': [
                            [
                                msg['body']
                            ]
                        ]
                    }]
                    body = {
                        'valueInputOption': 'RAW',
                        'data': data
                    }
                    result = SHEETS.spreadsheets().values().batchUpdate(
                        spreadsheetId=spreadsheet_id, body=body).execute()


                drive_folder_query = DriveFolder.query.filter(DriveFolder.name == locations[msg['email']])\
                    .first()
                if not drive_folder_query:
                    folder_id = DRIVE.files().create(body={
                        'name': locations[msg['email']],
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [drive.parent_folder]
                    }, fields='id').execute()
                    drive_folder = DriveFolder(folder_id=str(folder_id.get('id')), name=locations[msg['email']])
                    db.session.add(drive_folder)
                    db.session.commit()

                attachment = GMAIL.users().messages().attachments()\
                    .get(userId='me', id=msg['file_id'], messageId=msg['msg_id'])\
                    .execute()
                file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))

                if file_data:
                    f = open(os.path.join(BASE_DIR, 'attachments', str(msg['date'])+msg['filename']), 'wb')
                    f.write(file_data)
                    f.close()
                if os.path.exists(os.path.join(BASE_DIR, 'attachments', str(msg['date'])+msg['filename'])):
                    drive_file_query = DriveFile.query\
                        .filter(DriveFile.folder_id == drive_folder_query.folder_id,
                                DriveFile.file_name == str(msg['date'])+msg['filename'])\
                        .first()
                    if not drive_file_query:
                        media = MediaFileUpload(os.path.join(BASE_DIR, 'attachments', str(msg['date'])+msg['filename']),
                                                mimetype='application/octect-stream',
                                                resumable=True)
                        file_id = DRIVE.files().create(body={
                            'name': str(msg['date'])+msg['filename'],
                            'parents': [drive_folder_query.folder_id]
                        }, fields='id', media_body=media).execute()
                        drive_file = DriveFile(file_id=str(file_id.get('id')),
                                               folder_id=drive_folder_query.folder_id,
                                               file_name=str(msg['date'])+msg['filename'])
                        db.session.add(drive_file)
                        db.session.commit()
        flash("Mail synced to drive.")
        return redirect("/")

    return redirect("/")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
