# Metterboard

### Set Up

1. Obtain authentication on dev twitter dashboard, set environment variables for:
- CONSUMER_KEY
- CONSUMER_SECRET
- ACCESS_TOKEN
- ACCESS_SECRET

2. Create virtualenv
```bash
virtualenv venv
pip install requirements.txt
```

3. Precompile handlebars templates (NOTE: may need to `npm install handlebars`)
```bash
handlebars templates/tweets.handlebars -f static/tweets.tpl.js
handlebars templates/admin_tweets.handlebars -f static/admin_tweets.tpl.js
```

### Run
```bash
gunicorn -k gevent -w 1 metterboard:app
```
