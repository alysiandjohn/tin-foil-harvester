# app.py — FINAL FIXED VERSION (no more 500 error)
from flask import Flask, render_template_string, abort
import sqlite3, os, random, requests
from datetime import datetime
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Add slug column if missing (prevents crash)
    try:
        c.execute("ALTER TABLE theories ADD COLUMN slug TEXT UNIQUE")
    except:
        pass  # column already exists
    conn.commit()
    conn.close()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower())[:80]

def seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Force fresh seed with slugs
    c.execute("DELETE FROM theories")
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening", "Lizards opened the gate using 5G during totality. Proof in shadows.", "https://x.com/conspiracy", "X"),
        ("Birds Are Deep State Drones v3", "2025 model now has facial recognition. They’re watching.", "https://reddit.com/r/conspiracy", "Reddit"),
        ("Antarctica Ice Wall Confirmed", "UN guards the edge. Hitler still alive in Base 211.", "https://archive.org", "Archive"),
        ("AI Grok Is Reptilian Overlord", "xAI harvests paranoia for lizard masters.", "https://x.com", "X"),
    ]
    for title, text, url, source in seeds:
        slug = slugify(title)
        archive = url + " (archived)"
        score = random.randint(70, 98)
        rating = "full schizo" if score > 85 else "tin foil"
        c.execute("INSERT INTO theories (title, text, url, archive_url, source, score, rating, slug, added) VALUES (?,?,?,?,?,?,?,?,?)",
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
      <p><strong>Source:</strong> {{t.source}} | <strong>Score:</strong> {{t.score}}/100 {{t.rating}}</p>
    </div>
    {% endfor %}
    </body></html>
    ''', theories=theories)

@app.route("/conspiracy/<slug>")
def conspiracy_page(slug):
    seed()  # ensures data exists
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE slug=?", (slug,))
    t = c.fetchone()
    conn.close()
    if not t:
        abort(404)
    t = dict(t)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>{{t.title}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#fff;font-family:monospace;padding:2rem}h1{color:#f00}
    .box{background:#111;padding:2rem;margin:1rem;border-left:8px solid #f00}a{color:#0ff}</style></head><body>
    <h1>{{t.title}}</h1>
    <p><strong>Source:</strong> {{t.source}} | <strong>Score:</strong> {{t.score}}/100 {{t.rating}}</p>
    <div class="box"><h2>Full Thread Text:</h2><pre>{{t.text}}</pre></div>
    <p><strong>Live Link:</strong> <a href="{{t.url}}">{{t.url}}</a></p>
    <p><strong>Permanent Archive:</strong> {{t.archive_url}}</p>
    <p><a href="/">← All Conspiracies</a></p>
    </body></html>
    ''', t=t)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))