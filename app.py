# app.py – FINAL VERSION (paste over the old one)
from flask import Flask, render_template_string
import sqlite3, os, random
from datetime import datetime

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories
                 (id INTEGER PRIMARY KEY, title TEXT UNIQUE, text TEXT, url TEXT,
                  source TEXT, score REAL, rating TEXT, added TEXT)''')
    conn.commit()
    conn.close()

def rate_craziness(text):
    keywords = ["lizard","nwo","chemtrail","flat earth","5g","eclipse portal","soul trap","hologram","reptil","deep state","antichrist","great reset"]
    hits = sum(word in text.lower() for word in keywords)
    score = hits * 17 + random.randint(0, 30)
    score = min(score, 100)
    ratings = ["mild","speculation","conspiracy","tin foil","full schizo","beyond the veil"]
    return score, ratings[min(hits//2, 5)]

def seed():
    init_db()
    seeds = [
        ("2025 Eclipse Was Actual NWO Portal Opening","Lizards used 5G + HAARP during totality. Shadows don’t lie.","https://x.com","X"),
        ("Birds Are Deep State Drones v3","2025 firmware update adds facial recognition. They’re watching YOU.","https://reddit.com/r/conspiracy","Reddit"),
        ("Antarctica Ice Wall + Nazi Base Still Active","Hitler escaped. They guard the edge AND the dome.","https://archive.org","Wayback"),
        ("AI Grok Is a Reptilian Overlord","xAI = x-tra terrestrial AI. Built to harvest human paranoia.","https://x.com","X"),
        ("Taylor Swift’s 2025 Tour = Mass Satanic Initiation","Eclipse alignment + 33 symbolism everywhere.","https://tiktok.com","TikTok"),
        ("The Moon Is a Soul-Recycling Machine","That’s why they hide the dark side.","https://godlikeproductions.com","Forum")
    ]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for title,text,url,src in seeds:
        score, rating = rate_craziness(title + " " + text)
        c.execute("INSERT OR IGNORE INTO theories (title,text,url,source,score,rating,added) VALUES (?,?,?,?,?,?,?)",
                  (title,text,url,src,score,rating,datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_theories(order="score DESC", limit=50):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"SELECT * FROM theories ORDER BY {order} LIMIT {limit}")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    seed()
    latest = get_theories("added DESC", 6)
    top = get_theories("score DESC", 6)
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TIN FOIL TIMES</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem;margin:0}
    h1,h2{text-align:center;margin:2rem 0;color:#f00}
    .c{background:#111;padding:1.5rem;margin:1rem 0;border-left:6px solid #f00;border-radius:8px}
    a{color:#0ff;text-decoration:none}</style></head><body>
    <h1>🛸 TIN FOIL TIMES 🛸</h1>
    <h2>Freshest Harvest</h2>
    {% for t in latest %}
    <div class="c"><b>{{ t.title }}</b><br>{{ t.source }} • {{ t.score|round(1) }}/100 <b>{{ t.rating }}</b></div>
    {% endfor %}
    <h2>Current Schizo Kings</h2>
    {% for t in top %}
    <div class="c">#{{ loop.index }} <b>{{ t.title }}</b> — {{ t.score|round(1) }}/100 {{ t.rating }}</div>
    {% endfor %}
    <p style="text-align:center"><a href="/hall-of-fame">→ ENTER HALL OF FAME ←</a></p>
    </body></html>
    ''', latest=latest, top=top)

@app.route("/hall-of-fame")
def hall():
    seed()
    all_theories = get_theories("score DESC", 100)
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Hall of Eternal Paranoia</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:2rem;margin:0}
    h1{text-align:center;color:#f00;margin:3rem 0}
    .c{background:#111;padding:1rem;margin:0.8rem 0;border-left:6px solid #f00;border-radius:8px}</style></head><body>
    <h1>🏆 HALL OF ETERNAL PARANOIA 🏆</h1>
    {% for t in all_theories %}
    <div class="c">#{{ loop.index }} <b>{{ t.title }}</b><br>{{ t.source }} • {{ t.score|round(1) }}/100 <b>{{ t.rating }}</b></div>
    {% endfor %}
    <p style="text-align:center"><small>Updated {{ "now"|strftime("%Y-%m-%d %H:%M") }}</small></p>
    </body></html>
    ''', all_theories=all_theories)

if __name__ == "__main__":
    app.run(debug=True)