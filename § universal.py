import os
from bs4 import BeautifulSoup

try:
    import chardet
except ImportError:
    chardet = None

# Set this to the file you want to process.
HTML_INPUT_FILE = "/Users/nicholaschang/Helpful Scripts/conquest parse/shtml's of location/illusio.shtml"
BASE_URL = "https://www.serebii.net"

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
        print("Chardet not installed; using utf-8 with replacement.")

    # Decode using the detected encoding.
    text = raw_data.decode(encoding, errors="replace")
    soup = BeautifulSoup(text, "html.parser")

    # Extract location name from the title.
    title_text = soup.title.get_text() if soup.title else "Unknown Location"
    location = title_text.split("-")[-1].strip().lower()
    print(f"Detected location: {location}")

    # Set the output file name to "<location>_pokemon.html"
    output_file = f"{location}_pokemon.html"

    # Try method 1: extract area names from <a name="..."> tags within <p> tags that have a <font> element.
    area_names = get_area_names_from_anchors(soup)
    if not area_names:
        # Fallback: use the anctab table.
        area_names = get_area_names_from_anctab(soup)
    if not area_names:
        print("No area names found.")
        return

    sections = []
    for area in area_names:
        section_html = parse_area_section(soup, area)
        if section_html:
            sections.append(section_html)

    final_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{location.title()} Areas</title>
</head>
<body>
  <h1>{location.title()}</h1>
  {''.join(sections)}
  {localstorage_script(location)}
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(final_html)
    print(f"Done! See '{output_file}' for the final output.")

def get_area_names_from_anchors(soup):
    """
    Look for all <a> tags with a name attribute that are inside a <p> tag 
    containing a <font> element (common for area anchors).
    Returns a list of area names (lowercase).
    """
    area_names = []
    for a in soup.find_all("a", attrs={"name": True}):
        parent = a.find_parent("p")
        if parent:
            font = parent.find("font")
            if font:
                text = font.get_text(strip=True).lower()
                if text and text not in area_names:
                    area_names.append(text)
    return area_names

def get_area_names_from_anctab(soup):
    """
    Fallback: Find the table with class "anctab" and extract area names from its <a> tags.
    """
    anchor_table = soup.find("table", class_="anctab")
    if not anchor_table:
        return []
    area_names = []
    for a in anchor_table.find_all("a"):
        text = a.get_text(strip=True).lower()
        if text and "area anchors" not in text and text not in area_names:
            area_names.append(text)
    return area_names

def parse_area_section(soup, area_name):
    """
    Search for a <p> tag that is likely the anchor for the given area.
    First, look for a <p> that has an <a> tag with a name attribute exactly matching area_name.
    If not found, fall back to any <p> whose text contains (or is contained by) area_name.
    Then, take the next table with class "dextable" and process it.
    Returns an HTML snippet with an H3 heading and the processed table.
    """
    area_p = None
    # Try to find a <p> with an <a name="..."> that equals area_name.
    for p_tag in soup.find_all("p"):
        a_tag = p_tag.find("a", attrs={"name": True})
        if a_tag and a_tag.get("name", "").lower() == area_name:
            area_p = p_tag
            break
    # If not found, try a fuzzy match.
    if not area_p:
        for p_tag in soup.find_all("p"):
            p_text = p_tag.get_text(strip=True).lower()
            if area_name in p_text or p_text in area_name:
                area_p = p_tag
                break
    if not area_p:
        return f"<p style='color:red;'>Could not find area: {area_name}</p>"
    area_table = area_p.find_next("table", class_="dextable")
    if not area_table:
        return f"<p style='color:red;'>No dextable found for {area_name}</p>"
    headers, rows = extract_table_data(area_table)
    table_html = build_table_html(headers, rows)
    section_html = (
        f"<h3 style='margin-bottom: 5px;'>{area_name.title()}</h3>\n"
        f"{table_html}\n"
        f"<div style='margin-bottom: 20px;'></div>"
    )
    return section_html

def extract_table_data(table):
    """
    Extract rows from the given table (skipping its header row) and reorder the columns into:
      No. | Pic | Name | Type | HP | Attack | Defence | Speed | Movement Range | Area Level | Trainers
    Pokémon names are delinked.
    """
    headers = [
        "No.",
        "Pic",
        "Name",
        "Type",
        "HP",
        "Attack",
        "Defence",
        "Speed",
        "Movement Range",
        "Area Level",
        "Trainers"
    ]
    data_rows = []
    all_rows = table.find_all("tr", recursive=False)
    data_trs = all_rows[1:]  # skip header row
    for tr in data_trs:
        cells = [child for child in tr.children if getattr(child, "name", None) == "td"]
        if len(cells) < 10:
            continue
        no_          = cells[0].get_text(strip=True)
        pic_html     = fix_images(cells[1])
        name_text    = cells[2].get_text(strip=True)
        type_html    = fix_images(cells[3])
        orig_hp      = cells[4].get_text(strip=True)
        orig_attack  = cells[5].get_text(strip=True)
        orig_defence = cells[6].get_text(strip=True)
        orig_speed   = cells[7].get_text(strip=True)
        orig_move    = cells[8].get_text(strip=True)
        orig_area    = fix_images(cells[9])  # process images in the Area Level column
        new_row = [
            no_,
            pic_html,
            name_text,
            type_html,
            orig_hp,
            orig_attack,
            orig_defence,
            orig_speed,
            orig_move,
            orig_area,
            ""  # Trainers (editable)
        ]
        data_rows.append(new_row)
    return headers, data_rows

def fix_images(cell_tag):
    """
    Converts the inner HTML of the cell using BeautifulSoup and
    prepends BASE_URL to any <img> tag's src that is not already absolute.
    If the src does not start with "http", a leading "/" is added if missing.
    """
    temp_soup = BeautifulSoup(cell_tag.decode_contents(), "html.parser")
    for img in temp_soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("http"):
            if not src.startswith("/"):
                src = "/" + src
            img["src"] = BASE_URL + src
    return temp_soup.decode()

def build_table_html(headers, rows):
    """
    Builds an HTML table with the provided headers and rows.
    The final column (Trainers) is set to be contenteditable.
    """
    html = []
    html.append('<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;">')
    html.append("<thead><tr>")
    for head in headers:
        html.append(f"<th>{head}</th>")
    html.append("</tr></thead>")
    html.append("<tbody>")
    for row in rows:
        html.append("<tr>")
        for col_index, cell_data in enumerate(row):
            if col_index == len(row) - 1:
                html.append(f'<td contenteditable="true" class="trainers-col">{cell_data}</td>')
            else:
                html.append(f"<td>{cell_data}</td>")
        html.append("</tr>")
    html.append("</tbody>")
    html.append("</table>")
    return "\n".join(html)

def localstorage_script(location):
    """
    Returns a JavaScript snippet that makes the Trainers column editable and
    persists changes using localStorage. The keys include the location name so that
    different output files save data independently.
    """
    return f"""<script>
document.addEventListener('DOMContentLoaded', function() {{
  const trainerCells = document.querySelectorAll('td.trainers-col');
  trainerCells.forEach((cell, i) => {{
    const key = 'trainers_cell_{location}_' + i;
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
