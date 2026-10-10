"""Bincom election-results test solution using only Python's standard library."""
import html
import json
import os
import sqlite3
import shutil
from datetime import datetime
from urllib.parse import parse_qs, quote
from wsgiref.simple_server import make_server

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "election.db"))
if not os.path.exists(DATABASE):
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)), exist_ok=True)
    shutil.copy2(os.path.join(BASE_DIR, "election.db"), DATABASE)


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def fmt(value):
    return f"{int(value or 0):,}"


def page(title, content, messages=""):
    nav = '''<header class="site-header"><a class="brand" href="/"><span class="brand-mark">B</span><span>Bincom<span class="brand-light">Results</span></span></a><nav aria-label="Main navigation"><a href="/polling-unit">Polling unit</a><a href="/lga-results">LGA totals</a><a class="nav-cta" href="/add-polling-unit">Add results <span>＋</span></a></nav></header>'''
    footer = f'''<footer class="footer"><span>Election Results Demo</span><span>Sample dataset · Delta State, Nigeria</span><span>© {datetime.now().year}</span></footer>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Polling-unit election results and LGA vote totals."><title>{esc(title)} · Bincom Results</title><link rel="stylesheet" href="/static/style.css"></head><body>{nav}<main class="container">{messages}{content}</main>{footer}<script src="/static/app.js" defer></script></body></html>'''


def message(text, kind="info"):
    if not text:
        return ""
    return f'<section class="flash-list" aria-live="polite"><div class="flash flash-{esc(kind)}">{esc(text)}</div></section>'


def lga_options(conn, selected=None):
    rows = conn.execute("SELECT uniqueid, lga_name FROM lga WHERE state_id=25 ORDER BY lga_name").fetchall()
    return '<option value="">Choose an LGA…</option>' + ''.join(
        f'<option value="{r["uniqueid"]}"{" selected" if str(selected)==str(r["uniqueid"]) else ""}>{esc(r["lga_name"])}</option>' for r in rows)


def unit_options(conn, selected=None):
    rows = conn.execute("""SELECT pu.uniqueid, pu.polling_unit_name, pu.polling_unit_number, l.lga_name
        FROM polling_unit pu LEFT JOIN lga l ON l.uniqueid=pu.lga_id
        ORDER BY l.lga_name, pu.polling_unit_name, pu.uniqueid""").fetchall()
    out = '<option value="">Choose a polling unit…</option>'
    for r in rows:
        name = r["polling_unit_name"] or r["polling_unit_number"] or f'Polling unit {r["uniqueid"]}'
        label = f'{name} · {r["lga_name"] or "LGA not listed"} · ID {r["uniqueid"]}'
        out += f'<option value="{r["uniqueid"]}"{" selected" if str(selected)==str(r["uniqueid"]) else ""}>{esc(label)}</option>'
    return out


def table_rows(rows, total, with_rank=False):
    if not rows:
        return '<div class="empty-state">No party result records were found for this selection.</div>'
    out = []
    for index, row in enumerate(rows, 1):
        votes = int(row["votes"] or 0)
        share = votes / total * 100 if total else 0
        rank = f'<td><span class="rank">{index:02d}</span></td>' if with_rank else ''
        out.append(f'''<tr>{rank}<td><span class="party-dot">{esc(row['party_abbreviation'][:1])}</span><strong>{esc(row['party_abbreviation'])}</strong></td><td class="numeric vote-number">{fmt(votes)}</td><td><div class="share-cell"><div class="share-track"><span style="width:{share:.1f}%"></span></div><small>{share:.1f}%</small></div></td></tr>''')
    return '<div class="table-wrap"><table><thead><tr>' + ('<th>Rank</th>' if with_rank else '') + '<th>Political party</th><th class="numeric">Votes</th><th>Share of recorded votes</th></tr></thead><tbody>' + ''.join(out) + '</tbody></table></div>'


def dashboard():
    conn = db()
    units = conn.execute("SELECT COUNT(*) FROM polling_unit").fetchone()[0]
    lgas = conn.execute("SELECT COUNT(*) FROM lga WHERE state_id=25").fetchone()[0]
    records = conn.execute("SELECT COUNT(*) FROM announced_pu_results").fetchone()[0]
    conn.close()
    content = f'''<section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="pulse"></span> ELECTION DATA WORKSPACE</div><h1>Election results,<br><span>made clearer.</span></h1><p>Explore polling-unit scores, calculate LGA-wide totals from the underlying records, and enter new results in one simple workspace.</p><div class="hero-actions"><a class="button button-primary" href="/polling-unit">Explore results <span>→</span></a><a class="button button-quiet" href="/add-polling-unit">Enter new results</a></div></div><div class="hero-art" aria-hidden="true"><div class="art-ring ring-one"></div><div class="art-ring ring-two"></div><div class="art-card"><div class="art-card-top"><span>RESULTS OVERVIEW</span><span class="live-dot"></span></div><div class="art-big-number">2011</div><div class="art-label">Delta State sample data</div><div class="art-bars"><i style="height:82%"></i><i style="height:55%"></i><i style="height:70%"></i><i style="height:38%"></i><i style="height:63%"></i><i style="height:46%"></i><i style="height:91%"></i><i style="height:58%"></i></div><div class="art-legend"><span><b></b>Polling-unit records</span><span>Sample dataset</span></div></div><div class="floating-chip"><span class="chip-icon">↗</span><span><strong>Live calculations</strong><small>Totals from polling units</small></span></div></div></section>
    <section class="stats-grid"><article class="stat-card"><div class="stat-icon icon-blue">▦</div><div class="stat-label">Polling units</div><div class="stat-number">{fmt(units)}</div><div class="stat-note">Available in the sample database</div></article><article class="stat-card"><div class="stat-icon icon-violet">⌖</div><div class="stat-label">Local governments</div><div class="stat-number">{fmt(lgas)}</div><div class="stat-note">Delta State · State ID 25</div></article><article class="stat-card"><div class="stat-icon icon-green">☷</div><div class="stat-label">Party score records</div><div class="stat-number">{fmt(records)}</div><div class="stat-note">Individual party results recorded</div></article></section>
    <section class="section-heading"><div><div class="eyebrow">GET STARTED</div><h2>What would you like to do?</h2></div><p>Choose a task to get started with the sample election data.</p></section><section class="feature-grid"><a class="feature-card" href="/polling-unit"><div class="feature-icon blue">01</div><div class="feature-arrow">↗</div><h3>View a polling unit</h3><p>Choose an individual polling unit and inspect its party-by-party vote counts.</p><span class="text-link">View polling-unit results <b>→</b></span></a><a class="feature-card" href="/lga-results"><div class="feature-icon purple">02</div><div class="feature-arrow">↗</div><h3>Calculate LGA totals</h3><p>Sum recorded polling-unit votes by party for any available Local Government Area.</p><span class="text-link">Calculate totals <b>→</b></span></a><a class="feature-card" href="/add-polling-unit"><div class="feature-icon green">03</div><div class="feature-arrow">↗</div><h3>Add a polling unit</h3><p>Enter a new unit and save a score for every party in the sample database.</p><span class="text-link">Enter new results <b>→</b></span></a></section><div class="notice"><span class="notice-mark">i</span><p><strong>About this demo</strong><br>This application uses the supplied sample database. LGA totals are calculated from individual polling-unit results; the announced LGA results table is not used for those calculations.</p></div>'''
    return page("Dashboard", content)


def polling_unit_page(params):
    selected = (params.get("unit_id") or [""])[0]
    try: selected_id = int(selected) if selected else None
    except ValueError: selected_id = None
    conn = db()
    options = unit_options(conn, selected_id)
    content = f'''<div class="page-intro"><div class="eyebrow">RESULT EXPLORER / 01</div><h1>Polling unit <span>results</span></h1><p>Choose a polling unit to view the recorded vote count for each political party.</p></div><section class="panel selector-panel"><form method="get" class="selector-form"><label for="unit_id">Select polling unit</label><div class="selector-row"><select id="unit_id" name="unit_id" required>{options}</select><button class="button button-primary" type="submit">View results <span>→</span></button></div><small>Choose from the polling units available in the supplied dataset.</small></form></section>'''
    if selected_id:
        unit = conn.execute("""SELECT pu.*, l.lga_name, w.ward_name FROM polling_unit pu LEFT JOIN lga l ON l.uniqueid=pu.lga_id LEFT JOIN ward w ON w.uniqueid=pu.uniquewardid WHERE pu.uniqueid=?""", (selected_id,)).fetchone()
        if unit:
            rows = conn.execute("SELECT party_abbreviation, SUM(party_score) AS votes FROM announced_pu_results WHERE CAST(polling_unit_uniqueid AS INTEGER)=? GROUP BY party_abbreviation ORDER BY party_abbreviation", (selected_id,)).fetchall()
            total = sum(int(r["votes"] or 0) for r in rows)
            content += f'''<section class="results-heading"><div><div class="eyebrow">POLLING UNIT ID {unit['uniqueid']}</div><h2>{esc(unit['polling_unit_name'] or 'Unnamed polling unit')}</h2><p>{esc(unit['polling_unit_number'] or 'No unit code')} <span class="dot-sep">·</span> {esc(unit['ward_name'] or 'Ward not listed')} <span class="dot-sep">·</span> {esc(unit['lga_name'] or 'LGA not listed')}</p></div><div class="total-pill"><span>Total recorded votes</span><strong>{fmt(total)}</strong></div></section><section class="panel table-panel"><div class="table-top"><div><h3>Party results</h3><p>Votes recorded for this polling unit</p></div><span class="table-count">{len(rows)} parties with records</span></div>{table_rows(rows,total)}<div class="table-foot"><span>Source: announced polling-unit records</span><span>Calculated from stored party scores</span></div></section>'''
        else:
            content = message("Please select a valid polling unit.", "error") + content
    else:
        content += '<section class="empty-panel"><div class="empty-illustration">⌕</div><h2>Your results will appear here</h2><p>Select a polling unit above to see its recorded party scores and total votes.</p></section>'
    conn.close()
    return page("Polling Unit Results", content)


def lga_page(params):
    selected = (params.get("lga_id") or [""])[0]
    try: selected_id = int(selected) if selected else None
    except ValueError: selected_id = None
    conn = db()
    options = lga_options(conn, selected_id)
    content = f'''<div class="page-intro"><div class="eyebrow">RESULT EXPLORER / 02</div><h1>Local government <span>totals</span></h1><p>Calculate party totals by adding the recorded results from all polling units within an LGA.</p></div><section class="panel selector-panel"><form method="get" class="selector-form"><label for="lga_id">Select Local Government Area</label><div class="selector-row"><select id="lga_id" name="lga_id" required>{options}</select><button class="button button-primary" type="submit">Calculate totals <span>→</span></button></div><small>Only LGAs included in the supplied Delta State dataset are listed.</small></form></section>'''
    if selected_id:
        lga = conn.execute("SELECT uniqueid,lga_name FROM lga WHERE uniqueid=? AND state_id=25", (selected_id,)).fetchone()
        if lga:
            units = conn.execute("SELECT COUNT(*) FROM polling_unit WHERE lga_id=?", (selected_id,)).fetchone()[0]
            # Question 2: aggregate the polling-unit rows; announced_lga_results is deliberately not queried.
            rows = conn.execute("""SELECT apr.party_abbreviation, SUM(apr.party_score) AS votes FROM announced_pu_results apr JOIN polling_unit pu ON pu.uniqueid=CAST(apr.polling_unit_uniqueid AS INTEGER) WHERE pu.lga_id=? GROUP BY apr.party_abbreviation ORDER BY votes DESC, apr.party_abbreviation""", (selected_id,)).fetchall()
            total = sum(int(r["votes"] or 0) for r in rows)
            content += f'''<section class="results-heading"><div><div class="eyebrow">LGA SUMMARY</div><h2>{esc(lga['lga_name'])}</h2><p>Aggregated from individual polling-unit records</p></div><div class="total-pill"><span>Total recorded votes</span><strong>{fmt(total)}</strong></div></section><section class="summary-strip"><div><span>Polling units in this LGA</span><strong>{fmt(units)}</strong></div><div><span>Parties with recorded votes</span><strong>{len(rows)}</strong></div><div><span>Calculation source</span><strong>Polling-unit records</strong></div></section><section class="panel table-panel"><div class="table-top"><div><h3>Aggregated party results</h3><p>Highest recorded vote totals first</p></div><span class="table-count">Calculated total</span></div>{table_rows(rows,total,True)}<div class="table-foot"><span>Source: announced_pu_results joined to polling_unit</span><span>announced_lga_results is not used</span></div></section>'''
        else:
            content = message("Please select a valid Local Government Area.", "error") + content
    else:
        content += '<section class="empty-panel"><div class="empty-illustration">∑</div><h2>Your LGA summary will appear here</h2><p>Choose an LGA to calculate the total votes for each party.</p></section>'
    conn.close()
    return page("LGA Totals", content)


def add_unit_page(environ, form=None, notice="", notice_kind="info"):
    form = form or {}
    conn = db()
    lgas = conn.execute("SELECT uniqueid,lga_name FROM lga WHERE state_id=25 ORDER BY lga_name").fetchall()
    parties = [r[0] for r in conn.execute("SELECT DISTINCT party_abbreviation FROM announced_pu_results ORDER BY party_abbreviation").fetchall()]
    if not parties: parties = ["PDP","DPP","ACN","PPA","CDC","JP","ANPP","LABO","CPP"]
    selected_lga = form.get("lga_id", "")
    ward_rows = conn.execute("SELECT uniqueid,ward_name FROM ward WHERE lga_id=? ORDER BY ward_name", (int(selected_lga),)).fetchall() if str(selected_lga).isdigit() else []
    lga_html = '<option value="">Select an LGA</option>' + ''.join(f'<option value="{r["uniqueid"]}"{" selected" if str(selected_lga)==str(r["uniqueid"]) else ""}>{esc(r["lga_name"])}</option>' for r in lgas)
    ward_html = '<option value="">Choose a ward</option>' + ''.join(f'<option value="{r["uniqueid"]}"{" selected" if str(form.get("ward_id",""))==str(r["uniqueid"]) else ""}>{esc(r["ward_name"])}</option>' for r in ward_rows)
    scores_html = ''.join(f'<div class="field score-field"><label for="score_{esc(p)}"><span class="party-dot">{esc(p[:1])}</span>{esc(p)}</label><input id="score_{esc(p)}" name="score_{esc(p)}" type="number" min="0" step="1" inputmode="numeric" placeholder="0" value="{esc(form.get("score_"+p,"0"))}" required></div>' for p in parties)
    content = f'''<div class="page-intro"><div class="eyebrow">RESULT ENTRY / 03</div><h1>Add polling unit <span>results</span></h1><p>Enter the unit details and the recorded score for every party. All vote counts must be zero or a positive whole number.</p></div><form method="post" class="entry-layout" id="entry-form"><section class="panel form-panel"><div class="form-section-title"><span class="section-number">01</span><div><h2>Polling unit information</h2><p>Identify where this polling unit belongs.</p></div></div><div class="field-grid"><div class="field field-full"><label for="polling_unit_name">Polling unit name <span class="required">*</span></label><input id="polling_unit_name" name="polling_unit_name" type="text" maxlength="100" placeholder="e.g. Central Primary School" value="{esc(form.get('polling_unit_name',''))}" required></div><div class="field"><label for="polling_unit_number">Polling unit code/number <span class="required">*</span></label><input id="polling_unit_number" name="polling_unit_number" type="text" maxlength="50" placeholder="e.g. DT2501001" value="{esc(form.get('polling_unit_number',''))}" required></div><div class="field"><label for="lga_id">Local Government Area <span class="required">*</span></label><select id="lga_id" name="lga_id" required>{lga_html}</select></div><div class="field"><label for="ward_id">Ward <span class="required">*</span></label><select id="ward_id" name="ward_id" required {'disabled' if not selected_lga else ''}>{ward_html if selected_lga else '<option value="">Choose an LGA first</option>'}</select><small class="field-hint">Ward options update when you choose an LGA.</small></div><div class="field field-full"><label for="polling_unit_description">Description <span class="optional">Optional</span></label><textarea id="polling_unit_description" name="polling_unit_description" rows="3" placeholder="Add a location description if useful">{esc(form.get('polling_unit_description',''))}</textarea></div></div></section><section class="panel form-panel"><div class="form-section-title"><span class="section-number">02</span><div><h2>Party vote counts</h2><p>Enter a score for every party. Leave a field blank if the party received zero votes.</p></div></div><div class="score-grid">{scores_html}</div><div class="form-actions"><a class="button button-quiet" href="/">Cancel</a><button class="button button-primary" type="submit">Save polling unit <span>→</span></button></div></section></form>'''
    conn.close()
    return page("Add Polling Unit", content, message(notice, notice_kind))


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))
    form = {}
    if method == "POST":
        try: length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError: length = 0
        raw = environ["wsgi.input"].read(length).decode("utf-8", "replace")
        form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

    status = "200 OK"
    headers = [("Content-Type", "text/html; charset=utf-8")]
    if path.startswith("/static/"):
        filename = os.path.basename(path)
        if filename not in {"style.css", "app.js"}:
            status = "404 Not Found"; body = b"Not found"
        else:
            full_path = os.path.join(BASE_DIR, "static", filename)
            with open(full_path, "rb") as f: body = f.read()
            headers = [("Content-Type", "text/css; charset=utf-8" if filename.endswith(".css") else "application/javascript; charset=utf-8")]
        start_response(status, headers); return [body]
    if path.startswith("/api/wards/"):
        try: lga_id = int(path.rsplit("/", 1)[-1])
        except ValueError: lga_id = -1
        conn = db(); rows = conn.execute("SELECT uniqueid,ward_name FROM ward WHERE lga_id=? ORDER BY ward_name", (lga_id,)).fetchall(); conn.close()
        body = json.dumps([{"id": r["uniqueid"], "name": r["ward_name"]} for r in rows]).encode()
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8")]); return [body]
    if path == "/" and method == "GET": body = dashboard()
    elif path == "/polling-unit" and method in ("GET", "POST"): body = polling_unit_page(query if method == "GET" else form)
    elif path == "/lga-results" and method in ("GET", "POST"): body = lga_page(query if method == "GET" else form)
    elif path == "/add-polling-unit" and method == "GET": body = add_unit_page(environ)
    elif path == "/add-polling-unit" and method == "POST":
        conn = db(); errors = []
        name = form.get("polling_unit_name", "").strip(); number = form.get("polling_unit_number", "").strip(); desc = form.get("polling_unit_description", "").strip()
        try: lga_id = int(form.get("lga_id", ""))
        except ValueError: lga_id = None
        try: ward_id = int(form.get("ward_id", ""))
        except ValueError: ward_id = None
        lga = conn.execute("SELECT uniqueid FROM lga WHERE uniqueid=? AND state_id=25", (lga_id,)).fetchone() if lga_id else None
        ward = conn.execute("SELECT uniqueid,ward_id,lga_id FROM ward WHERE uniqueid=?", (ward_id,)).fetchone() if ward_id else None
        if not name: errors.append("Polling unit name is required.")
        if not number: errors.append("Polling unit code/number is required.")
        if not lga: errors.append("Select a valid LGA.")
        if not ward or (lga and ward["lga_id"] != lga["uniqueid"]): errors.append("Select a ward belonging to the chosen LGA.")
        parties = [r[0] for r in conn.execute("SELECT DISTINCT party_abbreviation FROM announced_pu_results ORDER BY party_abbreviation").fetchall()]
        if not parties: parties = ["PDP","DPP","ACN","PPA","CDC","JP","ANPP","LABO","CPP"]
        scores = {}
        for party in parties:
            raw = form.get("score_" + party, "0").strip()
            try:
                score = int(raw or "0")
                if score < 0: raise ValueError
                scores[party] = score
            except ValueError: errors.append(f"Enter a whole number of zero or more for {party}.")
        if errors:
            conn.close(); body = add_unit_page(environ, form, " ".join(errors), "error")
        else:
            try:
                next_id = conn.execute("SELECT COALESCE(MAX(polling_unit_id),0)+1 FROM polling_unit").fetchone()[0]
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor = conn.execute("""INSERT INTO polling_unit (polling_unit_id,ward_id,lga_id,uniquewardid,polling_unit_number,polling_unit_name,polling_unit_description,entered_by_user,date_entered,user_ip_address) VALUES (?,?,?,?,?,?,?,?,?,?)""", (next_id,ward["ward_id"],lga_id,ward["uniqueid"],number,name,desc or None,"Test user",now,environ.get("REMOTE_ADDR","unknown")))
                new_id = cursor.lastrowid
                for party, score in scores.items():
                    conn.execute("INSERT INTO announced_pu_results (polling_unit_uniqueid,party_abbreviation,party_score,entered_by_user,date_entered,user_ip_address) VALUES (?,?,?,?,?,?)", (str(new_id),party,score,"Test user",now,environ.get("REMOTE_ADDR","unknown")))
                conn.commit(); conn.close()
                status = "303 See Other"; headers.append(("Location", f"/polling-unit?unit_id={new_id}")); body = "Saved"
            except sqlite3.Error:
                conn.rollback(); conn.close(); body = add_unit_page(environ, form, "The polling unit could not be saved. Please try again.", "error")
    else:
        status = "404 Not Found"; body = page("Page Not Found", '<section class="empty-panel"><div class="empty-illustration">!</div><h1>Page not found</h1><p>That page could not be found.</p><a class="button button-primary" href="/">Back to dashboard</a></section>')
    if isinstance(body, str): body = body.encode("utf-8")
    start_response(status, headers)
    return [body]


if __name__ == "__main__":
    from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
    port = int(os.environ.get("PORT", "5000"))
    print(f"Bincom Election Results is running at http://127.0.0.1:{port}")
    with make_server("0.0.0.0", port, application) as server:
        server.serve_forever()




