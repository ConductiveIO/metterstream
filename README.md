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

### Run
```bash
gunicorn -k gevent -w 1 metterboard:app
```
