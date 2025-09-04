from flask import Flask, render_template, request
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from deep_translator import GoogleTranslator
from better_profanity import profanity
import requests
import logging
import uuid
import json
import re

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

profanity.load_censor_words()
headers = {'User-Agent': 'JollyRadio/1.0 (We are a radio website to make you more jolly!; contact: contact@seafoodstudios.com; +https://jollyradio.seafoodstudios.com)'}

@app.route('/station/<path:subpath>/')
def station(subpath):
    try:
        try:
            uuid_obj = uuid.UUID(str(subpath))
        except ValueError:
            return "Invalid station UUID.", 400
        
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations/byuuid/{subpath}", timeout=5, headers=headers)

        if not raw_data.status_code == 200:
            return "Data could not be fetched.", 500
        
        parsed_data = json.loads(raw_data.text)
        if parsed_data == []:
            return "No results.", 400

        if not parsed_data:
            return "Invalid station UUID.", 400

        station = parsed_data[0]
        
        if not station.get("url", "Unknown").startswith("https://"):
            return "Unsupported station.", 400

        if profanity.contains_profanity(GoogleTranslator(source='auto', target='en').translate(station.get("name"))):
            return "Unsupported station.", 400
            
        if not station.get("codec") == "MP3":
            return "Unsupported music type.", 500

        data = []
        index = 0
        for item in station:
            if index > 99:
                break
            index += 1
            data.append((item, station[item]))
                
        return render_template('radio.html', link=station.get("url"), name=station.get("name"), country = station.get("country"),homepage = station.get("homepage"), data=data)
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500

@app.route('/local/')
def local():
    try:
        x_forwarded_for = request.headers.get('X-Forwarded-For', '')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.remote_addr
            
        ip_raw = requests.get(f"http://ip-api.com/json/{ip}", timeout=5, headers=headers)
        if not ip_raw.status_code == 200:
            return "Data could not be fetched.", 500
        ip_parsed = ip_raw.json()
        city = ip_parsed.get("city")
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations/bystate/{city}", timeout=5, headers=headers)
        parsed_data = json.loads(raw_data.text)
        if parsed_data == []:
            return "No results.", 400

        stations = parsed_data
        data = []
        index = 0
        for station in stations:
            if index > 99:
                break
            index += 1
            if station.get("codec", "Unknown") == "MP3":
                data.append((station.get("name", "Unknown"), station.get("homepage", "Unknown"), station.get("stationuuid", "")))
        return render_template('local.html', data=data)
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
@app.route('/explore/')
def explore():
    try:
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations?order=random&limit=100", timeout=5, headers=headers)
        parsed_data = json.loads(raw_data.text)
        if parsed_data == []:
            return "No results.", 400

        stations = parsed_data
        data = []
        index = 0
        for station in stations:
            if index > 99:
                break
            index += 1
            if station.get("codec", "Unknown") == "MP3":
                data.append((station.get("name", "Unknown"), station.get("homepage", "Unknown"), station.get("stationuuid", "")))
        return render_template('explore.html', data=data)
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
@app.route('/search/')
def search():
    subpath = request.args.get('q', '')
    if not bool(re.fullmatch(r'[A-Za-z0-9 ]+', subpath)):
        return "Input can only have alphanumerics with optional spaces.", 400
    if profanity.contains_profanity(GoogleTranslator(source='auto', target='en').translate(subpath)):
        return "Nothing profane, please!", 400
    try:
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations/byname/{subpath}", timeout=5, headers=headers)
        parsed_data = json.loads(raw_data.text)
        if parsed_data == []:
            return "No results.", 400

        stations = parsed_data
        data = []
        index = 0
        for station in stations:
            if index > 99:
                break
            index += 1
            if station.get("codec", "Unknown") == "MP3" and station.get("url", "Unknown").startswith("https://"):
                data.append((station.get("name", "Unknown"), station.get("homepage", "Unknown"), station.get("stationuuid", "")))
        return render_template('name.html', data=data)
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
@app.route('/ping')
def ping():
    try:
        return "pong", 200
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
@app.route('/terms')
def terms():
    try:
        return render_template('tos.html')
    except Exception as e:
        logger.exception(e)
        return "Generic error.", 500
