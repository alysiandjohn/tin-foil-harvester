from flask import Flask, render_template_string, request
import sqlite3, os, random, requests
from datetime import datetime
from bs4 import BeautifulSoup
import re, urllib.parse

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE, full_text TEXT, url TEXT,
                  archive_url TEXT, source TEXT, score REAL, rating TEXT, added TEXT)''')
    conn.commit()
    conn.close()

def archive_url(url):
    try:
        # Simple archive.is snapshot (free, no API key)
        archive_req = requests.post('https://archive.is/submit/', data={'url': url}, timeout=10)
        soup = BeautifulSoup(archive_req.text, 'html.parser')
        archive_link = soup.find('a', {'id': 'surl'})['href'] if soup.find('a', {'id': 'surl'}) else None
        return f"https://archive.is{archive_link}" if archive_link else url  # Fallback to original
    except:
        return url  # If archive fails, use original

def rate_craziness(text):
    text_lower = text.lower()
    keywords = ["lizard", "reptil", "nwo", "chemtrail", "flat earth", "hologram", "soul trap", "haarp", "5g mind", "deep state", "antarctica wall", "moon base", "great reset", "adrenochrome", "pizzagate", "qanon", "fema camp", "hollow earth", "mandela effect", "crisis actor", "false flag"]
    hits = sum(word in text_lower for word in keywords)
    exclamation_bonus = len(re.findall(r'[!]{2,}', text)) * 3
    question_bonus = len(re.findall(r'\?{2,}', text)) * 2
    score = min((hits * 8) + exclamation_bonus + question_bonus + random.randint(0, 20), 100)
    ratings = ["mild", "speculation", "conspiracy", "tin foil", "full schizo", "beyond the veil"]
    return score, ratings[min(int(score / 17), 5)]

def scrape_full_post(url, source):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (TinFoilBot/1.0)'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        if source == 'reddit':
            title = soup.find('h1').text.strip() if soup.find('h1') else 'Unknown'
            body = soup.find('div', {'id': 't3_'}).find('div', class_='usertext-body') or soup.find('article')
            full_text = body.get_text(strip=True)[:5000] if body else ''
        elif source == 'x':
            full_text = soup.find('div', {'data-testid': 'tweetText'}) or 'Thread archived.'
            full_text = full_text.get_text(strip=True)[:5000] if full_text else ''
            title = full_text[:100] + '...'
        elif source in ['4chan', 'godlike', 'abovetopsecret']:
            title = soup.find('title').text.strip() if soup.find('title') else 'Thread'
            body = soup.find('div', class_='postbody') or soup.find('div', class_='message-body') or soup.body
            full_text = body.get_text(strip=True)[:5000] if body else ''
        else:
            title = soup.title.string.strip() if soup.title else 'Archived Post'
            full_text = soup.get_text(strip=True)[:5000]
        return title, full_text
    except:
        return 'Harvest Failed', 'Unable to scrape full post.'

def harvest_global():
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    sources = [
        # Reddit
        {'url': 'https://www.reddit.com/r/conspiracy/hot.json?limit=20', 'source': 'reddit', 'type': 'json'},
        {'url': 'https://www.reddit.com/r/HighStrangeness/new.json?limit=10', 'source': 'reddit', 'type': 'json'},
        # X (via simple keyword search proxy – real API later)
        {'url': 'https://api.twitter.com/2/tweets/search/recent?query=conspiracy OR chemtrails OR flat earth&max_results=10', 'source': 'x', 'type': 'api'},  # Note: Needs key for real; mock for now
        # 4chan /pol/ via archived.moe
        {'url': 'https://archived.moe/pol/threads.json?limit=20', 'source': '4chan', 'type': 'json'},
        # GodlikeProductions
        {'url': 'https://www.godlikeproductions.com/search.php?search=conspiracy', 'source': 'godlike', 'type': 'html'},
        # AboveTopSecret
        {'url': 'https://www.abovetopsecret.com/forum42/pg1/srtpages', 'source': 'abovetopsecret', 'type': 'html'},
        # LunaticOutpost (fringe BBS)
        {'url': 'https://www.lunaticoutpost.com/search.php?keywords=conspiracy', 'source': 'lunaticoutpost', 'type': 'html'}
    ]
    for src in sources:
        try:
            if src['type'] == 'json':
                r = requests.get(src['url'], headers={'User-Agent': 'TinFoilBot/1.0'})
                data = r.json()
                for item in data.get('data', {}).get('children', []) or data.get('threads', []):
                    url = item.get('permalink', item.get('url', ''))
                    if url:
                        title, full_text = scrape_full_post(url, src['source'])
                        archive = archive_url(url)
                        score, rating = rate_craziness(full_text)
                        c.execute("INSERT OR IGNORE INTO theories (title, full_text, url, archive_url, source, score, rating, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (title, full_text, url, archive, src['source'], score, rating, datetime.now().isoformat()))
            elif src['type'] == 'html':
                r = requests.get(src['url'], headers={'User-Agent': 'TinFoilBot/1.0'})
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.find_all('a', href=re.compile(r'thread|post|topic'))
                for link in links[:5]:  # Limit to avoid overload
                    url = urllib.parse.urljoin(src['url'], link['href'])
                    title, full_text = scrape_full_post(url, src['source'])
                    archive = archive_url(url)
                    score, rating = rate_craziness(full_text)
                    c.execute("INSERT OR IGNORE INTO theories (title, full_text, url, archive_url, source, score, rating, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                              (title, full_text, url, archive, src['source'], score, rating, datetime.now().isoformat()))
        except Exception as e:
            print(f"Harvest error for {src['source']}: {e}")
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
    harvest_global()
    latest = get_theories("added DESC", 10)
    top = get_theories("score DESC", 10)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tin Foil Times</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:1rem}h1{text-align:center;color:#f00}.c{background:#111;padding:1rem;margin:1rem;border-left:5px solid #f00}a{color:#0ff}</style></head><body>
    <h1>🛸 TIN FOIL TIMES 🛸</h1>
    <h2>Freshest Global Harvest</h2>{% for t in latest %}<div class="c"><a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}
    <h2>Schizo Kings</h2>{% for t in top %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a> — {{t.score|round(1)}}/100</div>{% endfor %}
    <p style="text-align:center"><a href="/hall-of-fame">→ HALL OF FAME ←</a></p>
    </body></html>
    ''', latest=latest, top=top)

@app.route("/hall-of-fame")
def hall():
    harvest_global()
    theories = get_theories("score DESC", 100)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Eternal Paranoia</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:1rem}h1{text-align:center;color:#f00}.c{background:#111;padding:1rem;margin:0.5rem;border-left:5px solid #f00}a{color:#0ff}</style></head><body>
    <h1>🏆 HALL OF ETERNAL PARANOIA 🏆</h1>{% for t in theories %}<div class="c">#{{loop.index}} <a href="/theory/{{t.id}}">{{t.title}}</a><br>{{t.source}} • {{t.score|round(1)}}/100 {{t.rating}}</div>{% endfor %}</body></html>
    ''', theories=theories)

@app.route("/theory/<int:tid>")
def theory_page(tid):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM theories WHERE id = ?", (tid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "Theory not found. <a href='/'>Back</a>", 404
    t = dict(row)
    return render_template