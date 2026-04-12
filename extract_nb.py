import json

with open('Integration_dash.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']

with open('full_notebook_code.py', 'w', encoding='utf-8') as out:
    out.write(f'# Total cells: {len(cells)}\n\n')
    for i, c in enumerate(cells):
        src = ''.join(c['source'])
        out.write(f'\n# ===== Cell {i} ({c["cell_type"]}) =====\n')
        out.write(src)
        out.write('\n')

print(f"Extracted {len(cells)} cells to full_notebook_code.py")
