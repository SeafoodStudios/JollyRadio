from flask import Flask, render_template, request
import uuid
import json
import requests

app = Flask(__name__)

@app.route('/station/<path:subpath>/')
def index(subpath):
    try:
        try:
            uuid_obj = uuid.UUID(str(subpath))
        except ValueError:
            return "Invalid station UUID.", 400
        
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations/byuuid/{subpath}")

        if not raw_data.status_code == 200:
            return "Data could not be fetched.", 500
        
        parsed_data = json.loads(raw_data.text)

        if not parsed_data:
            return "Invalid station UUID.", 400

        station = parsed_data[0]
        
        if not station.get("codec") == "MP3":
            return "Unsupported music type."
        
        return render_template('radio.html', link=station.get("url"))
    except:
        return "Generic error.", 500

@app.route('/local/')
def local():
    try:
        x_forwarded_for = request.headers.get('X-Forwarded-For', '')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.remote_addr
            
        ip_raw = requests.get(f"http://ip-api.com/json/{ip}")
        if not ip_raw.status_code == 200:
            return "Data could not be fetched.", 500
        ip_parsed = ip_raw.json()
        city = ip_parsed.get("city")
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations/bystate/{city}")
        parsed_data = json.loads(raw_data.text)

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
    except:
        return "Generic error.", 500
@app.route('/explore/')
def explore():
    try:
        raw_data = requests.get(f"https://de1.api.radio-browser.info/json/stations?order=random&limit=100")
        parsed_data = json.loads(raw_data.text)

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
    except:
        return "Generic error.", 500
