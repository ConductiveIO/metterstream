import sqlite3
from tweepy import API, StreamListener, OAuthHandler, Stream, TweepError
from flask import Flask, render_template, g
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


def connect_db():
    db = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database."""
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
    '''
    proc = Process(target=track, args=(hashtag,))
    proc.start()
    proc.join()
    '''
    track(hashtag)
    return hashtag

class TweetListener(StreamListener):

    def __init__(self, db):
        self.db = db

    def on_status(self, data):
        self.db.execute(
                """insert into tbltweet (text, user, screen_name, profile_image_url) 
                values (\"%s\", \"%s\", \"%s\", \"%s\");
                """ % (data.text, data.user.name, data.author.screen_name, data.author.profile_image_url)
                )
        self.db.commit()
        return True

def track(hashtag):
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = API(auth)

    listener = TweetListener(get_db())
    listener.api = api
    stream = Stream(api.auth, listener)
    stream.filter(track=[hashtag], async=True)
