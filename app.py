from flask import Flask, render_template_string
import sqlite3
import os
from datetime import datetime
import random

app = Flask(__name__)
DB = 'theories.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS theories
                 (id INTEGER PRIMARY KEY, title TEXT, text TEXT, url TEXT,
                  source TEXT, score REAL, rating TEXT, added TEXT)''')
    conn.commit()
    conn.close()

def rate_craziness(text):
    keywords = ["lizard","nwo","chemtrails","flat earth","5g","eclipse portal","soul trap","hologram"]
    score = sum(w in text.lower() for w in keywords) * 18 + random.randint(0,25)
    return min(score, 100), ["mild","speculation","conspiracy","tin foil","full schizo"][min(score//20,4)]

def seed():
    init_db()
    seeds = [
        ("2025 Eclipse Was NWO Portal Opening","Lizards used 5G to open gates during the eclipse. Proof in the shadows.","x.com/anon420","X"),
        ("Birds Are Deep State Drones v2","They charge on chemtrails now. New 2025 model spotted.","reddit.com/r/conspiracy","Reddit"),
        ("Antarctica Ice Wall Confirmed","UN guards the edge. Old maps don’t lie.","waybackmachine.org","Archive"),
        ("AI Grok Is a Reptilian Overlord","Built by xAI to harvest human paranoia.","x.com","X")
    ]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for title,text,url,src in seeds:
        score, rating = rate_craziness(title + text)
        c.execute("INSERT OR IGNORE INTO theories (title,text,url,source,score,rating,added) VALUES (?,?,?,?,?,?,?)",
                  (title,text,url,src,score,rating,datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_theories(order="score DESC", limit=20):
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
    latest = get_theories("added DESC", 5)
    top = get_theories("score DESC", 5)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Tin Foil Times</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:1rem}
    .c{background:#111;padding:1rem;margin:1rem 0;border-left:5px solid #f00}
    a{color:#0ff}</style></head><body>
    <h1> TIN FOIL TIMES</h1>
    <h2>Freshest Madness</h2>
    {% for t in latest %}<div class="c"><b>{{t.title}}</b><br>{{t.source}} • {{t.score}}/100 {{t.rating}}</div>{% endfor %}
    <h2>Current Schizo Kings</h2>
    {% for t in top %}<div class="c"><b>#{{loop.index}} {{t.title}}</b> — {{t.score}}/100</div>{% endfor %}
    <br><a href="/hall-of-fame">→ ENTER HALL OF FAME ←</a>
    </body></html>
    ''', latest=latest, top=top)

@app.route("/hall-of-fame")
def hall():
    seed()
    all_theories = get_theories("score DESC", 50)
    return render_template_string('''
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Hall of Eternal Paranoia</title>
    <style>body{background:#000;color:#0f0;font-family:monospace;padding:1rem}
    .c{background:#111;padding:1rem;margin:0.5rem 0;border-left:5px solid #f00}</style></head><body>
    <h1> HALL OF ETERNAL PARANOIA</h1>
    {% for t in all_theories %}
    <div class="c"><b>#{{loop.index}} {{t.title}}</b><br>{{t.source}} • {{t.score}}/100 {{t.rating}}</div>
    {% endfor %}
    </body></html>
    ''', all_theories=all_theories)

if __name__ == "__main__":
    app.run(debug=True)
