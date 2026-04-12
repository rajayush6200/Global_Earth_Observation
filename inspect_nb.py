import json
import io

with open('Integration_dash.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
output_lines = [f'Total cells: {len(cells)}']
for i, c in enumerate(cells):
    src = ''.join(c['source'])
    output_lines.append(f'\n=== Cell {i} ({c["cell_type"]}) ===')
    # Only ASCII to avoid codec issues
    safe_src = src.encode('ascii', 'replace').decode('ascii')
    output_lines.append(safe_src[:4000])
    if len(src) > 4000:
        output_lines.append('[TRUNCATED]')

with open('nb_content_ascii.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("Done. Written to nb_content_ascii.txt")
