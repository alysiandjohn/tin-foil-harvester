from flask import Flask, render_template_string, abort
import cloudscraper  # <-- New: Bypasses Cloudflare
from bs4 import BeautifulSoup
import sqlite3, re, time
from datetime import datetime

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
    try:
        c.execute("ALTER TABLE theories ADD COLUMN slug TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower().strip())[:100]

def scrape_with_bypass(url, source):
    scraper = cloudscraper.create_scraper()  # Creates session that bypasses Cloudflare
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        time.sleep(2)  # Delay to avoid rate limits
        r = scraper.get(url, headers=headers, timeout=30)
        if r.status_code == 403 or 'cloudflare' in r.text.lower():
            return "Cloudflare blocked this request. Try manual visit.", "Blocked"
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else source + " Thread"
        text = soup.get_text(strip=True)[:5000]  # Full scraped text, truncated
        return title, text
    except Exception as e:
        return f"Scrape failed: {e}", "Error"

def seed():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM theories")
    # Test sources – real harvest will expand
    test_sources = [
        ("https://www.reddit.com/r/conspiracy/", "Reddit"),
        ("https://boards.4chan.org/pol/", "4chan"),
        ("https://www.godlikeproductions.com/", "GLP")
    ]
    for base_url, source in test_sources:
        title, text = scrape_with_bypass(base_url, source)
        slug = slugify(title)
        archive = "https://archive.is/submit/"  # Mock; real one in harvest
        score = random.randint(70, 100)
        rating = "full schizo" if score > 85 else "tin foil"
        c.execute("INSERT OR REPLACE INTO theories (title, text, url, archive_url, source, score, rating, slug, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (title, text, base_url, archive, source, score, rating, slug, datetime.now().isoformat()))
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