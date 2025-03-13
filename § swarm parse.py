import os
from bs4 import BeautifulSoup
try:
    import chardet
except ImportError:
    chardet = None

import posixpath  # Used to correctly join URL paths

# ============================================================
# EDITABLE VARIABLES:
# Specify your input swarm shtml file and desired output HTML file.
# ============================================================
HTML_INPUT_FILE = '/Users/nicholaschang/Helpful Scripts/conquest parse/swarms.shtml'
OUTPUT_FILE = "/Users/nicholaschang/Helpful Scripts/conquest parse/swarm_pokemon.html"
BASE_URL = "https://www.serebii.net"
HTML_BASE_PATH = "/conquest"  # This should match the directory path of the original HTML

def main():
    if not os.path.isfile(HTML_INPUT_FILE):
        print(f"Could not find file: {HTML_INPUT_FILE}")
        return

    # Read file in binary mode for encoding detection.
    with open(HTML_INPUT_FILE, "rb") as f:
        raw_data = f.read()

    if chardet:
        detected = chardet.detect(raw_data)
        encoding = detected.get("encoding", "utf-8")
        print(f"Detected encoding: {encoding}")
    else:
        encoding = "utf-8"
        print("Chardet not installed; using utf-8.")

    text = raw_data.decode(encoding, errors="replace")
    soup = BeautifulSoup(text, "html.parser")

    # Look for the swarm table (assumed to be the first table with class "tab")
    table = soup.find("table", class_="tab")
    if not table:
        print("Could not find table with class 'tab'.")
        return

    headers, rows = extract_swarm_table_data(table)
    table_html = build_table_html(headers, rows)

    final_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Swarm Pokemon</title>
</head>
<body>
  <h1>Swarm Pokemon</h1>
  {table_html}
  {localstorage_script("swarm")}
</body>
</html>
"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(final_html)
    print(f"Done! Output saved to {OUTPUT_FILE}")

def extract_swarm_table_data(table):
    """
    Extracts rows from the provided swarm table.
    The original table is expected to have 12 columns:
      0: No.
      1: Pic (contains an image)
      2: Name (with a link – to be delinked)
      3: Type (contains an image)
      4: HP
      5: Attack
      6: Defence
      7: Speed
      8: Movement Range
      9: Moves (skip this column)
      10: Abilities (with links – delink these and separate abilities with <br>)
      11: Nation (may include images and links)
    New column order becomes:
      No., Pic, Name, Type, Hp, Attack, Defence, Speed, Movement Range, Abilities, Nation, Trainers
    """
    new_headers = ["No.", "Pic", "Name", "Type", "Hp", "Attack", "Defence", "Speed", "Movement Range", "Abilities", "Nation", "Trainers"]
    data_rows = []
    all_rows = table.find_all("tr", recursive=False)
    # Skip the header row (assumed first row)
    for tr in all_rows[1:]:
        cells = [child for child in tr.children if getattr(child, "name", None) == "td"]
        if len(cells) < 12:
            continue
        # Use indices: 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11 (skip column 9: "Moves")
        indices_to_use = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11]
        new_row = []
        for idx in indices_to_use:
            cell = cells[idx]
            # For "Pic" (index 1) and "Type" (index 3), fix images.
            if idx == 1:  # Pic column: also resize images
                value = fix_images(cell, base_path=HTML_BASE_PATH, max_width=50)
            elif idx == 3:  # Type column: no resizing applied here
                value = fix_images(cell, base_path=HTML_BASE_PATH)
            # For "Name" (index 2), extract plain text.
            elif idx == 2:
                value = cell.get_text(strip=True)
            # For "Abilities" (index 10), get text with a <br> separator.
            elif idx == 10:
                value = cell.get_text(separator="<br>", strip=True)
            # For "Nation" (index 11), fix images and remove any links.
            elif idx == 11:
                value = remove_links(fix_images(cell, base_path=HTML_BASE_PATH))
            else:
                value = cell.get_text(strip=True)
            new_row.append(value)
        # Append an empty cell for the Trainers column.
        new_row.append("")
        data_rows.append(new_row)
    return new_headers, data_rows

def fix_images(cell_tag, base_path="/conquest", max_width=None):
    """
    Converts the inner HTML of the cell using BeautifulSoup and
    prepends BASE_URL and base_path to any <img> tag's src that is not absolute.
    Also handles sources starting with a dot.
    If max_width is provided, adds an inline style to limit the image's width.
    """
    temp_soup = BeautifulSoup(cell_tag.decode_contents(), "html.parser")
    for img in temp_soup.find_all("img"):
        src = img.get("src", "").strip()
        # Remove leading dot if present.
        if src.startswith("."):
            src = src.lstrip(".")
        # If src is not absolute...
        if not src.startswith("http"):
            if not src.startswith("/"):
                src = posixpath.join(base_path, src)
                if not src.startswith("/"):
                    src = "/" + src
            img["src"] = BASE_URL + src
        # If max_width is provided, add an inline style.
        if max_width:
            current_style = img.get("style", "")
            new_style = (current_style + " " if current_style else "") + f"max-width:{max_width}px; height:auto;"
            img["style"] = new_style
    return str(temp_soup)

def remove_links(html):
    """
    Removes all <a> tags from the provided HTML while preserving their inner content.
    """
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a"):
        a.unwrap()
    return str(soup)

def build_table_html(headers, rows):
    """
    Constructs an HTML table from the given headers and rows.
    The final column ("Trainers") is set to be contenteditable.
    Also, sets a fixed width for the "Pic" column.
    """
    html = []
    html.append('<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;" align="center">')
    html.append("<thead><tr>")
    for head in headers:
        if head == "Pic":
            html.append(f"<th style='width:60px;'>{head}</th>")
        else:
            html.append(f"<th>{head}</th>")
    html.append("</tr></thead>")
    html.append("<tbody>")
    for row in rows:
        html.append("<tr>")
        for col_index, cell in enumerate(row):
            if col_index == len(row) - 1:
                html.append(f'<td contenteditable="true" class="trainers-col">{cell}</td>')
            else:
                html.append(f"<td>{cell}</td>")
        html.append("</tr>")
    html.append("</tbody>")
    html.append("</table>")
    return "\n".join(html)

def localstorage_script(identifier):
    """
    Returns a JavaScript snippet that makes the Trainers column editable and
    persists changes using localStorage. The keys include the given identifier so that
    different output files save data independently.
    """
    return f"""<script>
document.addEventListener('DOMContentLoaded', function() {{
  const trainerCells = document.querySelectorAll('td.trainers-col');
  trainerCells.forEach((cell, i) => {{
    const key = 'trainers_cell_{identifier}_' + i;
    const saved = localStorage.getItem(key);
    if (saved) cell.textContent = saved;
    cell.addEventListener('blur', () => {{
      localStorage.setItem(key, cell.textContent);
    }});
  }});
}});
</script>"""

if __name__ == "__main__":
    main()
