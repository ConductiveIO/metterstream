from flask import Flask

app = Flask(__name__)

# Set up endpoints
@app.route('/')
def index():
  return 'Index Page'

@app.route('/modboard')
def modboard():
  return 'Mod Board'

@app.route('/display')
def display():
  return 'display'

if __name__ == "__main__":
  app.run()
