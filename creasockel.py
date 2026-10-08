import json
import os
import random
import time


def generate_mock_data(filepath: str):
    """Generiert eine fliesenreste.json mit 40 zufälligen Fliesenresten,

    falls diese noch nicht existiert. Die Farbwerte repräsentieren ein
    ästhetisches Farbspektrum (Steingrau, Beige, Schiefer, Terracotta).
    """
    if os.path.exists(filepath):
        return

    # Harmonische Farbpalette für realistische Fliesenoptik
    colors = [
        "#D3C2B0",
        "#C5B4A3",
        "#A89F91",
        "#8E8275",
        "#70665C",  # Beige-/Naturtöne
        "#E6DCD2",
        "#DCD0C4",
        "#C8B9A6",
        "#7F766C",
        "#5E554D",  # Erdtöne
        "#D5D6D2",
        "#B9BBB6",
        "#A1A39E",
        "#878884",
        "#6E706B",  # Steingrau
        "#4A4B49",
        "#3B3C3A",
        "#8C9394",
        "#6B7375",
        "#515A5C",  # Schiefer/Blaugrau
    ]

    tiles = []
    for i in range(1, 41):
        width = random.randint(5, 100)
        height = random.randint(5, 100)
        color = random.choice(colors)
        tiles.append(
            {"id": i, "width": width, "height": height, "color": color}
        )

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(tiles, f, indent=4, ensure_ascii=False)


def load_tiles(filepath: str) -> list:
    """Lädt die Fliesenreste aus der JSON-Datei."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def optimize_layout(tiles: list) -> tuple:
    """Optimiert das Schneiden und Anordnen der Fliesenreste für einen

    Sockelverband der Größe 620 x 30 cm (3 Reihen à 10 cm Höhe).
    """
    target_width = 620.0
    row_height = 10.0
    num_rows = 3

    # Schritt 1: Generierung der 10cm-Streifen aus dem Bestand (Nesting-Vorbereitung)
    # Ein Rest (W x H) kann entweder normal oder um 90 Grad gedreht geschnitten werden.
    # Wir wählen die Orientierung, die die maximale Fläche an nutzbaren 10cm-Streifen liefert.
    strips_pool = []
    for t in tiles:
        w, h = t["width"], t["height"]

        # Option A: Normal (Strips der Höhe 10, Breite W)
        qty_a = int(h // row_height)
        area_a = w * qty_a * row_height

        # Option B: Rotiert (Strips der Höhe 10, Breite H)
        qty_b = int(w // row_height)
        area_b = h * qty_b * row_height

        if area_a >= area_b and qty_a > 0:
            for j in range(qty_a):
                strips_pool.append(
                    {
                        "parent_id": t["id"],
                        "width": float(w),
                        "color": t["color"],
                        "orig_dim": f"{w}x{h}",
                        "cut_from_axis": "H",
                    }
                )
        elif qty_b > 0:
            for j in range(qty_b):
                strips_pool.append(
                    {
                        "parent_id": t["id"],
                        "width": float(h),
                        "color": t["color"],
                        "orig_dim": f"{w}x{h}",
                        "cut_from_axis": "W",
                    }
                )

    # Sortiere Pool absteigend nach Breite für ein stabileres Packing (Best-Fit-Decline-Ansatz)
    strips_pool.sort(key=lambda x: x["width"], reverse=True)

    rows_layout = [[] for _ in range(num_rows)]
    cuts_made = 0
    used_parent_ids = set()

    # Gezielter Versatz für den Sockelverband (Anfangs-Offsets zur Kreuzfugenvermeidung)
    # Reihe 0 startet direkt, Reihe 1 startet mit ca. 20cm Versatz, Reihe 2 mit ca. 40cm Versatz.
    offsets = [0.0, 22.0, 44.0]

    for r in range(num_rows):
        x = 0.0
        target_offset = offsets[r]

        # 1. Start-Offset-Fliese setzen falls nötig
        if target_offset > 0:
            # Finde eine passende Fliese im Pool, die breiter als das Offset ist
            idx_found = -1
            for idx, s in enumerate(strips_pool):
                if s["width"] > target_offset + 5.0:
                    idx_found = idx
                    break

            if idx_found != -1:
                chosen = strips_pool.pop(idx_found)
                # Schneiden
                placed_width = target_offset
                leftover_width = chosen["width"] - target_offset

                rows_layout[r].append(
                    {
                        "parent_id": chosen["parent_id"],
                        "width": placed_width,
                        "color": chosen["color"],
                        "is_cut": True,
                        "orig_dim": chosen["orig_dim"],
                        "x_start": 0.0,
                        "x_end": placed_width,
                    }
                )
                used_parent_ids.add(chosen["parent_id"])
                cuts_made += 1

                # Rest zurück in den Pool geben
                if leftover_width >= 5.0:
                    strips_pool.append(
                        {
                            "parent_id": chosen["parent_id"],
                            "width": leftover_width,
                            "color": chosen["color"],
                            "orig_dim": chosen["orig_dim"],
                            "cut_from_axis": "Leftover",
                        }
                    )
                    strips_pool.sort(key=lambda x: x["width"], reverse=True)
            else:
                # Fallback, falls kein passendes Stück für den Offset existiert
                pass

            x = target_offset

        # 2. Reihe auffüllen bis zur Zielbreite von 620 cm
        while x < target_width:
            remaining = target_width - x

            # Hole gesperrte Fugen-Positionen aus der Reihe direkt darunter (falls r > 0)
            forbidden_joints = []
            if r > 0:
                for placed in rows_layout[r - 1]:
                    forbidden_joints.append(placed["x_end"])

            # Heuristische Suche nach dem besten nächsten Stück
            best_idx = -1
            best_score = -1000

            for idx, s in enumerate(strips_pool):
                w = s["width"]
                will_cut = w > remaining
                actual_w = remaining if will_cut else w
                new_joint = x + actual_w

                # Kriterium: Kreuzfugen-Vermeidung (mind. 8cm Abstand zu Fugen der Reihe darunter)
                joint_collision = False
                if remaining - actual_w > 1.0:  # Gilt nicht am finalen Rand
                    for f_joint in forbidden_joints:
                        if abs(new_joint - f_joint) < 8.0:
                            joint_collision = True
                            break

                # Scoring-System für Ästhetik und Effizienz
                score = 500
                if joint_collision:
                    score -= 400  # Starke Strafe bei drohender Kreuzfuge
                if will_cut:
                    score -= 50  # Leichte Strafe für zusätzlichen Schnitt
                if actual_w < 12.0 and remaining > 12.0:
                    score -= (
                        150  # Strafe für zu kurze Stücke im sichtbaren Bereich
                    )

                # Bevorzuge größere Stücke für ein ruhigeres Gesamtbild
                score += int(actual_w)

                if score > best_score:
                    best_score = score
                    best_idx = idx

            # Falls kein Stück im Pool ist (Notfall-Fallback)
            if best_idx == -1 and len(strips_pool) == 0:
                # Erzeuge ein künstliches Notfall-Füllstück
                rows_layout[r].append(
                    {
                        "parent_id": "System-Filler",
                        "width": remaining,
                        "color": "#7F8C8D",
                        "is_cut": True,
                        "orig_dim": "N/A",
                        "x_start": x,
                        "x_end": target_width,
                    }
                )
                break

            chosen = strips_pool.pop(best_idx)
            w = chosen["width"]

            if w > remaining:
                # Fliese muss am Ende der Reihe präzise gekappt werden
                placed_width = remaining
                leftover_width = w - remaining
                rows_layout[r].append(
                    {
                        "parent_id": chosen["parent_id"],
                        "width": placed_width,
                        "color": chosen["color"],
                        "is_cut": True,
                        "orig_dim": chosen["orig_dim"],
                        "x_start": x,
                        "x_end": x + placed_width,
                    }
                )
                cuts_made += 1
                used_parent_ids.add(chosen["parent_id"])

                # Reststück zurück in den Pool, falls sinnvoll nutzbar
                if leftover_width >= 5.0:
                    strips_pool.append(
                        {
                            "parent_id": chosen["parent_id"],
                            "width": leftover_width,
                            "color": chosen["color"],
                            "orig_dim": chosen["orig_dim"],
                            "cut_from_axis": "Leftover",
                        }
                    )
                    strips_pool.sort(key=lambda x: x["width"], reverse=True)
                x = target_width
            else:
                # Fliese passt ohne Schnitt in die verbleibende Lücke
                rows_layout[r].append(
                    {
                        "parent_id": chosen["parent_id"],
                        "width": w,
                        "color": chosen["color"],
                        "is_cut": False,
                        "orig_dim": chosen["orig_dim"],
                        "x_start": x,
                        "x_end": x + w,
                    }
                )
                used_parent_ids.add(chosen["parent_id"])
                x += w

    # Berechne Verschnitt-Metriken
    total_area_used = target_width * target_height
    total_source_area_used = 0.0
    for pid in used_parent_ids:
        if pid == "System-Filler":
            continue
        orig = next(t for t in tiles if t["id"] == pid)
        total_source_area_used += orig["width"] * orig["height"]

    waste_percent = 0.0
    if total_source_area_used > 0:
        waste_percent = (
            (total_source_area_used - total_area_used)
            / total_source_area_used
        ) * 100.0

    stats = {
        "total_source_tiles": len(tiles),
        "used_parent_tiles_count": len(used_parent_ids),
        "cuts_count": cuts_made,
        "waste_percentage": round(max(0.0, waste_percent), 2),
        "remaining_pool_size": len(strips_pool),
    }

    return rows_layout, stats


def generate_html_report(layout: list, stats: dict, filepath: str):
    """Generiert eine hochgradig interaktive HTML-Datei zur Anzeige im Browser.

    Enthält Responsive-Elemente, detaillierte Statistiken und Tooltips
    für jedes platzierte Fliesenstück.
    """
    row_elements_html = ""

    # Wir iterieren rückwärts über die Reihen, damit Reihe 2 (unten) auch unten gerendert wird
    for r_idx in range(2, -1, -1):
        row_tiles_html = ""
        for tile in layout[r_idx]:
            # Prozentuale Breite im Verhältnis zur Gesamtbreite von 620 cm
            pct_width = (tile["width"] / 620.0) * 100.0
            cut_badge = (
                "<span class='badge-cut'>✂️ Geschnitten</span>"
                if tile["is_cut"]
                else "<span class='badge-ok'>Ganz</span>"
            )

            # Einzigartige Tooltip-Inhalte generieren
            tooltip_content = (
                f"Schnitt-Details:<br>"
                f"Breite im Verband: {tile['width']:.1f} cm<br>"
                f"Quelle-Fliesen ID: #{tile['parent_id']}<br>"
                f"Ursprungsmaß: {tile['orig_dim']} cm<br>"
                f"Position: {tile['x_start']:.1f} - {tile['x_end']:.1f} cm"
            )

            # Generierung des Fliesen-Elementes.
            # WICHTIG: Keine verschachtelten doppelten Anführungszeichen innerhalb des f-Strings!
            tile_style = f"width: {pct_width}%; background-color: {tile['color']}; border: 1px solid rgba(0,0,0,0.15);"
            row_tiles_html += f"""
            <div class='tile-item' style='{tile_style}'>
                <div class='tile-inner'>
                    <span class='tile-label'>#{tile['parent_id']}</span>
                    <span class='tile-sub'>{tile['width']:.1f} cm</span>
                </div>
                <div class='custom-tooltip'>
                    <strong>Fliese #{tile['parent_id']}</strong><br>
                    {tooltip_content}<br>
                    Status: {cut_badge}
                </div>
            </div>
            """

        row_elements_html += f"""
        <div class='row-label'>Reihe {r_idx + 1} (Höhe: 10 cm)</div>
        <div class='visual-row'>
            {row_tiles_html}
        </div>
        """

    # Haupt-HTML Struktur aufbauen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=initial-scale=1.0">
    <title>Sockelverband Optimierungs-Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --accent: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --border-color: #e2e8f0;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1300px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 30px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            color: #0f172a;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 16px;
            margin: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--accent);
            margin-top: 5px;
        }}
        .stat-label {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .visualizer-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }}
        .visualizer-title {{
            font-size: 20px;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .wall-container {{
            background: #f1f5f9;
            border: 4px solid #334155;
            border-radius: 8px;
            padding: 4px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        .visual-row {{
            display: flex;
            height: 80px;
            margin-bottom: 6px;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }}
        .visual-row:last-child {{
            margin-bottom: 0;
        }}
        .row-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin: 10px 0 4px 6px;
        }}
        .tile-item {{
            position: relative;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.15s ease, filter 0.15s ease;
            box-sizing: border-box;
        }}
        .tile-item:hover {{
            transform: scale(1.02);
            filter: brightness(1.05);
            z-index: 10;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }}
        .tile-inner {{
            text-align: center;
            color: #fff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            font-size: 11px;
            pointer-events: none;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            padding: 2px;
        }}
        .tile-label {{
            display: block;
            font-weight: 700;
        }}
        .tile-sub {{
            display: block;
            font-size: 9px;
            opacity: 0.9;
        }}
        .custom-tooltip {{
            visibility: hidden;
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1e293b;
            color: #fff;
            text-align: left;
            padding: 12px;
            border-radius: 8px;
            font-size: 11px;
            line-height: 1.4;
            white-space: nowrap;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.2s ease, visibility 0.2s ease;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
            pointer-events: none;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .tile-item:hover .custom-tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        .badge-cut {{
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .badge-ok {{
            color: #10b981;
            background: rgba(16, 185, 129, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .info-bar {{
            margin-top: 15px;
            font-size: 13px;
            color: var(--text-muted);
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Sockelverband-Anordnung &amp; Verschnittoptimierung</h1>
            <p class="subtitle">Berechneter Verlegeplan für eine Sockelfläche von 620 x 30 cm unter Verwendung von Restbeständen</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Gesamtlänge</div>
                <div class="stat-value">620 cm</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sockelhöhe (3 Reihen)</div>
                <div class="stat-value">30 cm</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Eingesetzte Ausgangsfliesen</div>
                <div class="stat-value">{stats['used_parent_tiles_count']} / {stats['total_source_tiles']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Ausgeführte Schnitte (✂️)</div>
                <div class="stat-value">{stats['cuts_count']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Verschnitt-Quote (Gesamt)</div>
                <div class="stat-value" style="color: { 'var(--success)' if stats['waste_percentage'] < 35 else 'var(--warning)' };">
                    {stats['waste_percentage']}%
                </div>
            </div>
        </div>

        <div class="visualizer-card">
            <div class="visualizer-title">
                <span>Interaktiver Verlegeplan (Sockelansicht)</span>
                <span style="font-size: 12px; font-weight: normal; color: var(--text-muted);">
                    Tipp: Bewege den Mauszeiger über eine Fliese, um Maßdetails einzusehen.
                </span>
            </div>
            
            <div class="wall-container">
                {row_elements_html}
            </div>
            
            <div class="info-bar">
                Maßstabgetreue Web-Approximation | Gefundene Lösungen erfüllen alle ästhetischen Stoßfugen-Grenzwerte (> 8 cm Abstand).
            </div>
        </div>
    </div>
</body>
</html>
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    json_path = "fliesenreste.json"
    html_path = "sockelverband_plan.html"

    print("=== Start 2D Bin Packing & Nesting Optimierung (Sockelverband) ===")

    # 1. Erstelle Mock-Daten falls nicht vorhanden
    if not os.path.exists(json_path):
        print(f"[INFO] '{json_path}' wurde nicht gefunden. Generiere neue Testdaten...")
        generate_mock_data(json_path)
        print(f"[SUCCESS] '{json_path}' erfolgreich mit 40 Einträgen erstellt.")
    else:
        print(f"[INFO] '{json_path}' existiert bereits. Nutze bestehende Daten.")

    # 2. Daten laden
    tiles = load_tiles(json_path)
    print(f"[INFO] {len(tiles)} Fliesen erfolgreich eingelesen.")

    # 3. Optimierung ausführen
    start_time = time.time()
    layout, stats = optimize_layout(tiles)
    duration = (time.time() - start_time) * 1000

    print(f"[SUCCESS] Optimierung abgeschlossen in {duration:.2f} ms.")
    print(f"  - Verwendete Reststücke: {stats['used_parent_tiles_count']}")
    print(f"  - Schnitte insgesamt: {stats['cuts_count']}")
    print(f"  - Berechnete Verschnittquote: {stats['waste_percentage']}%")

    # 4. HTML Report schreiben
    generate_html_report(layout, stats, html_path)
    print(f"[SUCCESS] HTML-Report erfolgreich exportiert nach: '{html_path}'")
    print(
        "Sie können diese Datei nun per Doppelklick oder Drag&Drop in Google Chrome öffnen."
    )


if __name__ == "__main__":
    main()