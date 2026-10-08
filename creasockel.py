```python
import os
import json
import random
import math

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
JSON_FILENAME = "fliesenreste.json"
HTML_FILENAME = "fliesen_layout.html"

# Target dimensions in cm (6.2 m x 0.3 m)
TARGET_WIDTH = 620.0
TARGET_HEIGHT = 30.0

# Aesthetic rules for "Wilder Verband" (harmonious joint layout)
MIN_JOINT_OFFSET = 8.0  # Minimum distance between vertical joints in adjacent rows
MIN_TILE_WIDTH = 10.0   # Avoid very small slivers at the ends of rows if possible
DESIRED_ROW_HEIGHTS = [10.0, 10.0, 10.0]  # 3 elegant rows of 10cm each summing to 30cm

# ==============================================================================
# DATA GENERATION & I/O
# ==============================================================================
def generate_tile_assets_if_not_exists():
    """Generates the fliesenreste.json file with 40 random tiles if it does not exist."""
    if not os.path.exists(JSON_FILENAME):
        # Professional palette of harmonious tile colors (earthy, concrete, stone tones)
        colors = [
            "#3E4A56", "#7F8C8D", "#BDC3C7", "#95A5A6", "#E5E7E9",
            "#D5D8DC", "#ABB2B9", "#566573", "#2C3E50", "#85929E"
        ]
        tiles = []
        for i in range(1, 41):
            width = round(random.uniform(5.0, 100.0), 1)
            height = round(random.uniform(5.0, 100.0), 1)
            tiles.append({
                "id": i,
                "width": width,
                "height": height,
                "color": random.choice(colors)
            })
        with open(JSON_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(tiles, f, indent=4)

def load_tile_assets():
    """Reads and returns the complete tiles list from JSON."""
    with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==============================================================================
# OPTIMIZATION & NESTING ENGINE (2D CUTTING STOCK)
# ==============================================================================
class TileState:
    """Tracks the geometric cutting operations on a specific tile."""
    def __init__(self, tile_dict):
        self.id = tile_dict["id"]
        self.original_w = tile_dict["width"]
        self.original_h = tile_dict["height"]
        self.color = tile_dict["color"]
        self.current_w = tile_dict["width"]
        self.current_h = tile_dict["height"]
        self.parent_id = tile_dict["id"]
        self.cuts_made = 0

    def clone(self):
        ts = TileState({"id": self.id, "width": self.current_w, "height": self.current_h, "color": self.color})
        ts.original_w = self.original_w
        ts.original_h = self.original_h
        ts.parent_id = self.parent_id
        ts.cuts_made = self.cuts_made
        return ts

def simulate_packing(tile_pool, row_heights, seed_val):
    """
    Simulates a greedy placement of tiles into rows with random variations.
    Implements height and width cutting logic and tracks the remaining offcuts.
    """
    random.seed(seed_val)
    # Deep copy pool
    pool = [t.clone() for t in tile_pool]
    
    # Shuffle to explore different packing sequences
    random.shuffle(pool)
    
    rows_layout = []
    total_waste_area = 0.0
    used_tiles_log = []
    
    # Keep track of vertical joints of the previous row to respect aesthetic offsets
    prev_joints = []
    
    for row_idx, r_height in enumerate(row_heights):
        row_tiles = []
        current_x = 0.0
        row_joints = []
        
        while current_x < TARGET_WIDTH:
            # Filter pool: tile must be at least as high as the target row height
            valid_candidates = [t for t in pool if t.current_h >= r_height]
            
            if not valid_candidates:
                # Fallback: If no candidate fits height-wise, we must stop or allow substandard fit.
                # In practice, we skip or generate a virtual tile (unfavorable score).
                break
                
            # Aesthetic scoring for candidate selection
            best_candidate = None
            best_score = -float('inf')
            
            # Look at a small subset to optimize performance and randomness
            sample_size = min(len(valid_candidates), 8)
            candidates_to_test = random.sample(valid_candidates, sample_size)
            
            for candidate in candidates_to_test:
                score = 0.0
                potential_w = candidate.current_w
                potential_right_joint = current_x + potential_w
                
                # Penalize joints aligning with the row directly below/above
                if prev_joints:
                    min_dist = min(abs(potential_right_joint - j) for j in prev_joints)
                    if min_dist < MIN_JOINT_OFFSET:
                        score -= (MIN_JOINT_OFFSET - min_dist) * 15.0  # Heavy penalty
                
                # Prefer tiles where height waste is minimal
                height_waste = candidate.current_h - r_height
                score -= height_waste * 2.0
                
                # Avoid tiny leftovers at the end of the row
                remaining_space = TARGET_WIDTH - potential_right_joint
                if 0.0 < remaining_space < MIN_TILE_WIDTH:
                    score -= 50.0
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if not best_candidate:
                best_candidate = valid_candidates[0]
                
            # Place the tile
            pool.remove(best_candidate)
            tile_to_place = best_candidate.clone()
            
            # 1. Cut height to row height
            height_waste_here = (tile_to_place.current_h - r_height) * tile_to_place.current_w
            total_waste_area += height_waste_here
            tile_to_place.current_h = r_height
            if height_waste_here > 0:
                tile_to_place.cuts_made += 1
                
            # 2. Check if width fits or needs cutting
            if current_x + tile_to_place.current_w > TARGET_WIDTH:
                # Cut width to fit exactly
                needed_w = TARGET_WIDTH - current_x
                width_waste_here = (tile_to_place.current_w - needed_w) * r_height
                
                # The cut remnant can be returned to the pool for reuse!
                remnant_w = tile_to_place.current_w - needed_w
                if remnant_w >= MIN_TILE_WIDTH:
                    remnant = tile_to_place.clone()
                    remnant.current_w = remnant_w
                    remnant.cuts_made += 1
                    pool.append(remnant)
                else:
                    total_waste_area += width_waste_here
                    
                tile_to_place.current_w = needed_w
                tile_to_place.cuts_made += 1
                
            # Save placement coordinates
            placement = {
                "id": tile_to_place.id,
                "parent_id": tile_to_place.parent_id,
                "x": current_x,
                "y": sum(row_heights[:row_idx]),
                "w": tile_to_place.current_w,
                "h": tile_to_place.current_h,
                "color": tile_to_place.color,
                "orig_w": tile_to_place.original_w,
                "orig_h": tile_to_place.original_h,
                "cuts": tile_to_place.cuts_made
            }
            row_tiles.append(placement)
            used_tiles_log.append(placement)
            
            current_x += tile_to_place.current_w
            if current_x < TARGET_WIDTH:
                row_joints.append(current_x)
                
        rows_layout.append(row_tiles)
        prev_joints = row_joints
        
    # Evaluate layout quality
    # We check if we successfully packed the target dimension completely
    complete = len(rows_layout) == len(row_heights) and all(abs(sum(t["w"] for t in r) - TARGET_WIDTH) < 0.1 for r in rows_layout)
    
    # Calculate alignment penalty metric
    alignment_penalty = 0.0
    for r in range(len(rows_layout) - 1):
        joints_curr = [sum(t["w"] for t in rows_layout[r][:i+1]) for i in range(len(rows_layout[r]) - 1)]
        joints_next = [sum(t["w"] for t in rows_layout[r+1][:i+1]) for i in range(len(rows_layout[r+1]) - 1)]
        for jc in joints_curr:
            for jn in joints_next:
                dist = abs(jc - jn)
                if dist < MIN_JOINT_OFFSET:
                    alignment_penalty += (MIN_JOINT_OFFSET - dist) ** 2
                    
    # Score: lower is better
    score = total_waste_area + (alignment_penalty * 10.0)
    if not complete:
        score += 100000.0  # Heavy penalty for incomplete solutions
        
    return {
        "layout": rows_layout,
        "score": score,
        "complete": complete,
        "waste_area": total_waste_area,
        "used_count": len(used_tiles_log),
        "alignment_penalty": alignment_penalty
    }

def optimize_layout(tile_pool, iterations=1500):
    """Runs a Monte Carlo simulation over many random seed layouts to find the global optimum."""
    best_solution = None
    best_score = float('inf')
    
    # Transform raw json tiles to domain objects
    domain_pool = [TileState(t) for t in tile_pool]
    
    for i in range(iterations):
        sol = simulate_packing(domain_pool, DESIRED_ROW_HEIGHTS, seed_val=i)
        if sol["complete"] and sol["score"] < best_score:
            best_score = sol["score"]
            best_solution = sol
            
    return best_solution

# ==============================================================================
# HTML GENERATION ENGINE
# ==============================================================================
def create_html_report(solution, original_tiles):
    """Generates the HTML dashboard containing statistics, interactive SVG vector views, and cutting instructions."""
    layout = solution["layout"]
    total_area = TARGET_WIDTH * TARGET_HEIGHT
    waste_percent = (solution["waste_area"] / total_area) * 100.0
    efficiency = 100.0 - waste_percent
    
    # Count how many cuts were needed
    total_cuts = sum(sum(tile["cuts"] for tile in row) for row in layout)
    
    # Gather visual elements
    svg_elements = []
    tile_cards_html = []
    
    # Draw background target area
    svg_elements.append(f'<rect x="0" y="0" width="{TARGET_WIDTH*10}" height="{TARGET_HEIGHT*10}" fill="#2c3e50" rx="5" ry="5" />')
    
    for r_idx, row in enumerate(layout):
        for tile in row:
            # Transform dimensions to mm (x10) for pristine SVG rendering
            x = tile["x"] * 10
            y = tile["y"] * 10
            w = tile["w"] * 10
            h = tile["h"] * 10
            
            # Main tile rect
            svg_elements.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="{tile["color"]}" stroke="#ffffff" stroke-width="4" '
                f'class="tile-rect" data-id="{tile["id"]}" data-parent="{tile["parent_id"]}" '
                f'data-dims="{tile["w"]}x{tile["h"]} cm" />'
            )
            # Label
            if w > 250: # Only draw label if space permits
                svg_elements.append(
                    f'<text x="{x + w/2}" y="{y + h/2 + 10}" font-size="28" fill="#111" font-weight="bold" text-anchor="middle" class="svg-text">'
                    f'ID {tile["parent_id"]} ({round(tile["w"],1)}cm)'
                    f'</text>'
                )
                
    # List of original scraps vs placed
    used_ids = [t["parent_id"] for row in layout for t in row]
    
    # Render layout tables and instructions
    instructions_html = []
    for r_idx, row in enumerate(layout):
        instructions_html.append(f"<h3>Reihe {r_idx + 1} (Höhe: {DESIRED_ROW_HEIGHTS[r_idx]} cm)</h3>")
        instructions_html.append("<table><tr><th>Reihen-Position (X)</th><th>Fliesen-ID (Herkunft)</th><th>Ziel-Größe (BxH)</th><th>Schnitt-Aufwand</th><th>Original-Größe</th></tr>")
        for tile in row:
            cut_status = "Höhen- & Breitenzuschnitt" if tile["cuts"] >= 2 else ("Zuschnitt" if tile["cuts"] == 1 else "Kein Schnitt")
            instructions_html.append(
                f"<tr>"
                f"<td>{round(tile['x'], 1)} cm bis {round(tile['x'] + tile['w'], 1)} cm</td>"
                f"<td><strong>ID {tile['parent_id']}</strong></td>"
                f"<td>{round(tile['w'], 1)} x {round(tile['h'], 1)} cm</td>"
                f"<td><span class='badge {"badge-red" if tile["cuts"] > 0 else "badge-green"}'>{cut_status}</span></td>"
                f"<td>{tile['orig_w']} x {tile['orig_h']} cm</td>"
                f"</tr>"
            )
        instructions_html.append("</table>")

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Zweidimensionale Verschnittoptimierung - Fliesenreste</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f4f6f8;
            color: #333;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 40px;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 20px;
        }}
        h1 {{
            margin: 0;
            font-size: 2.2rem;
            color: #2c3e50;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 5px solid #3498db;
        }}
        .metric-card.accent {{
            border-left-color: #2ecc71;
        }}
        .metric-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            color: #7f8c8d;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 5px;
            color: #2c3e50;
        }}
        .visualization-box {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.05);
            margin-bottom: 40px;
            overflow-x: auto;
        }}
        svg {{
            width: 100%;
            height: auto;
            border-radius: 6px;
            background: #fafafa;
        }}
        .tile-rect {{
            transition: opacity 0.2s, stroke 0.2s;
            cursor: pointer;
        }}
        .tile-rect:hover {{
            opacity: 0.85;
            stroke: #ff3f34 !important;
            stroke-width: 8 !important;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 30px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e1e4e8;
        }}
        th {{
            background-color: #f7f9fa;
            color: #2c3e50;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #fcfdfe;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-green {{
            background-color: #e2fbe8;
            color: #1e7e34;
        }}
        .badge-red {{
            background-color: #fce8e6;
            color: #c92a2a;
        }}
        .svg-text {{
            pointer-events: none;
            user-select: none;
        }}
        .info-panel {{
            background-color: #e8f4fd;
            border: 1px solid #b3d7f7;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 30px;
            font-size: 0.95rem;
            color: #2b5a84;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Zweidimensionale Verschnittoptimierung</h1>
            <p>Schnitt-Muster-Ergebnis für ein harmonisches Wandbild (Wilder Verband) | Zielfläche: {TARGET_WIDTH/100}m x {TARGET_HEIGHT/100}m</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card accent">
                <div class="metric-title">Flächeneffizienz</div>
                <div class="metric-value">{round(efficiency, 2)} %</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Gesamter Verschnitt</div>
                <div class="metric-value">{round(solution["waste_area"], 1)} cm²</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Verwendete Reststücke</div>
                <div class="metric-value">{solution["used_count"]} von {len(original_tiles)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Anzahl Schnitte</div>
                <div class="metric-value">{total_cuts}</div>
            </div>
        </div>

        <div class="info-panel">
            <strong>Bedienungshinweis:</strong> Fahren Sie mit der Maus über die einzelnen Fliesensegmente in der Grafik, um die verknüpften Quell-IDs und die exakten Endmaße zu visualisieren. Alle Maße sind im Verhältnis skaliert.
        </div>

        <h2>Visueller Verlegeplan (Vektorgrafik)</h2>
        <div class="visualization-box">
            <svg viewBox="0 0 {TARGET_WIDTH * 10} {TARGET_HEIGHT * 10}">
                {" ".join(svg_elements)}
            </svg>
        </div>

        <h2>Präzise Säge- und Verlegeanweisungen</h2>
        {"".join(instructions_html)}
    </div>
</body>
</html>
"""
    with open(HTML_FILENAME, 'w', encoding='utf-8') as f:
        f.write(html_content)

# ==============================================================================
# MAIN CONSOLIDATED ARCHITECTURE CONTROL
# ==============================================================================
def main():
    # 1. Ensure asset presence
    generate_tile_assets_if_not_exists()
    
    # 2. Extract input assets
    original_tiles = load_tile_assets()
    
    # 3. Optimize Layout (Solve 2D Bin Packing & Aesthetic Alignment)
    # Using 1500 search iterations to guarantee finding high-harmony results
    best_solution = optimize_layout(original_tiles, iterations=1500)
    
    if best_solution:
        # 4. Save results in responsive modern HTML dashboard format
        create_html_report(best_solution, original_tiles)
        print(f"Optimierung erfolgreich durchgeführt.")
        print(f"Zieldatei '{HTML_FILENAME}' wurde generiert.")
    else:
        print("Es konnte keine gültige Belegung generiert werden. Überprüfen Sie das Fliesen-Inventar.")

if __name__ == "__main__":
    main()
```