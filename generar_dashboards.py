#!/usr/bin/env python3
"""
generar_dashboards.py
Genera dashboards HTML por célula a partir del CSV de tickets.
Uso: python generar_dashboards.py --csv <ruta_csv> --output <carpeta_salida>
"""
import csv
import json
import os
import sys
import argparse
from collections import defaultdict

# ── Colores ──────────────────────────────────────────────────────────────────

CELULA_COLORS = {
    "Alpha":   "#1B3A6B",
    "Beta":    "#1A6B3A",
    "Gamma":   "#6B1A3A",
    "Delta":   "#6B4A1A",
    "Epsilon": "#3A1A6B",
}
DEFAULT_COLOR = "#1B3A6B"

CLASS_COLORS = {
    "Service Requests":      "#2E86DE",
    "Change Requests":       "#27AE60",
    "Incidents":             "#E74C3C",
    "Recommendations":       "#9B59B6",
    "Monitoring and Events": "#F5A623",
    "Warranty":              "#1ABC9C",
    "Sin clasificar":        "#95A5A6",
}

STATUS_COLORS = {
    "Open":                 "#2E86DE",
    "Waiting On Customer":  "#F5A623",
    "Escalated":            "#E74C3C",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_classification(c):
    c = (c or "").strip()
    return "Sin clasificar" if c in ("", "-") else c

def normalize_overdue(v):
    return str(v).strip().upper() == "TRUE"

def parse_csv(csv_path):
    tickets = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    # Fila 4 = headers, fila 5+ = datos
    for row in rows[5:]:
        if len(row) < 11:
            continue
        if row[0].startswith("Total records"):
            continue
        celula = row[7].strip()
        if not celula:
            continue
        tickets.append({
            "account":        row[0].strip(),
            "created":        row[1].strip(),
            "modified":       row[2].strip(),
            "id":             row[3].strip(),
            "subject":        row[4].strip(),
            "owner":          row[5].strip(),
            "due_date":       row[6].strip(),
            "celula":         celula,
            "classification": normalize_classification(row[8]),
            "status":         row[9].strip(),
            "overdue":        normalize_overdue(row[10]),
        })
    return tickets

def calc_metrics(tickets):
    return {
        "total":    len(tickets),
        "open":     sum(1 for t in tickets if t["status"] == "Open"),
        "waiting":  sum(1 for t in tickets if t["status"] == "Waiting On Customer"),
        "escalated":sum(1 for t in tickets if t["status"] == "Escalated"),
        "overdue":  sum(1 for t in tickets if t["overdue"]),
    }

def group_by(tickets, key):
    result = defaultdict(int)
    for t in tickets:
        result[t[key]] += 1
    return dict(result)

# ── Dashboard por célula ───────────────────────────────────────────────────────

def generate_celula_html(celula, tickets, all_celulas, today):
    color   = CELULA_COLORS.get(celula, DEFAULT_COLOR)
    metrics = calc_metrics(tickets)

    by_class   = group_by(tickets, "classification")
    by_status  = group_by(tickets, "status")
    by_owner   = group_by(tickets, "owner")
    by_account = group_by(tickets, "account")

    class_labels  = list(by_class.keys())
    class_data    = list(by_class.values())
    class_colors  = [CLASS_COLORS.get(l, "#95A5A6") for l in class_labels]

    status_labels = list(by_status.keys())
    status_data   = list(by_status.values())
    status_colors = [STATUS_COLORS.get(l, "#95A5A6") for l in status_labels]

    owner_sorted   = sorted(by_owner.items(),   key=lambda x: x[1], reverse=True)
    account_sorted = sorted(by_account.items(), key=lambda x: x[1], reverse=True)[:10]

    owner_labels   = [o[0] for o in owner_sorted]
    owner_data     = [o[1] for o in owner_sorted]
    account_labels = [a[0][:30] for a in account_sorted]
    account_data   = [a[1] for a in account_sorted]

    table_rows = ""
    for t in tickets:
        od_badge     = '<span style="color:#E74C3C;font-weight:bold;">&#10003;</span>' if t["overdue"] else ""
        status_color = STATUS_COLORS.get(t["status"], "#666")
        due          = t["due_date"] if t["due_date"] and t["due_date"] != "-" else "&#8212;"
        acct         = t["account"][:35] + ("..." if len(t["account"]) > 35 else "")
        subj         = t["subject"][:50] + ("..." if len(t["subject"]) > 50 else "")
        table_rows += f"""
        <tr>
          <td>{t['id']}</td>
          <td title="{t['account']}">{acct}</td>
          <td title="{t['subject']}">{subj}</td>
          <td>{t['owner']}</td>
          <td>{t['classification']}</td>
          <td><span style="background:{status_color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">{t['status']}</span></td>
          <td>{due}</td>
          <td style="text-align:center;">{od_badge}</td>
        </tr>"""

    nav_links = "".join(
        f'<a href="Dashboard_{c}.html" {"style=\"font-weight:900;\"" if c==celula else ""}>{c}</a>'
        for c in all_celulas
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dashboard {celula} &mdash; {today}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:#f0f2f5;color:#333}}
.header{{background:{color};color:#fff;padding:20px 30px;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:24px;font-weight:700}}
.header .sub{{font-size:13px;opacity:.85;margin-top:4px}}
.nav{{background:#fff;padding:10px 30px;border-bottom:1px solid #ddd;display:flex;gap:10px;flex-wrap:wrap}}
.nav a{{text-decoration:none;color:{color};font-size:13px;font-weight:600;padding:4px 12px;border:1px solid {color};border-radius:20px}}
.nav a:hover{{background:{color};color:#fff}}
.container{{padding:24px 30px;max-width:1400px;margin:0 auto}}
.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px}}
.kpi{{background:#fff;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.07);border-top:4px solid {color}}}
.kpi .value{{font-size:36px;font-weight:800;color:{color}}}
.kpi .label{{font-size:12px;color:#777;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}}
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.card{{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.07)}}
.card h3{{font-size:14px;font-weight:700;color:#444;margin-bottom:16px;text-transform:uppercase;letter-spacing:.5px}}
.chart-container{{position:relative;height:260px}}
.search-bar{{width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px;outline:none}}
.search-bar:focus{{border-color:{color};box-shadow:0 0 0 3px {color}22}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:{color};color:#fff;padding:10px 12px;text-align:left;font-weight:600}}
td{{padding:9px 12px;border-bottom:1px solid #f0f0f0;vertical-align:middle}}
tr:hover td{{background:#f7f9ff}}
.footer{{text-align:center;padding:20px;color:#aaa;font-size:12px}}
</style>
</head>
<body>
<div class="header">
  <div><h1>&#128202; Dashboard &mdash; C&eacute;lula {celula}</h1>
  <div class="sub">Reporte semanal &middot; Generado: {today} &middot; Solusoft</div></div>
  <div style="font-size:13px;opacity:.85">Dpto: Soluciones y Servicios Tecnol&oacute;gicos</div>
</div>
<div class="nav">
  <a href="../Dashboard_Estrategico.html">&#127968; Estrat&eacute;gico</a>
  {nav_links}
</div>
<div class="container">
  <div class="kpi-row">
    <div class="kpi"><div class="value">{metrics['total']}</div><div class="label">Total Tickets</div></div>
    <div class="kpi"><div class="value" style="color:#2E86DE">{metrics['open']}</div><div class="label">Abiertos</div></div>
    <div class="kpi"><div class="value" style="color:#F5A623">{metrics['waiting']}</div><div class="label">Esp. Cliente</div></div>
    <div class="kpi"><div class="value" style="color:#E74C3C">{metrics['escalated']}</div><div class="label">Escalados</div></div>
    <div class="kpi"><div class="value" style="color:#E74C3C">{metrics['overdue']}</div><div class="label">Vencidos</div></div>
  </div>
  <div class="charts-row">
    <div class="card"><h3>Por Clasificaci&oacute;n</h3><div class="chart-container"><canvas id="cC"></canvas></div></div>
    <div class="card"><h3>Por Estado</h3><div class="chart-container"><canvas id="sC"></canvas></div></div>
  </div>
  <div class="charts-row">
    <div class="card"><h3>Tickets por Agente</h3><div class="chart-container"><canvas id="oC"></canvas></div></div>
    <div class="card"><h3>Tickets por Cliente (Top {min(10,len(account_sorted))})</h3><div class="chart-container"><canvas id="aC"></canvas></div></div>
  </div>
  <div class="card">
    <h3>Todos los Tickets</h3>
    <input type="text" class="search-bar" id="q" placeholder="&#128269; Buscar..." onkeyup="filterTable()">
    <div style="overflow-x:auto"><table id="T">
      <thead><tr><th>ID</th><th>Cliente</th><th>Asunto</th><th>Agente</th><th>Tipo</th><th>Estado</th><th>Vence</th><th>OD</th></tr></thead>
      <tbody id="TB">{table_rows}</tbody>
    </table></div>
  </div>
</div>
<div class="footer">Solusoft &middot; C&eacute;lula {celula} &middot; {today}</div>
<script>
new Chart(document.getElementById('cC'),{{type:'doughnut',data:{{labels:{json.dumps(class_labels)},datasets:[{{data:{json.dumps(class_data)},backgroundColor:{json.dumps(class_colors)},borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{font:{{size:11}}}}}}}}}}}}));
new Chart(document.getElementById('sC'),{{type:'doughnut',data:{{labels:{json.dumps(status_labels)},datasets:[{{data:{json.dumps(status_data)},backgroundColor:{json.dumps(status_colors)},borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{font:{{size:11}}}}}}}}}}}}));
new Chart(document.getElementById('oC'),{{type:'bar',data:{{labels:{json.dumps(owner_labels)},datasets:[{{label:'Tickets',data:{json.dumps(owner_data)},backgroundColor:'{color}cc',borderColor:'{color}',borderWidth:1,borderRadius:4}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true,ticks:{{stepSize:1}}}},y:{{ticks:{{font:{{size:11}}}}}}}}}}}}));
new Chart(document.getElementById('aC'),{{type:'bar',data:{{labels:{json.dumps(account_labels)},datasets:[{{label:'Tickets',data:{json.dumps(account_data)},backgroundColor:'{color}aa',borderColor:'{color}',borderWidth:1,borderRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}},x:{{ticks:{{font:{{size:10}},maxRotation:45}}}}}}}}}}));
function filterTable(){{const q=document.getElementById('q').value.toLowerCase();for(const r of document.getElementById('TB').rows)r.style.display=r.textContent.toLowerCase().includes(q)?'':'none'}}
</script>
</body>
</html>"""

# ── Dashboard estratégico ──────────────────────────────────────────────────────

def generate_strategic_html(all_tickets, celula_groups, all_celulas, today):
    gm = calc_metrics(all_tickets)
    cm = {c: calc_metrics(celula_groups[c]) for c in all_celulas}

    gb_class = group_by(all_tickets, "classification")
    class_labels = list(gb_class.keys())
    class_data   = list(gb_class.values())
    class_colors = [CLASS_COLORS.get(l, "#95A5A6") for l in class_labels]

    statuses = ["Open", "Waiting On Customer", "Escalated"]
    stacked  = {s: [sum(1 for t in celula_groups[c] if t["status"]==s) for c in all_celulas] for s in statuses}

    def trow(t):
        cc  = CELULA_COLORS.get(t["celula"], DEFAULT_COLOR)
        due = t["due_date"] if t["due_date"] and t["due_date"] != "-" else "&#8212;"
        return (f'<tr><td>{t["id"]}</td>'
                f'<td><span style="background:{cc};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">{t["celula"]}</span></td>'
                f'<td title="{t["account"]}">{t["account"][:40]}{"..." if len(t["account"])>40 else ""}</td>'
                f'<td title="{t["subject"]}">{t["subject"][:55]}{"..." if len(t["subject"])>55 else ""}</td>'
                f'<td>{t["owner"]}</td><td>{due}</td></tr>')

    overdue_tickets   = [t for t in all_tickets if t["overdue"]]
    escalated_tickets = [t for t in all_tickets if t["status"] == "Escalated"]
    overdue_rows   = "".join(trow(t) for t in overdue_tickets)
    escalated_rows = "".join(trow(t) for t in escalated_tickets)

    cards = ""
    for c in all_celulas:
        m     = cm[c]
        color = CELULA_COLORS.get(c, DEFAULT_COLOR)
        warn  = f'<br><span style="color:#E74C3C;font-weight:700;">&#9888; {m["overdue"]} Vencidos</span>' if m["overdue"] > 0 else ""
        cards += (f'<a href="Dashboard_{c}.html" class="celula-card" style="border-top-color:{color};">'
                  f'<div class="celula-name" style="color:{color};">{c}</div>'
                  f'<div class="celula-total">{m["total"]}</div>'
                  f'<div class="celula-detail">'
                  f'<span style="color:#2E86DE;">&#9679; {m["open"]} Open</span> '
                  f'<span style="color:#F5A623;">&#9679; {m["waiting"]} Esp.</span> '
                  f'<span style="color:#E74C3C;">&#9679; {m["escalated"]} Esc.</span>'
                  f'{warn}</div></a>')

    comp_rows = ""
    for c in all_celulas:
        m     = cm[c]
        color = CELULA_COLORS.get(c, DEFAULT_COLOR)
        comp_rows += (f'<tr>'
                      f'<td><span style="background:{color};color:#fff;padding:3px 12px;border-radius:12px;font-weight:700;">{c}</span></td>'
                      f'<td style="text-align:center;font-weight:700;">{m["total"]}</td>'
                      f'<td style="text-align:center;color:#2E86DE;">{m["open"]}</td>'
                      f'<td style="text-align:center;color:#F5A623;">{m["waiting"]}</td>'
                      f'<td style="text-align:center;color:#E74C3C;">{m["escalated"]}</td>'
                      f'<td style="text-align:center;color:#E74C3C;font-weight:{"700" if m["overdue"]>0 else "400"};">{m["overdue"]}</td>'
                      f'<td><a href="Dashboard_{c}.html" style="color:{color};font-weight:600;text-decoration:none;">Ver &rarr;</a></td>'
                      f'</tr>')

    tbl_header = '<table><thead><tr><th>ID</th><th>C&eacute;lula</th><th>Cliente</th><th>Asunto</th><th>Agente</th><th>Vence</th></tr></thead><tbody>'
    esc_section  = tbl_header + escalated_rows + '</tbody></table>' if escalated_tickets else '<p style="color:#aaa;padding:16px">Sin tickets escalados.</p>'
    over_section = tbl_header + overdue_rows   + '</tbody></table>' if overdue_tickets   else '<p style="color:#aaa;padding:16px">Sin tickets vencidos.</p>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dashboard Estrat&eacute;gico &mdash; {today}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:#f0f2f5;color:#333}}
.header{{background:linear-gradient(135deg,#1B3A6B,#2E86DE);color:#fff;padding:24px 30px}}
.header h1{{font-size:26px;font-weight:800}}
.header .sub{{font-size:13px;opacity:.85;margin-top:6px}}
.container{{padding:24px 30px;max-width:1400px;margin:0 auto}}
.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px}}
.kpi{{background:#fff;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.07);border-top:4px solid #1B3A6B}}
.kpi .value{{font-size:38px;font-weight:800}}
.kpi .label{{font-size:12px;color:#777;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}}
.celula-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}}
.celula-card{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,.07);border-top:5px solid #1B3A6B;text-decoration:none;color:#333;transition:transform .15s,box-shadow .15s;display:block}}
.celula-card:hover{{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12)}}
.celula-name{{font-size:18px;font-weight:800;margin-bottom:4px}}
.celula-total{{font-size:36px;font-weight:800;color:#333;margin:8px 0}}
.celula-detail{{font-size:12px;line-height:1.8}}
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.card{{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.07)}}
.card h3{{font-size:14px;font-weight:700;color:#444;margin-bottom:16px;text-transform:uppercase;letter-spacing:.5px}}
.chart-container{{position:relative;height:300px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#1B3A6B;color:#fff;padding:10px 12px;text-align:left;font-weight:600}}
td{{padding:9px 12px;border-bottom:1px solid #f0f0f0;vertical-align:middle}}
tr:hover td{{background:#f7f9ff}}
.section-title{{font-size:16px;font-weight:700;color:#444;margin:24px 0 12px;padding-bottom:8px;border-bottom:2px solid #e0e0e0}}
.footer{{text-align:center;padding:20px;color:#aaa;font-size:12px}}
</style>
</head>
<body>
<div class="header">
  <h1>&#127962; Dashboard Estrat&eacute;gico &mdash; Todas las C&eacute;lulas</h1>
  <div class="sub">Reporte semanal consolidado &middot; {today} &middot; Solusoft &mdash; Soluciones y Servicios Tecnol&oacute;gicos</div>
</div>
<div class="container">
  <div class="kpi-row">
    <div class="kpi"><div class="value" style="color:#1B3A6B">{gm['total']}</div><div class="label">Total Tickets</div></div>
    <div class="kpi"><div class="value" style="color:#2E86DE">{gm['open']}</div><div class="label">Abiertos</div></div>
    <div class="kpi"><div class="value" style="color:#F5A623">{gm['waiting']}</div><div class="label">Esp. Cliente</div></div>
    <div class="kpi"><div class="value" style="color:#E74C3C">{gm['escalated']}</div><div class="label">Escalados</div></div>
    <div class="kpi"><div class="value" style="color:#E74C3C">{gm['overdue']}</div><div class="label">Vencidos</div></div>
  </div>
  <div class="section-title">&#128204; Acceso por C&eacute;lula</div>
  <div class="celula-grid">{cards}</div>
  <div class="section-title">&#128202; An&aacute;lisis Comparativo</div>
  <div class="charts-row">
    <div class="card"><h3>Estado por C&eacute;lula</h3><div class="chart-container"><canvas id="stackC"></canvas></div></div>
    <div class="card"><h3>Clasificaci&oacute;n Global</h3><div class="chart-container"><canvas id="gClassC"></canvas></div></div>
  </div>
  <div class="section-title">&#128203; Tabla Comparativa</div>
  <div class="card" style="margin-bottom:24px">
    <table><thead><tr><th>C&eacute;lula</th><th style="text-align:center">Total</th><th style="text-align:center">Abiertos</th><th style="text-align:center">Esp. Cliente</th><th style="text-align:center">Escalados</th><th style="text-align:center">Vencidos</th><th>Link</th></tr></thead>
    <tbody>{comp_rows}</tbody></table>
  </div>
  <div class="section-title">&#9888;&#65039; Tickets Escalados ({len(escalated_tickets)})</div>
  <div class="card" style="margin-bottom:24px">{esc_section}</div>
  <div class="section-title">&#128308; Tickets Vencidos ({len(overdue_tickets)})</div>
  <div class="card" style="margin-bottom:24px">{over_section}</div>
</div>
<div class="footer">Solusoft &middot; Dashboard Estrat&eacute;gico &middot; {today}</div>
<script>
new Chart(document.getElementById('stackC'),{{type:'bar',data:{{labels:{json.dumps(all_celulas)},datasets:[{{label:'Open',data:{json.dumps(stacked['Open'])},backgroundColor:'#2E86DE',borderRadius:4}},{{label:'Waiting On Customer',data:{json.dumps(stacked['Waiting On Customer'])},backgroundColor:'#F5A623',borderRadius:4}},{{label:'Escalated',data:{json.dumps(stacked['Escalated'])},backgroundColor:'#E74C3C',borderRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'top'}}}},scales:{{x:{{stacked:true}},y:{{stacked:true,beginAtZero:true,ticks:{{stepSize:1}}}}}}}}}}));
new Chart(document.getElementById('gClassC'),{{type:'doughnut',data:{{labels:{json.dumps(class_labels)},datasets:[{{data:{json.dumps(class_data)},backgroundColor:{json.dumps(class_colors)},borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{font:{{size:11}}}}}}}}}}}}));
</script>
</body>
</html>"""

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Genera dashboards HTML de tickets")
    parser.add_argument("--csv",    required=True, help="Ruta al archivo CSV")
    parser.add_argument("--output", required=True, help="Carpeta de salida para los HTMLs")
    parser.add_argument("--date",   required=True, help="Fecha en formato YYYY-MM-DD")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    tickets = parse_csv(args.csv)
    print(f"[OK] {len(tickets)} tickets leídos de {args.csv}")

    celula_groups = defaultdict(list)
    for t in tickets:
        celula_groups[t["celula"]].append(t)

    all_celulas = sorted(celula_groups.keys())
    print(f"[OK] Células: {all_celulas}")

    for celula in all_celulas:
        html = generate_celula_html(celula, celula_groups[celula], all_celulas, args.date)
        path = os.path.join(args.output, f"Dashboard_{celula}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] {path} ({len(celula_groups[celula])} tickets)")

    strategic = generate_strategic_html(tickets, celula_groups, all_celulas, args.date)
    path = os.path.join(args.output, "Dashboard_Estrategico.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(strategic)
    print(f"[OK] {path}")

    print(f"\n[DONE] {len(all_celulas)+1} archivos HTML en {args.output}")

if __name__ == "__main__":
    main()
