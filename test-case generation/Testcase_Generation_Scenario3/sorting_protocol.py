import re
import json
from collections import defaultdict

# Protocol mapping rules (keywords and patterns)
protocol_rules = {
    'NAS': [
        r'NAS\b',
        r'Non-Access Stratum',
        r'registration request',
        r'attach procedure',
        r'paging message',
        r'SUCI',
        r'SUPI',
        r'5G-GUTI',
        r'authentication material'
    ],
    'NGAP': [
        r'NGAP\b',
        r'AMF',
        r'gNB',
        r'core network function',
        r'NRF',
        r'Service Based Interface',
        r'SBI'
    ],
    'RRC': [
        r'RRC\b',
        r'Radio Resource Control',
        r'radio interface',
        r'air interface',
        r'base station',
        r'gNB',
        r'measurement report',
        r'broadcast message',
        r'bidding down',
        r'UE measurement'
    ],
    'GTP': [
        r'GTP\b',
        r'GTP-U',
        r'GTP-C',
        r'TEID',
        r'user plane',
        r'UPF',
        r'PGW-U',
        r'tunnel endpoint',
        r'user plane function'
    ]
}


def count_keyword_occurrences(description, protocol):
    """Count occurrences of each keyword for a protocol in the description"""
    counts = defaultdict(int)
    description_lower = description.lower()

    for pattern in protocol_rules[protocol]:
        # Count all non-overlapping matches
        matches = re.findall(pattern.lower(), description_lower)
        counts[pattern] += len(matches)

    return dict(counts)


def map_technique_to_protocol(description):
    """Determine the protocol based on technique description with keyword counts"""
    description_lower = description.lower()
    protocol_matches = defaultdict(dict)

    for protocol, patterns in protocol_rules.items():
        pattern_counts = defaultdict(int)
        for pattern in patterns:
            matches = re.findall(pattern.lower(), description_lower)
            pattern_counts[pattern] = len(matches)

        if any(pattern_counts.values()):  # Only include if any matches
            protocol_matches[protocol] = dict(pattern_counts)

    # Determine primary protocol (most matches)
    if protocol_matches:
        primary_protocol = max(protocol_matches.keys(),
                               key=lambda k: sum(protocol_matches[k].values()))
        return primary_protocol, protocol_matches
    return 'OTHER', {}


def parse_techniques_file(file_content):
    """Parse the techniques file and map each to a protocol with keyword counts"""
    techniques = []
    current_tech = {}

    for line in file_content.split('\n'):
        if line.startswith('ID:'):
            if current_tech:  # Save previous technique if exists
                techniques.append(current_tech)
            current_tech = {
                'id': line.split('ID:')[1].strip(),
                'name': '',
                'description': '',
                'protocol': 'OTHER',
                'protocol_matches': {}
            }
        elif line.startswith('Name:'):
            current_tech['name'] = line.split('Name:')[1].strip()
        elif line.startswith('Description:'):
            current_tech['description'] = line.split('Description:')[1].strip()
        elif line.strip() == '--------------------------------------------------------------------------------':
            if current_tech and current_tech['description']:
                protocol, matches = map_technique_to_protocol(current_tech['description'])
                current_tech['protocol'] = protocol
                current_tech['protocol_matches'] = matches
                techniques.append(current_tech)
                current_tech = {}

    # Add the last technique if exists
    if current_tech and current_tech.get('description'):
        protocol, matches = map_technique_to_protocol(current_tech['description'])
        current_tech['protocol'] = protocol
        current_tech['protocol_matches'] = matches
        techniques.append(current_tech)

    return techniques


def generate_json_output(techniques):
    """Generate enhanced JSON output with protocol mappings and keyword statistics"""
    # Calculate global keyword frequencies
    global_keyword_stats = defaultdict(lambda: defaultdict(int))

    for tech in techniques:
        for protocol, matches in tech['protocol_matches'].items():
            for keyword, count in matches.items():
                global_keyword_stats[protocol][keyword] += count

    return {
        'metadata': {
            'protocols': ['NAS', 'NGAP', 'RRC', 'GTP', 'OTHER'],
            'total_techniques': len(techniques),
            'technique_counts': {
                'NAS': len([t for t in techniques if t['protocol'] == 'NAS']),
                'NGAP': len([t for t in techniques if t['protocol'] == 'NGAP']),
                'RRC': len([t for t in techniques if t['protocol'] == 'RRC']),
                'GTP': len([t for t in techniques if t['protocol'] == 'GTP']),
                'OTHER': len([t for t in techniques if t['protocol'] == 'OTHER'])
            },
            'keyword_frequencies': {
                protocol: dict(keywords)
                for protocol, keywords in global_keyword_stats.items()
            }
        },
        'techniques': techniques
    }


if __name__ == "__main__":
    with open('mitre_techniques_output.txt', 'r') as file:
        content = file.read()

    techniques = parse_techniques_file(content)
    json_output = generate_json_output(techniques)

    # Print sample output
    print("Sample JSON output (metadata only):")
    print(json.dumps(json_output['metadata'], indent=2))

    # Save to JSON file
    with open('technique_protocol_mapping_with_counts.json', 'w') as jsonfile:
        json.dump(json_output, jsonfile, indent=2)

    print("\nFull output saved to 'technique_protocol_mapping_with_counts.json'")