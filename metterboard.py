import sqlite3
from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET
from tweepy import API, StreamListener, OAuthHandler, Stream, TweepError
from flask import Flask, render_template, g, jsonify
from flask_socketio import SocketIO, emit
import os
from multiprocessing import Process


app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'metterboard.db'),
    DEBUG=True,
    SECRET_KEY='supersecret',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('MB_SETTINGS', silent=True)

socketio = SocketIO(app,  async_mode='gevent', ping_timeout=30, logger=False, engineio_logger=False)

# Connections to Twitter
streams = []

@socketio.on('my_event')
def test_message(message):
    print message

def connect_db():
    db = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('mb_schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database')

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select text, user, screen_name, profile_image_url from tblTweet order by id desc')
    tweets = cur.fetchall()
    return render_template('show_tweets.html', tweets=tweets)

@app.route('/admin/<hashtag>')
def admin(hashtag):
    for stream in streams:
        stream.disconnect()
    stream = track(hashtag)
    streams.append(stream)
    return hashtag

class TweetListener(StreamListener):

    def __init__(self, db):
        self.db = db

    def on_status(self, data):
        # Persist tweet to DB
        with app.test_request_context():
            self.db.execute(
                    """insert into tbltweet (text, user, screen_name, profile_image_url) 
                    values (%d, \"%s\", \"%s\", \"%s\", \"%s\");
                    """ % (data.id,
                        data.text.replace('"', '\''), 
                        data.user.name.replace('"', '\''), 
                        data.author.screen_name.replace('"', '\''), 
                        data.author.profile_image_url.replace('"', '\''))
                    )
            self.db.commit()
            print 'tweet by ' + str(data.user.name.encode('utf-8').strip())
            # Stream tweet to client
            json_data = jsonify({
                'id': data.id.encode('utf-8').strip(),
                'text': data.text.encode('utf-8').strip(), 
                'user': data.user.name.encode('utf-8').strip(), 
                'screen_name': data.author.screen_name.encode('utf-8').strip(), 
                'profile_image_url': data.user.profile_image_url.encode('utf-8').strip()
            })
            socketio.emit('tweetstream', json_data.data.encode('utf-8').strip())
        return True

def track(hashtag):
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = API(auth)
    
    listener = TweetListener(get_db())
    listener.api = api
    stream = Stream(api.auth, listener)
    stream.filter(track=[hashtag], async=True)
   
    return stream
