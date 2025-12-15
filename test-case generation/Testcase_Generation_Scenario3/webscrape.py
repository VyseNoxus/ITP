from bs4 import BeautifulSoup

# Read the HTML file
with open('Techniques List _ MITRE FiGHT™.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Find all technique rows
technique_rows = soup.find_all('tr', class_='v-data-table__mobile-table-row')

# Prepare the output
output_lines = []

for row in technique_rows:
    # Extract ID
    id_cell = row.find('td', class_='v-data-table__mobile-row')
    if id_cell:
        id_link = id_cell.find('a')
        technique_id = id_link.get('id', '').strip() if id_link else ''

    # Extract Name
    name_cell = row.find_all('td', class_='v-data-table__mobile-row')[1] if len(
        row.find_all('td', class_='v-data-table__mobile-row')) > 1 else None
    if name_cell:
        name_link = name_cell.find('a')
        name = name_link.text.strip() if name_link else ''

    # Extract Description
    desc_cell = row.find_all('td', class_='v-data-table__mobile-row')[2] if len(
        row.find_all('td', class_='v-data-table__mobile-row')) > 2 else None
    if desc_cell:
        desc_div = desc_cell.find('div', class_='my-3')
        description = desc_div.text.strip() if desc_div else ''

    # Add to output if we have all fields
    if technique_id and name and description:
        output_lines.append(f"ID: {technique_id}")
        output_lines.append(f"Name: {name}")
        output_lines.append(f"Description: {description}")
        output_lines.append("-" * 80)  # Separator line

# Write to output file
with open('mitre_techniques_output.txt', 'w', encoding='utf-8') as out_file:
    out_file.write('\n'.join(output_lines))

print("Extraction complete. Results saved to mitre_techniques_output.txt")