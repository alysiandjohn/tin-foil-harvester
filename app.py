# app.py — FIXED WORLDWIDE CONSPIRACY ARCHIVE
from flask import Flask, render_template_string, abort
import sqlite3, os, random, re, time
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
DB = 'theories.db'
scraper = cloudscraper.create_scraper()

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
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Only delete if we have old data (optional - removes this to accumulate)
    c.execute("SELECT COUNT(*) FROM theories")
    count = c.fetchone()[0]
    if count > 100:  # Keep fresh but don't delete every time
        c.execute("DELETE FROM theories WHERE added < datetime('now', '-1 day')")

    sources = [
        ("https://www.reddit.com/r/conspiracy/top/?t=day", "Reddit", "reddit"),
        ("https://www.abovetopsecret.com/forum/latest.php", "AboveTopSecret", "ats"),
    ]

    for url, source, site_type in sources:
        try:
            time.sleep(3)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = scraper.get(url, timeout=30, headers=headers)
            
            if r.status_code != 200: 
                print(f"Failed {source}: {r.status_code}")
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')

            if site_type == "reddit":
                # Reddit scraping
                posts = soup.find_all('div', {'data-testid': 'post-container'}) or \
                        soup.find_all('a', href=re.compile(r'/r/conspiracy/comments'))[:20]
                
                for post in posts[:15]:
                    try:
                        # Try multiple selectors for Reddit's changing layout
                        title_elem = post.find('h3') or post.find('a', href=re.compile(r'/comments'))
                        if not title_elem: continue
                        
                        title = title_elem.get_text(strip=True)
                        if len(title) < 20 or len(title) > 300: continue
                        
                        # Get actual post URL
                        link = post.find('a', href=re.compile(r'/comments')) or title_elem
                        thread_url = link.get('href', '')
                        if thread_url.startswith('/'):
                            thread_url = 'https://www.reddit.com' + thread_url
                        
                        insert_theory(c, title, thread_url, source)
                    except Exception as e:
                        print(f"Reddit post error: {e}")
                        continue
            
            elif site_type == "ats":
                # AboveTopSecret scraping
                topics = soup.find_all('a', href=re.compile(r'/forum/thread'))[:15]
                
                for topic in topics:
                    try:
                        title = topic.get_text(strip=True)
                        if len(title) < 20: continue
                        
                        thread_url = topic.get('href', '')
                        if thread_url.startswith('/'):
                            thread_url = 'https://www.abovetopsecret.com' + thread_url
                        
                        insert_theory(c, title, thread_url, source)
                    except Exception as e:
                        print(f"ATS post error: {e}")
                        continue
                        
        except Exception as e:
            print(f"Harvest error {source}: {e}")

    conn.commit()
    conn.close()

def insert_theory(cursor, title, thread_url, source):
    """Helper to insert theory into database"""
    if not thread_url or not thread_url.startswith('http'):
        return
        
    archive = f"https://archive.is/{thread_url}"
    slug = slugify(title)
    
    # Better scoring based on keywords
    keywords = ['lizard', 'nwo', 'chemtrail', 'flat earth', '5g', 'portal', 
                'drone', 'moon', 'swift', 'antichrist', 'reset', 'adrenochrome',
                'illuminati', 'deep state', 'psyop', 'false flag']
    
    score = 70
    title_lower = title.lower()
    for keyword in keywords:
        if keyword in title_lower:
            score += random.randint(3, 8)
    score = min(score, 99)
    
    rating = "FULL SCHIZO" if score > 88 else "Tin Foil Approved" if score > 78 else "Plausible"
    
    try:
        cursor.execute("""INSERT OR IGNORE INTO theories 
                        (title,text,url,archive_url,source,score,rating,slug,added)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                      (title, "Click to view full thread", thread_url, archive, 
                       source, score, rating, slug, datetime.now().isoformat()))
    except Exception as e:
        print(f"Insert error: {e}")

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
    # Only harvest if database is empty or old
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM theories WHERE added > datetime('now', '-1 hour')")
    recent_count = c.fetchone()[0]
    conn.close()
    
    if recent_count < 5:
        harvest_worldwide()
    
    theories = get_theories()
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>🛸 WORLDWIDE CONSPIRACY ARCHIVE 🛸</title>
    <style>
        body{background:#000;color:#0f0;font-family:'Courier New',monospace;padding:2rem;max-width:1200px;margin:0 auto}
        h1{color:#f00;text-align:center;text-shadow:0 0 10px #f00;font-size:2rem;border:3px solid #f00;padding:1rem}
        .stats{text-align:center;color:#ff0;margin:1rem 0;font-size:1.2rem}
        a{color:#0ff;text-decoration:none;transition:all 0.3s}
        a:hover{color:#f0f;text-shadow:0 0 5px #f0f}
        .folder{background:#111;padding:1.5rem;margin:1rem 0;border:4px solid #f00;border-radius:8px;
                box-shadow:0 0 20px rgba(255,0,0,0.3);transition:all 0.3s}
        .folder:hover{border-color:#0ff;box-shadow:0 0 30px rgba(0,255,255,0.5)}
        .folder h2{margin:0 0 0.5rem 0;color:#0ff;font-size:1.3rem}
        .meta{color:#999;font-size:0.9rem;margin-top:0.5rem}
        .score{color:#ff0;font-weight:bold}
        .rating{color:#f0f;font-weight:bold;text-transform:uppercase}
    </style></head><body>
    <h1>🛸 WORLDWIDE CONSPIRACY ARCHIVE 🛸</h1>
    <div class="stats">📂 {{theories|length}} THEORIES ARCHIVED 📂</div>
    {% if theories|length == 0 %}
    <div class="folder"><h2>No theories found yet...</h2><p>Harvesting in progress. Refresh in a moment.</p></div>
    {% endif %}
    {% for t in theories %}
    <div class="folder">
      <h2><a href="/conspiracy/{{t.slug}}">{{t.title}}</a></h2>
      <div class="meta">
        <span class="score">🔥 {{t.score}}/100</span> | 
        <span class="rating">{{t.rating}}</span> | 
        Source: {{t.source}}
      </div>
    </div>
    {% endfor %}
    </body></html>
    ''', theories=theories)

@app.route("/conspiracy/<slug>")
def conspiracy_page(slug):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE slug=?", (slug,))
    t = c.fetchone()
    conn.close()
    if not t: abort(404)
    t = dict(t)
    return render_template_string('''
    <!DOCTYPE html><html><head><title>{{t.title}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#000;color:#0f0;font-family:'Courier New',monospace;padding:2rem;max-width:900px;margin:0 auto}
    h1{color:#f00;border:3px solid #f00;padding:1rem;text-shadow:0 0 10px #f00}
    .box{background:#111;padding:2rem;margin:2rem 0;border-left:8px solid #0ff;box-shadow:0 0 20px rgba(0,255,255,0.3)}
    a{color:#0ff;text-decoration:none}a:hover{color:#f0f}
    .meta{color:#ff0;font-size:1.1rem;margin:1rem 0;padding:1rem;background:#111;border:2px solid #ff0}
    .links{margin:2rem 0;padding:1rem;background:#111;border:2px solid #f00}
    .links a{display:inline-block;margin:0.5rem 1rem 0.5rem 0;padding:0.5rem 1rem;background:#f00;color:#fff;border-radius:5px}
    .links a:hover{background:#0ff;color:#000}</style></head><body>
    <h1>{{t.title}}</h1>
    <div class="meta">
        🔥 Conspiracy Score: <strong>{{t.score}}/100</strong><br>
        📊 Rating: <strong>{{t.rating}}</strong><br>
        📡 Source: <strong>{{t.source}}</strong><br>
        📅 Archived: {{t.added[:10]}}
    </div>
    <div class="box">
        <h2>🎯 INVESTIGATION LINKS:</h2>
        <p>{{t.text}}</p>
    </div>
    <div class="links">
        <a href="{{t.url}}" target="_blank">🔗 View Original Thread</a>
        <a href="{{t.archive_url}}" target="_blank">📦 Permanent Archive</a>
        <a href="/">← Back to Archive</a>
    </div>
    </body></html>
    ''', t=t)

@app.route("/refresh")
def refresh():
    harvest_worldwide()
    return "Harvest complete! <a href='/'>View theories</a>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
