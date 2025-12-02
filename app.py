# app.py — FINAL FOLDER-STYLE ARCHIVE (one conspiracy = one folder/page)
from flask import Flask, render_template_string, abort
import sqlite3, os, random, requests, re
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 slug TEXT UNIQUE,
                 title TEXT,
                 full_text TEXT,
                 url TEXT,
                 archive_url TEXT,
                 source TEXT,
                 score REAL,
                 rating TEXT,
                 added TEXT)''')
    conn.commit()
    conn.close()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower().strip())[:100]

def archive_url(url):
    try:
        r = requests.post("https://archive.is/submit/", data={"url": url}, timeout=15)
        return r.url if "archive.is" in r.url else url
    except:
        return url

def rate_craziness(text):
    text = text.lower()
    keywords = ["lizard","nwo","chemtrail","flat earth","5g","soul trap","haarp","hologram","deep state","adrenochrome","reptilian","great reset","fema","mandela","false flag","pizzagate"]
    score = sum(word in text for word in keywords)*14 + random.randint(0,25)
    score = min(score, 100)
    rating = ["mild","speculation","conspiracy","tin foil","full schizo","beyond the veil"][min(score//17,5)]
    return score, rating

def seed_harvest():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening", "Lizards used 5G + HAARP during totality. Shadows don’t lie. Full thread inside.", "https://x.com/conspiracy420", "X"),
        ("Birds Are Deep State Drones v3", "2025 model now has facial recognition. They’re watching your every move.", "https://reddit.com/r/conspiracy", "Reddit"),
        ("Antarctica Ice Wall Confirmed", "UN guards the edge. Hitler still alive in Base 211.", "https://godlikeproductions.com", "GLP"),
        ("AI Grok Is Reptilian Overlord", "xAI built to harvest human paranoia for lizard masters.", "https://x.com", "X"),
    ]
    for title, text, url, source in seeds:
        slug = slugify(title)
        archive = archive_url(url)
        score, rating = rate_craziness(title + text)
        c.execute("INSERT OR IGNORE INTO theories (slug,title,full_text,url,archive_url,source,score,rating,added) VALUES (?,?,?,?,?,?,?,?,?)",
                  (slug, title, text, url, archive, source, score, rating, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_theories():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories ORDER BY score DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    seed_harvest()
    theories = get_theories()
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TIN FOIL ARCHIVE</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}
    h1{color:#f00;text-align:center}a{color:#0ff;text-decoration:none}
    .folder{background:#111;padding:1.5rem;margin:1rem;border:2px solid #f00;border-radius:8px}</style></head><body>
    <h1> TIN FOIL ARCHIVE</h1>
    <p>Each conspiracy has its own permanent folder below.</p>
    {% for t in theories %}
    <div class="folder">
      <h2><a href="/conspiracy/{{t.slug}}">{{t.title}}</a></h2>
      <p><strong>Source:</strong> {{t.source}} | <strong>Tin Foil Score:</strong> {{t.score|round(1)}}/100 {{t.rating}}</p>
    </div>
    {% endfor %}
    </body></html>
    ''', theories=theories)

@app.route("/conspiracy/<slug>")
def conspiracy_folder(slug):
    seed_harvest()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE slug=?", (slug,))
    t = c.fetchone()
    conn.close()