"""
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* Copyright (C) Metter Media LLC - All Rights Reserved                      *
* Unauthorized copying of this file, via any medium is strictly prohibited  *
* Proprietary and confidential                                              *
* All Rights Reserved                                                       *
* Written by Robby Grodin <robby@toypig.co>, March 2017                     *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
"""
from multiprocessing import Process
import os

from flask import Flask, render_template, g, jsonify, make_response, request
from flask_socketio import SocketIO, emit
from tweepy import API, StreamListener, OAuthHandler, Stream, TweepError
import sqlite3


# Configure global variables
CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCESS_SECRET = os.environ.get('ACCESS_SECRET')

app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'metterboard.db')
))

socketio = SocketIO(
    app,
    async_mode='gevent',
    ping_timeout=30,
    logger=False,
    engineio_logger=False
)

# Connections to Twitter Streams.
# Currently a singleton, but may expand in next iteration.
streams = []


def connect_db():
    """
    Connect to a local db file containing the schema for our twitter board.
    The check_same_thread param allows for threads to share a db connection.
    """
    db = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def init_db():
    """
    Initializes the database schema if no db file exists yet.
    """
    with app.app_context():
        db = get_db()
        with app.open_resource('mb_schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        return db


# Initialize the db schema on startup
init_db()


@socketio.on('connection')
def handle_connection(msg):
    """
    Flush the db contents onto the client upon connection.
    """
    db = get_db()
    cur = db.execute("""
        SELECT id, text, user, screen_name, profile_image_url, media_url
        FROM tblTweet ORDER BY id;
        """)
    tweets = cur.fetchall()
    for tweet in tweets:
        json_data = jsonify({
            'id': tweet['id'],
            'text': tweet['text'],
            'user': tweet['user'],
            'screen_name': tweet['screen_name'],
            'profile_image_url': tweet['profile_image_url'],
            'media_url': tweet['media_url']
        })
        # By using the SID of the current message as a 'room' id, we're able to target the sender only
        socketio.emit(msg['client'], json_data.data, room=request.sid)


@socketio.on('delete_tweet')
def delete_tweet(msg):
    """
    Remove a flagged tweet from the database to prevent being displayed.
    TODO: should this be a flag rather than a deletion?
    """
    tweet_id = msg.get('id')
    if tweet_id:
        delete_from_db(tweet_id)
        socketio.emit('delete_tweet_from_display', {'id': tweet_id})


def delete_from_db(tweet_id):
    """
    db action to remove tweet by id
    """
    db = get_db()
    cur = db.execute("""
        DELETE FROM tblTweet WHERE ID = %s;
        """ % (tweet_id))
    db.commit()


@app.route('/')
def show_entries():
    """
    Display endpoint. Delivers an html scaffold unto which
    we will project 140 characters of pure genius.
    """
    return render_template('show_tweets.html')


@app.route('/admin')
def admin():
    """
    Render the admin panel
    """
    return render_template('admin.html')


@app.route('/track/<hashtag>', methods=['GET'])
def track(hashtag):
    """
    Asynchronous endpoint used to initiate a twitter stream.
    Stream executes in a background process.
    """
    halt_streams()
    stream = track(hashtag)
    streams.append(stream)
    return make_response('', 200)


@app.route('/clear_db', methods=['GET'])
def clear_db():
    """
    Remove all the data in the db file.
    """
    db = get_db()
    db.execute("""DELETE FROM tblTweet;""")
    db.commit()
    return make_response('', 200)


@app.route('/halt', methods=['GET'])
def halt():
    """
    Stop the firehose.
    """
    halt_streams()
    return make_response('', 200)


def halt_streams():
    """
    Kill all streams in the registry.
    """
    for stream in streams:
        stream.disconnect()


def track(hashtag):
    """
    Authenticate to Twitter API and create an asycnhronous stream of tweets
    """
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = API(auth)

    listener = TweetListener(get_db())
    listener.api = api
    stream = Stream(api.auth, listener)
    stream.filter(track=[hashtag], async=True)

    return stream


class TweetListener(StreamListener):
    """
    Custom stream listener.
    Streams tweets in a background thread and makes them available
    to clients and persistent data store.
    """

    def __init__(self, db):
        self.db = db

    def on_status(self, data):
        """
        Handle an incoming tweet on the stream.
        Send it to the db, and to the clients.
        Because this is happening in another process,
        need to fake an app context.
        """
        with app.test_request_context():
            # MM prefers not to display retweets. TODO: make this mutable
            if not data.retweeted and not data.text.startswith('RT @'):
                self.persist_tweet(data)
                self.transmit_tweet(data)
        return True

    def persist_tweet(self, data):
        """
        Persist the vital tweet data to a local sqlite db file
        """
        media_url = data.entities['media'][0]['media_url'] if data.entities.get(
            'media') else None
        self.db.execute("""
                INSERT INTO TBLTWEET (
                    id, text, user, screen_name, profile_image_url, media_url
                ) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");
                """ % (unicode(data.id_str),
                       unicode(data.text.replace('"', '\'').strip()),
                       unicode(data.user.name.replace(
                           '"', '\'').strip()),
                       unicode(data.author.screen_name.replace(
                           '"', '\'').strip()),
                       unicode(data.author.profile_image_url.replace(
                           '"', '\'').strip().replace('normal', 'bigger')),
                       unicode(media_url.replace('"', '\'').strip()) if media_url else str(media_url)
                       )
        )
        self.db.commit()

    def transmit_tweet(self, data):
        """
        Send the tweet to all clients
        """
        # Stream tweet to client
        tweet = {
            'id': unicode(data.id_str),
            'text': unicode(data.text.strip()),
            'user': unicode(data.user.name.strip()),
            'screen_name': unicode(data.author.screen_name.strip()),
            'profile_image_url': unicode(data.user.profile_image_url.strip().replace('normal', 'bigger'))
        }

        # Add media url if present
        media_url = data.entities['media'][0]['media_url'] if data.entities.get(
            'media') else None
        if media_url:
            tweet['media_url'] = unicode(media_url.replace(
                '"', '\'').strip())

        # Transmit tweet to clients
        json_data = jsonify(tweet)
        socketio.emit('tweetstream', unicode(json_data.data.strip()))
        socketio.emit('admin_tweetstream',
                      unicode(json_data.data.strip()))
