from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
import os
from app import GMAIL
from app import DRIVE
import re
import base64
import email


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
        from_str = ",".join(from_)
        results = GMAIL.users().messages().list(
            userId='me',
            q='in {} in:inbox has:attachment'.format(group),
            maxResults=20)\
            .execute()
        lst = results.get('messages', [])
        filter_messages = []
        for l in lst[2:6]:
            message = GMAIL.users().messages().get(userId='me', id=l['id']).execute()
            payload = message['payload']
            headers = payload['headers']
            parts = payload['parts']
            body = payload['body']

            for part in parts:
                if part['filename']:
                    attachment = GMAIL.users().messages().attachments()\
                        .get(userId='me', id=part['body']['attachmentId'], messageId=l['id'])\
                        .execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))
                    filter_messages.append({
                        'filename': part['filename'],
                        'file_data': file_data
                    })

            for header in headers:
                if header['name'] == 'From':
                    raw_email = re.search("<", header['value']).span()
                    email = header['value'][raw_email[1]:len(header['value'])].rstrip(">")
                    filter_messages.append({
                        'email': email
                    })

        print(filter_messages)
        return redirect("/")
    return redirect("/")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
