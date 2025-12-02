# app.py — FINAL, NO ERRORS, REAL FOLDERS + CLOUDFLARE BYPASS
from flask import Flask, render_template_string, abort
import sqlite3, os, random, re, time
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
DB = 'theories.db'
scraper = cloudscraper.create_scraper()  # Bypasses Cloudflare

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT,
                 text TEXT,
                 url TEXT,
                 archive_url TEXT,
                 source TEXT,
                 score REAL,
                 rating TEXT,
                 slug TEXT UNIQUE,
                 added TEXT)''')
    try:
        c.execute("ALTER TABLE theories ADD COLUMN slug TEXT UNIQUE")
    except:
        pass
    conn.commit()
    conn.close()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower().strip())[:100]

def seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM theories")
    
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening", "Lizards used 5G during totality to open gates.", "https://x.com", "X"),
        ("Birds Are Deep State Drones v3", "2025 model recharges on chemtrails.", "https://reddit.com/r/conspiracy", "Reddit"),
        ("Antarctica Ice Wall Confirmed", "UN guards the edge. Hitler still alive.", "https://godlikeproductions.com", "GLP"),
        ("AI Grok Is Reptilian Overlord", "xAI harvests paranoia for lizards.", "https://x.com", "X"),
    ]
    for title, text, url, source in seeds:
        slug = slugify(title)
        archive = f"https://archive.is/submit/?url={url}"
        score = random.randint(70, 98)
        rating = "full schizo" if score > 88 else "tin foil"
        c.execute("""INSERT OR IGNORE INTO theories 
                     (title,text,url,archive_url,source,score,rating,slug,added) 
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (title, text, url, archive, source, score, rating, slug, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_theories():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, source, score, rating, slug FROM theories ORDER BY score DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    seed()
    theories = get_theories()
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TIN FOIL ARCHIVE</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem}
    h1{color:#f00;text-align:center}a{color:#0ff;text-decoration:none}
    .folder{background:#111;padding:1.5rem;margin:1rem;border:3px solid #f00;border-radius:10px}</style></head><body>
    <h1>TIN FOIL ARCHIVE</h1>
    {% for t in theories %}
    <div class="folder">
      <h2><a href="/conspiracy/{{t.slug}}">{{t.title}}</a></h2>
      <p>Source: {{t.source}} | Score: {{t.score}}/100 {{t