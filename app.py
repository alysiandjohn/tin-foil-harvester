from flask import Flask, render_template_string
import sqlite3, os, random
from datetime import datetime
import requests
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

def force_seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Clear old data for testing
    c.execute("DELETE FROM theories")
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening", "Lizards used 5G during totality to open gates. Proof in the shadows!!?", "https://x.com/conspiracy", "X", 92.0, "full schizo"),
        ("Birds Are Deep State Drones v3", "They recharge on chemtrails now. Wake up sheeple!!!", "https://reddit.com/r/conspiracy", "Reddit", 85.0, "tin foil"),
        ("Antarctica Ice Wall + Nazi Base Still Active", "Hitler escaped. They guard the edge. Flat Earth confirmed???", "https://archive.org", "Archive", 78.0, "conspiracy"),
        ("AI Grok Is Reptilian Overlord", "xAI harvests paranoia for lizard masters. Grok is the key!!!", "https://x.com", "X", 95.0, "beyond the veil"),
        ("Taylor Swift 2025 Tour = Satanic Mass Ritual", "Eclipse alignment + 33 symbolism everywhere. Satanic elite exposed.", "https://tiktok.com", "TikTok", 81.0, "tin foil")
    ]
    for title, text, url, source, score, rating in seeds:
        archive = url + " (archived)"  # Mock for now
        c.execute("INSERT INTO theories (title, text, url, archive_url, source, score, rating, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (title, text, url, archive, source, score, rating, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print("Seeded 5 theories – IDs 1-5 now available.")

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
    force_seed()
    latest = get_theories("added DESC", 5)
    top = get_theories("score DESC", 5)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TIN FOIL TIMES</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}h1,h2{color:#f00;text-align:center}
    .c{background:#111;padding:1.5rem;margin:1rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>🛸 TIN FOIL TIMES 🛸</h1>
    <h2>Freshest Harvest</h2>
    {% for t in latest %}<div class="c"><a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}
    <h2>Schizo Kings</h2>
    {% for t in top %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a> — {{t.score|round(1)}}/100</div>{% endfor %}
    <p style="text-align:center"><a href="/hall-of-fame">→ HALL OF FAME ←</a></p>
    </body></html>
    ''', latest=latest, top=top)

@app.route("/hall-of-fame")
def hall():
    force_seed()
    theories = get_theories("score DESC", 10)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>Hall of Eternal Paranoia</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}h1{color:#f00;text-align:center}
    .c{background:#111;padding:1rem;margin:0.5rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>🏆 HALL OF ETERNAL PARANOIA 🏆</h1>
    {% for t in theories %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}
    <p style="text-align:center"><a href="/">← Home</a></p>
    </body></html>
    ''', theories=theories)

@app.route("/theory/<int:tid>")
def theory(tid):
    force_seed()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE id=?", (tid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return render_template_string('''
        <!DOCTYPE html><html><head><title>404 - Theory Not Found</title>
        <style>body{background:#000;color:#f00;font-family:monospace;padding:2rem;text-align:center}</style></head><body>
        <h1>404 - Theory Not Found</h1>
        <p>ID {{tid}} doesn't exist. <a href="/">Back to Home</a></p>
        </body></html>
        ''', tid=tid), 404
    t = dict(row)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>{{t.title}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#fff;font-family:monospace;padding:2rem}h1{color:#f00}
    .box{background:#111;padding:1.5rem;margin:1rem;border-left:6px solid #f00}a{color:#0ff}</style></head><body>
    <h1>{{t.title}}</h1>
    <p><strong>Source:</strong> {{t.source}} | <strong>Score:</strong> {{t.score|round(1)}}/100 {{t.rating}}</p>
    <div class="box"><h2