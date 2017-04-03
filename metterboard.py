from tweepy import API, StreamListener, OAuthHandler, Stream, TweepError
import sqlite3
from flask import Flask, render_template, g, jsonify, make_response, request
from flask_socketio import SocketIO, emit
import os
from multiprocessing import Process


CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCESS_SECRET = os.environ.get('ACCESS_SECRET')

app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'metterboard.db')
))

socketio = SocketIO(app,  async_mode='gevent', ping_timeout=30, logger=False, engineio_logger=False)

# Connections to Twitter
streams = []

def connect_db():
    db = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('mb_schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        return db

# Initialize DB
init_db()

@socketio.on('connection')
def handle_connection(msg):
    db = get_db()
    cur = db.execute('select id, text, user, screen_name, profile_image_url, media_url from tblTweet order by id desc')
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
        socketio.emit(msg['client'], json_data.data)

@socketio.on('delete_tweet')
def delete_tweet(msg):
    tweet_id = msg.get('id')
    if tweet_id:
        delete_from_db(tweet_id)
        socketio.emit('delete_tweet_from_display', {'id': tweet_id})

def delete_from_db(tweet_id):
    db = get_db()
    cur = db.execute("""
        DELETE FROM tblTweet WHERE ID = %s;
    """ % (tweet_id))
    db.commit()

@app.route('/')
def show_entries():
    return render_template('show_tweets.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/track/<hashtag>', methods=['GET'])
def track(hashtag):
    halt_streams()
    stream = track(hashtag)
    streams.append(stream)
    return make_response('', 200)

@app.route('/clear_db', methods=['GET'])
def clear_db():
    db = get_db()
    db.execute('DELETE FROM tblTweet;')
    db.commit()
    return make_response()

@app.route('/halt', methods=['GET'])
def halt():
    halt_streams()
    return make_response('', 200)

def halt_streams():
    for stream in streams:
        stream.disconnect()

class TweetListener(StreamListener):

    def __init__(self, db):
        self.db = db

    def on_status(self, data):
        # Persist tweet to DB
        with app.test_request_context():
            media_url = data.entities['media'][0]['media_url'] if data.entities.get('media') else None
            self.db.execute(
                    """insert into tbltweet (id, text, user, screen_name, profile_image_url, media_url) 
                    values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");
                    """ % (data.id_str.encode('utf-8'),
                        data.text.replace('"', '\'').encode('utf-8').strip(), 
                        data.user.name.replace('"', '\'').encode('utf-8').strip(), 
                        data.author.screen_name.replace('"', '\'').encode('utf-8').strip(), 
                        data.author.profile_image_url.replace('"', '\'').encode('utf-8').strip(),
                        media_url.replace('"', '\'').encode('utf-8').strip() if media_url else str(media_url)
                    ))
            self.db.commit()
            
            # Stream tweet to client
            data = {
                'id': data.id_str.encode('utf-8'),
                'text': data.text.encode('utf-8').strip(), 
                'user': data.user.name.encode('utf-8').strip(), 
                'screen_name': data.author.screen_name.encode('utf-8').strip(), 
                'profile_image_url': data.user.profile_image_url.encode('utf-8').strip()
            }

            # Add media url if present
            if media_url:
                data['media_url'] = media_url.replace('"', '\'').encode('utf-8').strip()
            
            # Transmit tweet to clients
            json_data = jsonify(data)
            socketio.emit('tweetstream', json_data.data.encode('utf-8').strip())
            socketio.emit('admin_tweetstream', json_data.data.encode('utf-8').strip())
        return True

def track(hashtag):
    print 'setting up tracking'
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    print 'auth'
    if CONSUMER_KEY:
        print CONSUMER_KEY
    api = API(auth)
    
    listener = TweetListener(get_db())
    listener.api = api
    stream = Stream(api.auth, listener)
    stream.filter(track=[hashtag], async=True)
   
    return stream
