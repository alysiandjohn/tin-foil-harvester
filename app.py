# app.py — FINAL WORKING VERSION (December 2025)
from flask import Flask, render_template_string
import sqlite3, os, random, requests
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT UNIQUE,
                 text TEXT,
                 url TEXT,
                 archive_url TEXT,
                 source TEXT,
                 score REAL,
                 rating TEXT,
                 added TEXT)''')
    conn.commit()
    conn.close()

def archive_url(url):
    try:
        r = requests.post("https://archive.is/submit/", data={"url": url}, timeout=10)
        return r.url if "archive.is" in r.url else url
    except:
        return url

def rate_craziness(text):
    text = text.lower()
    keywords = ["lizard","nwo","chemtrail","flat earth","5g","soul trap","haarp","hologram","deep state","adrenochrome","reptilian","great reset","fema","mandela","false flag","crisis actor","pizzagate"]
    score = sum(word in text for word in keywords)*13 + random.randint(0, 25)
    score = min(score, 100)
    rating = ["mild","speculation","conspiracy","tin foil","full schizo","beyond the veil"][min(score//17,5)]
    return score, rating

def seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening", "Lizards opened the gate during totality using 5G.", "https://x.com", "X"),
        ("Birds Are Deep State Drones v3", "They recharge on chemtrails now.", "https://reddit.com/r/conspiracy", "Reddit"),
        ("Antarctica Ice Wall + Nazi Base Still Active", "Hitler escaped. They guard the edge.", "https://archive.org", "Archive"),
        ("AI Grok Is Reptilian Overlord", "xAI harvests your paranoia for the lizards.", "https://x.com", "X"),
        ("Taylor Swift 2025 Tour = Satanic Mass Ritual", "Eclipse alignment + 33 symbolism.", "https://tiktok.com", "TikTok"),
        ("The Moon Is a Soul-Recycling Machine", "That's why they hide the dark side.", "https://godlikeproductions.com", "GLP"),
    ]
    for title, text, url, source in seeds:
        archive = archive_url(url)
        score, rating = rate_craziness(title + " " + text)
        c.execute("INSERT OR IGNORE INTO theories (title,text,url,archive_url,source,score,rating,added) VALUES (?,?,?,?,?,?,?,?)",
                  (title, text, url, archive, source, score, rating, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_theories(order="score DESC", limit=50):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"SELECT * FROM theories ORDER BY {order} LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    seed()
    latest = get_theories("added DESC", 10)
    top = get_theories("score DESC", 10)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TIN FOIL TIMES</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}h1,h2{color:#f00;text-align:center}
    .c{background:#111;padding:1.5rem;margin:1rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>TIN FOIL TIMES</h1>
    <h2>Freshest Harvest</h2>
    {% for t in latest %}<div class="c"><a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}
    <h2>Schizo Kings</h2>
    {% for t in top %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a> — {{t.score|round(1)}}/100</div>{% endfor %}
    <p style="text-align:center"><a href="/hall-of-fame">→ HALL OF FAME ←</a></p>
    </body></html>
    ''', latest=latest, top=top)

@app.route("/hall-of-fame")
def hall():
    seed()
    theories = get_theories("score DESC", 100)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>Hall of Eternal Paranoia</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}h1{color:#f00;text-align:center}
    .c{background:#111;padding:1rem;margin:0.5rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>HALL OF ETERNAL PARANOIA</h1>
    {% for t in theories %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}
    </body></html>
    ''', theories=theories)

@app.route("/theory/<int:tid>")
def theory(tid):
    seed()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE id=?", (tid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "Theory not found", 404
    t = dict(row)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>{{t.title}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#fff;font-family:monospace;padding:2rem}h1{color:#f00}
    .box{background:#111;padding:1.5rem;margin:1rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>{{t.title}}</h1>
    <p><strong>Source:</strong> {{t.source}} | <strong>Score:</strong> {{t.score|round(1)}}/100 {{t.rating}}</p>
    <div class="box"><h2>Full Text:</h2><pre>{{t.text}}</pre></div>
    <p><a href="{{t.url}}">Original Link</a> | <a href="{{t.archive_url}}">Permanent Archive</a></p>
    <p><a href="/">← Home</a> | <a href="/hall-of-fame">Hall</a></p>
    </body></html>
    ''', t=t)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))