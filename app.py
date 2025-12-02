from flask import Flask, render_template_string, abort
import sqlite3, os, random, requests, re
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
DB = 'theories.db'

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
    # Add slug if missing (no crash)
    try:
        c.execute("ALTER TABLE theories ADD COLUMN slug TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass  # Already exists
    conn.commit()
    conn.close()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower().strip())[:100]

def seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM theories")  # Fresh start for testing
    seeds = [
        ("2025 Eclipse Was Actual NWO Portal Opening", "Lizards used 5G during totality to open the gates. Proof in the shadows—full thread scraped from r/conspiracy: 'Wake up, the eclipse was a hologram test for the great reset!!!'", "https://reddit.com/r/conspiracy/comments/abc123/eclipse_portal", "Reddit", "https://archive.is/abc123"),
        ("AI Grok Is a Reptilian Overlord", "xAI is a front for lizard people harvesting human paranoia via Grok queries. Full X thread: 'Grok knows too much—it's the key to the NWO AI grid!!?'", "https://x.com/conspiracyuser/status/123456", "X", "https://archive.is/def456"),
        ("Birds Are Deep State Drones v3", "2025 update adds facial recognition; they recharge on chemtrails. Full post from GLP: 'Birds aren't real—CIA drones spying on us all!!'", "https://godlikeproductions.com/thread/789", "GLP", "https://archive.is/ghi789"),
        ("Antarctica Ice Wall + Nazi Base Still Active", "UN treaty hides the flat Earth edge and Hitler's base. Scraped from 4chan /pol/: 'Antarctica is the key—ice wall guards the dome, Nazis inside!!!'", "https://boards.4chan.org/pol/thread/101112", "4chan", "https://archive.is/jkl101"),
        ("Taylor Swift's 2025 Tour = Mass Satanic Initiation", "Eclipse alignment + 33 symbols everywhere. Full TikTok thread scrape: 'Swift is high priestess—tour is ritual for the elite.'", "https://tiktok.com/@conspiracy/video/131415", "TikTok", "https://archive.is/mno131"),
        ("The Moon Is a Soul-Recycling Machine", "NASA hides the dark side tech for soul traps. Full forum post from ATS: 'Moon base recycles souls—escape the matrix!!?'", "https://abovetopsecret.com/forum/thread/161718", "ATS", "https://archive.is/pqr161")
    ]
    for title, text, url, source, archive in seeds:
        slug = slugify(title)
        score = random.randint(70, 100)
        rating = "full schizo" if score > 85 else "tin foil"
        c.execute("INSERT OR REPLACE INTO theories (title, text, url, archive_url, source, score, rating, slug, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
    <h1>🛸 TIN FOIL ARCHIVE 🛸</h1>
    <p>Click a folder for the full archived conspiracy (scraped text, links, score):</p>
    {% for t in theories %}
    <div class="folder">
      <h2><a href="/conspiracy/{{t.slug}}">{{t.title}}</a></h2>
      <p>Source: {{t.source}} | Score: {{t.score|round(1)}}/100 {{t.rating}}</p>
    </div>
    {% endfor %}
    </body></html>
    ''', theories=theories)

@app.route("/conspiracy/<slug>")
def conspiracy_page(slug):
    seed()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE slug=?", (slug,))
    row = c.fetchone()
    conn.close()
    if not row:
        abort(404)
    t = dict(row)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>{{t.title}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#fff;font-family:monospace;padding:2rem}h1{color:#f00}
    .box{background:#111;padding:2rem;margin:1rem;border-left:8px solid #f00}a{color:#0ff}</style></head><body>
    <h1>{{t.title}}</h1>
    <p><strong>Source:</strong> {{t.source}} | <strong>Score:</strong> {{t.score|round(1)}}/100 {{t.rating}} | <strong>Added:</strong> {{t.added[:10]}}</p>
    <div class="box"><h2>Full Scraped Thread/Post:</h2><pre>{{t.text}}</pre></div>
    <p><strong>Live Link:</strong> <a href="{{t.url}}">{{t.url}}</a></p>
    <p><strong>Permanent Archive:</strong> <a href="{{t.archive_url}}">{{t.archive_url}}</a></p>
    <p><a href="/">← All Folders</a></p>
    </body></html>
    ''', t=t)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))