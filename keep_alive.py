from flask import Flask, render_template_string
from threading import Thread
import psutil
import platform
import socket
import datetime
import os

import requests

app = Flask('')

# Lưu lại thời gian bot start
bot_start_time = datetime.datetime.now()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>HACKED BOT STATUS</title>
    <style>
        body {
            background: black;
            color: #00FF00;
            font-family: monospace;
            text-align: center;
            padding: 40px;
        }
        h1 {
            font-size: 2em;
        }
        #clock {
            font-size: 1.5em;
            margin: 20px 0;
        }
        .info {
            font-size: 1.1em;
            margin-top: 20px;
            text-align: left;
            display: inline-block;
        }
    </style>
    <script>
        function updateClock() {
            var now = new Date();
            var years = now.getFullYear();
            var months = ('0' + (now.getMonth() + 1)).slice(-2);
            var days = ('0' + now.getDate()).slice(-2);
            var hours = ('0' + now.getHours()).slice(-2);
            var minutes = ('0' + now.getMinutes()).slice(-2);
            var seconds = ('0' + now.getSeconds()).slice(-2);
            var formatted = years + '/' + months + '/' + days + ' ' + hours + ':' + minutes + ':' + seconds;
            document.getElementById('clock').innerHTML = formatted;
        }
        setInterval(updateClock, 1000);
        window.onload = updateClock;
    </script>
</head>
<body>
    <h1>🚀 BOT TELEGRAM ONLINE</h1>
    <div id="clock"></div>
    <div class="info">
        <b>OS:</b> {{ os_info }}<br>
        <b>Python Version:</b> {{ python_ver }}<br>
        <b>Hostname:</b> {{ hostname }}<br>
        <b>Local IP:</b> {{ local_ip }}<br>
        <b>Public IP:</b> {{ public_ip }}<br>
        <b>CPU Usage:</b> {{ cpu }}%<br>
        <b>RAM Usage:</b> {{ ram }}%<br>
        <b>System Uptime:</b> {{ sys_uptime }}<br>
        <b>Bot Uptime:</b> {{ bot_uptime }}<br>
    </div>
</body>
</html>
"""

def get_system_uptime():
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now = datetime.datetime.now()
    delta = now - boot_time
    return str(delta).split('.')[0]  # HH:MM:SS

def get_bot_uptime():
    now = datetime.datetime.now()
    delta = now - bot_start_time
    return str(delta).split('.')[0]

def get_public_ip():
    try:
        ip = requests.get('https://api.ipify.org').text
    except:
        ip = "Unavailable"
    return ip

@app.route('/')
def home():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    python_ver = platform.python_version()
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    public_ip = get_public_ip()
    sys_uptime = get_system_uptime()
    bot_uptime = get_bot_uptime()

    return render_template_string(
        HTML_TEMPLATE,
        cpu=cpu,
        ram=ram,
        os_info=os_info,
        python_ver=python_ver,
        hostname=hostname,
        local_ip=local_ip,
        public_ip=public_ip,
        sys_uptime=sys_uptime,
        bot_uptime=bot_uptime
    )

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
