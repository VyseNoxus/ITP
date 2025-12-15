import re
import json

def extract_json_blocks(content):
    pattern = r'```json\n(.*?)\n```'
    return re.findall(pattern, content, re.DOTALL)

def fix_hex_length(hex_str, target_octets):
    hex_data = hex_str[2:]  # remove '0x'
    expected_len = target_octets * 2
    fixed = hex_data[:expected_len].ljust(expected_len, '0')
    return '0x' + fixed.upper()

def parse_octets(length_str):
    match = re.search(r"(\d+)", str(length_str))
    return int(match.group(1)) if match else None

def correct_test_cases(json_data):
    for case in json_data.get("test_cases", []):
        template = case.get("template", {})

        for ie in template.get("Mandatory Information Elements", []):
            value = ie.get("value")
            if isinstance(value, str) and value.startswith("0x"):
                hex_str = value
                hex_len = len(hex_str[2:])
                expected_octets = None

                match ie["name"]:
                    case "5GS Registration Type + ngKSI" | "ngKSI + Spare half octet" | "Service Type + ngKSI":
                        expected_octets = 1
                    case "ABBA":
                        expected_octets = 3
                    case "5G-S-TMSI":
                        expected_octets = 7

                if expected_octets and hex_len != expected_octets * 2:
                    ie["value"] = fix_hex_length(hex_str, expected_octets)

        for opt_ie in template.get("Optional Information Elements", []):
            length_str = opt_ie.get("length", "")
            expected_octets = parse_octets(length_str)
            value = opt_ie.get("value", "")
            if expected_octets is not None and isinstance(value, str) and value.startswith("0x"):
                hex_len = len(value[2:])
                if hex_len != expected_octets * 2:
                    opt_ie["value"] = fix_hex_length(value, expected_octets)

    return json_data

def sanitize_json_block(raw_block):
    cleaned = raw_block

    # Remove comments, ellipses, and extra commas
    cleaned = re.sub(r'//.*', '', cleaned)
    cleaned = re.sub(r'…|\.{3,}', '', cleaned)
    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
    cleaned = re.sub(r'"value"\s*:\s*,', '"value": "0x"', cleaned)
    cleaned = re.sub(r'(?<!\\)\\(?![\"/bfnrtu])', r'\\\\', cleaned)
    cleaned = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', cleaned)
    cleaned = re.sub(r'"\}\s*"(?![:,}])', '"}, "', cleaned)
    cleaned = re.sub(r'"\}\s*{', '"}, {', cleaned)

    # Replace invalid hex strings
    def fix_invalid_hex(match):
        val = match.group(1)
        hex_part = val[2:] if val.lower().startswith('0x') else val
        if not re.fullmatch(r'[0-9A-Fa-f]+', hex_part):
            return '"value": "0x' + '00'*16 + '"'
        return match.group(0)

    cleaned = re.sub(r'"value"\s*:\s*"([^"]+)"', fix_invalid_hex, cleaned)

    # Ensure it ends with final closing brace
    last_close_brace = cleaned.rfind('}')
    if last_close_brace != -1:
        cleaned = cleaned[:last_close_brace+1]

    return cleaned.strip()

# === Main ===

with open("nas_llm_raw_20250706_162511.txt", "r", encoding="utf-8") as f:
    content = f.read()

json_blocks = extract_json_blocks(content)
all_test_cases = {"test_cases": []}
invalid_blocks = []

for idx, raw_block in enumerate(json_blocks, start=1):
    block = sanitize_json_block(raw_block)
    try:
        data = json.loads(block)
        all_test_cases["test_cases"].extend(data["test_cases"])
    except json.JSONDecodeError as e:
        print(f"[!] Skipping invalid JSON block #{idx}: {e}")
        invalid_blocks.append((idx, raw_block))

# Save corrected test cases
with open("nas_testcases_fixed.json", "w", encoding="utf-8") as f:
    corrected_data = correct_test_cases(all_test_cases)
    json.dump(corrected_data, f, indent=2)

# Save invalid blocks
if invalid_blocks:
    with open("invalid_json_blocks.txt", "w", encoding="utf-8") as bad_file:
        for idx, block in invalid_blocks:
            bad_file.write(f"--- Block #{idx} ---\n{block}\n\n")

print(" Conversion complete. Output saved to nas_testcases_fixed.json")
if invalid_blocks:
    print(f"[!] {len(invalid_blocks)} invalid blocks were written to invalid_json_blocks.txt")
