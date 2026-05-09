from flask import Flask, render_template_string, redirect
import subprocess
import sys
import os
import socket
from pathlib import Path

app = Flask(__name__)

TOOLS = {
    "shopware-marketing": {
        "name": "Shopware Marketing Campaign Audit",
        "description": "Analyze Shopware newsletter exports, duplicates, groups, DOI, and campaign candidates.",
        "file": "shopware_marketing_campaign_audit.py",
        "port": 5001,
    },
    "shopware-shopify": {
        "name": "Shopware vs Shopify Subscription Audit",
        "description": "Compare Shopware subscribers with Shopify customers and find missing/unsubscribed users.",
        "file": "shopware_shopify_compare.py",
        "port": 5002,
    },
    "shopify-unsubscribed": {
        "name": "Shopify Unsubscribe Audit",
        "description": "Compare old Shopify subscribed export with current Shopify export to find unsubscribed users.",
        "file": "shopify_unsubscribed_audit.py",
        "port": 5003,
    },
}

running_processes = {}

HTML = """
<!doctype html>
<html>
<head>
<title>Newsletter Audit Dashboard</title>
<style>
body{font-family:Arial;background:#f3f4f6;margin:0;padding:30px}
.box{background:white;max-width:1200px;margin:auto;padding:30px;border-radius:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}
.card{background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:22px}
.card h2{margin-top:0}
.btn{background:#111827;color:white;text-decoration:none;padding:12px 18px;border-radius:10px;display:inline-block;margin-top:10px}
.badge{background:#dcfce7;padding:6px 10px;border-radius:8px;font-size:13px}
</style>
</head>
<body>
<div class="box">
<h1>Newsletter Audit Tools Dashboard</h1>
<p>Choose a tool below. The dashboard will start the selected tool automatically.</p>

<div class="grid">
{% for key, tool in tools.items() %}
<div class="card">
<h2>{{ tool.name }}</h2>
<p>{{ tool.description }}</p>
<p><span class="badge">Port {{ tool.port }}</span></p>
<a class="btn" href="/open/{{ key }}">Open Tool</a>
</div>
{% endfor %}
</div>

<br>
<p><b>Note:</b> Keep this dashboard running while using the tools.</p>
</div>
</body>
</html>
"""

def is_port_running(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0

@app.route("/")
def index():
    return render_template_string(HTML, tools=TOOLS)

@app.route("/open/<tool_key>")
def open_tool(tool_key):
    if tool_key not in TOOLS:
        return "Tool not found"

    tool = TOOLS[tool_key]
    file_path = Path(tool["file"])

    if not file_path.exists():
        return f"File not found: {tool['file']}"

    port = tool["port"]

    if not is_port_running(port):
        env = os.environ.copy()
        env["PORT"] = str(port)

        running_processes[tool_key] = subprocess.Popen(
            [sys.executable, str(file_path)],
            env=env
        )

    return redirect(f"http://127.0.0.1:{port}")

if __name__ == "__main__":
    app.run(
        debug=False,
        host="127.0.0.1",
        port=5000,
        use_reloader=False
    )