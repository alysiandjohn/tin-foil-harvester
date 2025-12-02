from flask import Flask, render_template_string, abort
import sqlite3, os, random, re, time
from datetime import datetime

app = Flask(__name__)
DB = 'theories.db'

# Try to import scraping libraries, fallback if they fail
try:
    import cloudscraper
    from bs4 import BeautifulSoup
    SCRAPING_ENABLED = True
    scraper = cloudscraper.create_scraper()
except ImportError as e:
    app.logger.error(f"Scraping libraries not available: {e}")
    SCRAPING_ENABLED = False

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT, text TEXT, url TEXT, archive_url TEXT,
                 source TEXT, score REAL, rating TEXT, slug TEXT UNIQUE, added TEXT)''')
    conn.commit()
    conn.close()

def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower().strip())
    return slug.strip('-')[:100]

def harvest_worldwide():
    if not SCRAPING_ENABLED:
        app.logger.error("Scraping disabled - libraries not available")
        return
        
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Check if we have recent data
    try:
        c.execute("SELECT COUNT(*) FROM theories WHERE added > datetime('now', '-6 hours')")
        recent = c.fetchone()[0]
        if recent > 5:
            app.logger.info(f"Using cached data: {recent} recent theories")
            conn.close()
            return
    except:
        pass

    sources = [
        ("https://old.reddit.com/r/conspiracy/top/?t=day&limit=25", "Reddit"),
    ]

    for url, source in sources:
        try:
            app.logger.info(f"Scraping {source}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            r = scraper.get(url, timeout=15, headers=headers)
            
            if r.status_code != 200:
                app.logger.error(f"Failed {source}: status {r.status_code}")
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Old Reddit layout is easier to scrape
            posts = soup.find_all('a', class_='title')[:20]
            
            count = 0
            for post in posts:
                try:
                    title = post.get_text(strip=True)
                    if len(title) < 20 or len(title) > 300:
                        continue
                    
                    thread_url = post.get('href', '')
                    if not thread_url.startswith('http'):
                        thread_url = 'https://old.reddit.com' + thread_url
                    
                    slug = slugify(title)
                    archive = f"https://archive.is/{thread_url}"
                    
                    # Scoring
                    score = random.randint(70, 85)
                    keywords = ['lizard', 'nwo', 'chemtrail', 'flat', '5g', 'illuminati', 
                                'deep state', 'psyop', 'false flag', 'adrenochrome']
                    title_lower = title.lower()
                    for kw in keywords:
                        if kw in title_lower:
                            score += random.randint(3, 7)
                    score = min(score, 99)
                    
                    rating = "FULL SCHIZO" if score > 88 else "Tin Foil Approved" if score > 78 else "Plausible"
                    
                    c.execute("""INSERT OR IGNORE INTO theories 
                                (title,text,url,archive_url,source,score,rating,slug,added)
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                              (title, "Click to view full discussion thread", thread_url, 
                               archive, source, score, rating, slug, datetime.now().isoformat()))
                    count += 1
                    
                except Exception as e:
                    app.logger.error(f"Post error: {e}")
                    continue
            
            app.logger.info(f"Scraped {count} theories from {source}")
            
        except Exception as e:
            app.logger.error(f"Harvest error {source}: {e}")

    conn.commit()
    conn.close()

def get_theories():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories ORDER BY score DESC, added DESC LIMIT 100")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    try:
        init_db()
        
        # Check if we need to harvest
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM theories")
        count = c.fetchone()[0]
        conn.close()
        
        if count < 5 and SCRAPING_ENABLED:
            app.logger.info("Starting harvest...")
            harvest_worldwide()
        
        theories = get_theories()
        
        status_msg = ""
        if not SCRAPING_ENABLED:
            status_msg = "⚠️ SCRAPING OFFLINE - Check requirements.txt"
        elif len(theories) == 0:
            status_msg = "🔄 HARVESTING IN PROGRESS - Refresh in 30 seconds"
        
        return render_template_string('''
        <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
        <meta http-equiv="refresh" content="30">
        <title>🛸 WORLDWIDE CONSPIRACY ARCHIVE 🛸</title>
        <style>
            body{background:#000;color:#0f0;font-family:'Courier New',monospace;padding:1rem;max-width:1200px;margin:0 auto}
            h1{color:#f00;text-align:center;text-shadow:0 0 10px #f00;font-size:1.5rem;border:3px solid #f00;padding:1rem;margin-bottom:0}
            .status{text-align:center;color:#ff0;margin:1rem 0;font-size:1rem;padding:0.5rem;background:#111}
            .stats{text-align:center;color:#0ff;margin:1rem 0;font-size:1.1rem}
            a{color:#0ff;text-decoration:none;transition:all 0.3s}
            a:hover{color:#f0f;text-shadow:0 0 5px #f0f}
            .folder{background:#111;padding:1.5rem;margin:1rem 0;border:4px solid #f00;border-radius:8px;
                    box-shadow:0 0 20px rgba(255,0,0,0.3)}
            .folder:hover{border-color:#0ff;box-shadow:0 0 30px rgba(0,255,255,0.5)}
            .folder h2{margin:0 0 0.5rem 0;color:#0ff;font-size:1.2rem}
            .meta{color:#999;font-size:0.9rem;margin-top:0.5rem}
            .score{color:#ff0;font-weight:bold}
        </style></head><body>
        <h1>🛸 WORLDWIDE CONSPIRACY ARCHIVE 🛸</h1>
        {% if status_msg %}
        <div class="status">{{status_msg}}</div>
        {% endif %}
        <div class="stats">📂 {{theories|length}} THEORIES ARCHIVED 📂</div>
        {% for t in theories %}
        <div class="folder">
          <h2><a href="/conspiracy/{{t.slug}}">{{t.title}}</a></h2>
          <div class="meta">
            <span class="score">🔥 {{t.score}}/100</span> | 
            {{t.rating}} | Source: {{t.source}}
          </div>
        </div>
        {% endfor %}
        </body></html>
        ''', theories=theories, status_msg=status_msg)
        
    except Exception as e:
        app.logger.error(f"Home route error: {e}", exc_info=True)
        return f'''<html><body style="background:#000;color:#f00;font-family:monospace;padding:2rem">
        <h1>⚠️ SYSTEM ERROR</h1>
        <pre>{str(e)}</pre>
        <p><a href="/health" style="color:#0ff">Check health status</a></p>
        </body></html>''', 500

@app.route("/conspiracy/<slug>")
def conspiracy_page(slug):
    try:
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
        <style>body{background:#000;color:#0f0;font-family:'Courier New',monospace;padding:1rem;max-width:900px;margin:0 auto}
        h1{color:#f00;border:3px solid #f00;padding:1rem;font-size:1.2rem}
        .box{background:#111;padding:1.5rem;margin:2rem 0;border-left:8px solid #0ff}
        a{color:#0ff}a:hover{color:#f0f}
        .meta{color:#ff0;margin:1rem 0;padding:1rem;background:#111;border:2px solid #ff0}
        .links{margin:2rem 0;padding:1rem;background:#111}
        .links a{display:inline-block;margin:0.5rem;padding:0.5rem 1rem;background:#f00;color:#fff;border-radius:5px}
        </style></head><body>
        <h1>{{t.title}}</h1>
        <div class="meta">
            🔥 Score: {{t.score}}/100 | {{t.rating}}<br>
            📡 Source: {{t.source}}
        </div>
        <div class="box"><p>{{t.text}}</p></div>
        <div class="links">
            <a href="{{t.url}}" target="_blank">View Thread</a>
            <a href="/">← Back</a>
        </div>
        </body></html>
        ''', t=t)
        
    except Exception as e:
        app.logger.error(f"Conspiracy page error: {e}")
        return str(e), 500

@app.route("/health")
def health():
    status = {
        "scraping": SCRAPING_ENABLED,
        "database": os.path.exists(DB)
    }
    return status, 200

@app.route("/force-harvest")
def force_harvest():
    try:
        harvest_worldwide()
        return "Harvest complete! <a href='/'>View theories</a>"
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
