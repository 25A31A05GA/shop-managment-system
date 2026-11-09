#!/usr/bin/env python3
"""Render docs/*.md to static HTML inside docs/ (run before committing; needs: pip install markdown).
Output is plain HTML, so Vercel and GitHub Pages need no build step."""
import pathlib, re, markdown
D = pathlib.Path(__file__).resolve().parent.parent / "docs"
TOP = {"REPORT.md": "report", "JOURNEY.md": "journey", "ARCHITECTURE.md": "architecture", "API.md": "api", "RECRUITER_KIT.md": "recruiter-kit"}
PAGES = {k: v + ".html" for k, v in TOP.items()}
for p in sorted((D / "case-studies").glob("*.md")):
    PAGES["case-studies/" + p.name] = "case-studies/" + ("index.html" if p.name == "README.md" else p.stem + ".html")
CSS = """:root{--bg:#11151c;--card:#1a2029;--bd:#333d4c;--pri:#ff8a2b;--tx:#eef1f6;--mut:#a9b2c0;color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.65 'Noto Sans',system-ui,Segoe UI,sans-serif}
header{border-bottom:1px solid var(--bd);padding:12px 20px;display:flex;gap:18px;flex-wrap:wrap;background:#161b23}
header a{color:var(--mut);text-decoration:none;font-size:14px}header a:hover,header a.b{color:var(--pri)}
main{max-width:880px;margin:0 auto;padding:28px 20px 80px}h1{color:var(--pri);line-height:1.2}h2{border-bottom:1px solid var(--bd);padding-bottom:6px;margin-top:2em}a{color:var(--pri)}
code{background:#0f141b;padding:1px 6px;border-radius:4px;font-size:.9em}pre{background:#0f141b;border:1px solid var(--bd);padding:14px;overflow:auto;border-radius:8px}pre code{background:none;padding:0}
table{border-collapse:collapse;display:block;overflow-x:auto}th,td{border:1px solid var(--bd);padding:7px 10px;text-align:left;vertical-align:top}th{background:#161b23}
blockquote{border-left:3px solid var(--pri);margin:1em 0;padding:2px 16px;background:#161b23;color:var(--mut)}img{max-width:100%}"""

def fix_links(html, depth):
    def sub(m):
        u = m.group(1)
        if re.match(r"(https?:|#|mailto:)", u):
            return m.group(0)
        frag = "#" + u.split("#")[1] if "#" in u else ""
        base = u.split("#")[0]
        base = re.sub(r"^(\.\./)?(\./)?docs/", "", base)
        name = base.split("/")[-1]
        if name in TOP:
            base = ("../" * depth) + TOP[name] + ".html"
        else:
            base = re.sub(r"\.md$", ".html", base)
            base = re.sub(r"(^|/)README\.html$", r"\1index.html", base)
        return 'href="%s%s"' % (base, frag)
    return re.sub(r'href="([^"]+)"', sub, html)

for src, out in PAGES.items():
    md = (D / src).read_text(encoding="utf-8")
    depth = out.count("/")
    body = fix_links(markdown.markdown(md, extensions=["tables", "fenced_code"]), depth)
    root = "../" * depth
    t = re.search(r"^#\s+(.+)$", md, re.M)
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t.group(1) if t else 'Docs'} · Dukan Drishti</title><style>{CSS}</style></head><body>
<header><a class="b" href="{root}./">⌂ Dukan Drishti</a><a href="{root}dashboard.html">Live dashboard</a><a href="{root}report.html">Report</a><a href="{root}journey.html">Our journey</a><a href="{root}case-studies/">Case studies</a><a href="{root}architecture.html">Architecture</a><a href="{root}api.html">API</a><a href="{root}Dukan_Drishti.pptx">Slides</a></header>
<main>{body}</main></body></html>"""
    (D / out).parent.mkdir(parents=True, exist_ok=True)
    (D / out).write_text(html, encoding="utf-8")
    print("wrote docs/" + out)
