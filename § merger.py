import os
from bs4 import BeautifulSoup

# ============================================================
# EDITABLE VARIABLES:
# Specify the output HTML file and the input directory paths here.
# ============================================================
OUTPUT_FILE = "/Users/nicholaschang/Helpful Scripts/conquest parse/merged.html"
INPUT_DIR = "/Users/nicholaschang/Helpful Scripts/conquest parse/conquest_locations"

def merge_html_files(input_dir, output_file):
    """
    Merges ALL content from each HTML file in the input directory into a single file.
    Each file's raw HTML (including any <html>/<head>/<body> tags)
    is placed inside a <div> in one big <body>.
    
    This preserves all data, though the resulting file may not be strictly valid HTML
    if multiple <html> or <head> tags are present.
    """
    # 1) Start with a DOCTYPE + minimal skeleton
    base_html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>Merged HTML</title>
</head>
<body>
</body>
</html>"""
    merged_soup = BeautifulSoup(base_html, "html.parser")
    merged_body = merged_soup.body

    # 2) Get a list of all .html files in the input directory
    file_names = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.html')])
    
    # 3) Loop through each file and merge its content
    for file_name in file_names:
        file_path = os.path.join(input_dir, file_name)
        if not os.path.isfile(file_path):
            print(f"[WARNING] File not found: {file_path}")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            file_data = f.read()

        # Create a wrapper <div> to hold the entire content of this file
        wrapper_div = merged_soup.new_tag("div", **{"class": "merged-file"})

        # Optional: Add comments to mark the start and end of each file's content
        start_comment = merged_soup.new_string(f"<!-- START of {file_name} -->")
        end_comment = merged_soup.new_string(f"<!-- END of {file_name} -->")
        
        wrapper_div.append(start_comment)
        
        # Parse the file’s HTML and append all its top-level elements
        file_soup = BeautifulSoup(file_data, "html.parser")
        for child in file_soup.contents:
            wrapper_div.append(child)
        
        wrapper_div.append(end_comment)
        merged_body.append(wrapper_div)

    # 4) Write the merged HTML to the output file
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(str(merged_soup))

    print(f"[INFO] Successfully merged {len(file_names)} files into: {output_file}")

if __name__ == "__main__":
    print("Merging HTML files...")
    merge_html_files(INPUT_DIR, OUTPUT_FILE)
    print(f"Done! Created merged file: {OUTPUT_FILE}")
