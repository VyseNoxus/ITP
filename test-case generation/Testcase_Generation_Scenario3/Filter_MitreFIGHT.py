# === MITRE FiGHT Filtering Script for 5G Threat Hunting RAG DB ===

# Define relevant keywords for your project scope
keywords = [
    "5g", "nas", "ngap", "gtp", "sip", "ran", "core", "protocol",
    "flood", "crash", "overflow", "replay", "malformed", "tamper",
    "rogue", "ue", "mitm", "spoof", "evil twin", "injection", "denial"
]

# Load the scraped output
with open("mitre_techniques_output.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Split the raw text into blocks using separator
techniques = content.split("---")

# Filtered list to store shortlisted blocks
shortlisted = []

for block in techniques:
    lower_block = block.lower()
    if any(keyword in lower_block for keyword in keywords):
        shortlisted.append(block.strip())

# Save the filtered results into a new file
with open("shortlisted_mitre_fight.txt", "w", encoding="utf-8") as f:
    f.write("\n---\n".join(shortlisted))

print(f"Shortlisted {len(shortlisted)} MITRE FiGHT techniques saved to 'shortlisted_mitre_fight.txt'")
