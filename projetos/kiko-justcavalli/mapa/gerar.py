"""Gera o mapa de cenas (HTML) com as miniaturas embutidas."""
import json

cenas = json.load(open("/home/user/work/kiko/mapa/cenas.json"))
TEMPLATE = open("/home/user/work/kiko/mapa/mapa_template.html", encoding="utf-8").read()
html = TEMPLATE.replace("/*CENAS*/[]", json.dumps(cenas, ensure_ascii=False))
open("/home/user/claude/entregas/mapa_cenas_kiko.html", "w", encoding="utf-8").write(html)
print(len(html) // 1024, "KB")
