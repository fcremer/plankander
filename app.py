from flask import Flask, Response
from flask_httpauth import HTTPBasicAuth
import psycopg2
from psycopg2.extras import RealDictCursor
from ics import Calendar, Event
from datetime import timedelta
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# Database connection parameters from environment variables
db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# User credentials for basic authentication from environment variables
users = {
    os.getenv("FLASK_USERNAME"): os.getenv("FLASK_PASSWORD")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

def fetch_events():
    """ Fetch events from the PostgreSQL database where due_date is not null. """
    conn = None
    events = []
    try:
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT name, due_date FROM card WHERE due_date IS NOT NULL;")
        events = cur.fetchall()
        cur.close()
    except psycopg2.Error as e:
        print("An error occurred:", e)
    finally:
        if conn:
            conn.close()
    return events

@app.route('/calender/calendar.ics')
@auth.login_required
def calendar():
    """ Generate and return a dynamic ICS file based on database data. """
    events = fetch_events()
    c = Calendar()
    for event in events:
        e = Event()
        e.name = event['title']
        e.begin = event['due_date'].strftime('%Y-%m-%d %H:%M:%S')
        e.end = (event['due_date'] + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')  # assuming 1 hour duration
        c.events.add(e)

    response = Response(str(c), mimetype="text/calendar")
    response.headers['Content-Disposition'] = "attachment; filename=calendar.ics"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
