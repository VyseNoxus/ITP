import json
import requests
from datetime import datetime
from typing import Dict, Any, List

class SecurityTestCaseGenerator:
    def __init__(
        self,
        protocol_template_file: str = "new_protocol_templates.json",
        technique_mapping_file: str = "technique_protocol_mapping_with_counts.json",
        llm_endpoint: str = "http://localhost:11434/api/generate",
        llm_model: str = "mistral",
    ):
        # Load protocol templates (expecting {"templates": {"nas": { … }, …}})
        with open(protocol_template_file, 'r', encoding='utf-8') as f:
            self.protocol_templates = json.load(f)["templates"]
        # Load MITRE FiGHT techniques
        with open(technique_mapping_file, 'r', encoding='utf-8') as f:
            self.techniques = json.load(f)["techniques"]
        self.llm_endpoint = llm_endpoint
        self.llm_model = llm_model

    def ask_llm(self, prompt: str, timeout: int = 2000) -> str:
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "max_tokens": 4000}
        }
        resp = requests.post(self.llm_endpoint, json=payload, timeout=timeout)
        return resp.json().get("response", "")

    def get_nas_templates(self) -> Dict[str, Any]:
        # Grab the entire "nas" block from your templates JSON
        return self.protocol_templates.get("nas", {})

    def get_nas_techniques(self) -> List[Dict]:
        return [t for t in self.techniques if t.get("protocol", "").lower() == "nas"]

    def _build_prompt(self, technique: Dict[str,Any], message_name: str, tmpl: Dict[str,Any]) -> str:
        pd   = tmpl["protocol_discriminator"]
        sht  = tmpl["security_header_type"]
        mhex = tmpl["message_type_hex"]
        mand = tmpl.get("Mandatory Information Elements", [])
        opt  = tmpl.get("Optional Information Elements", [])

        # Mandatory IE bullets
        mand_lines = []
        for m in mand:
            if m["name"] == "5GS Mobile Identity":
                mand_lines.append(f"- {m['name']}: use fixed SUCI `suci-0-208-93-0000000001`")
            else:
                iei = m.get("iei", "—")
                mand_lines.append(f"- {m['name']} (length {m['length']}): generate concrete 0x… hex")

        # Optional IE bullets
        opt_lines = [
            f"- {o['name']} (IEI {o.get('iei','—')}, length {o['length']}): generate concrete 0x… hex"
            for o in opt
        ]

        return f"""
You are a 5G security researcher.
Generate **5** adversarial **JSON-only** test cases for:
- Technique: {technique['id']} — {technique['name']}
- Message: {message_name} ({mhex})

Protocol Discriminator: `{pd}`,  Security Header Type: `{sht}`

Mandatory IEs (include **all**):
{chr(10).join(mand_lines)}

Optional IEs (choose **zero or more**, cover each at least once):
{chr(10).join(opt_lines)}

**Rules:**
1) **JSON-only** output, no extra prose.
2) All hex fields must match their octet counts:
   - 1 octet → 2 hex digits (e.g. `0xA2`)
   - 2 octets → 4 hex digits (e.g. `0x1234`)
3) **Mandatory IEs:**
   - Each case must include **all** Mandatory IEs listed above.
   - Use exact field names and lengths; e.g.  
     `"name": "ngKSI + Spare half octet", "value": "0xA1"`.
4) **Optional IEs:**
   - A case may include **zero** or **more** Optional IEs.
   - When included, pick from the list above and generate a valid `0x…` value.
5) No placeholders (`"<…>"`) may remain.
6) Follow **3GPP TS 24.501** TLV encoding.
7) If any rule is violated, regenerate that case.

**Output JSON schema exactly (no extra text):**

{{
  "test_cases": [
    {{
      "case_id": "1",
      "message_name": "{message_name}",
      "mitre_fight_id": "{technique['id']}",
      "attack_description": "…",
      "affected_elements": ["…"],
      "protocol_discriminator": "{pd}",
      "security_header_type": "{sht}",
      "message_type_hex": "{mhex}",
      "Mandatory Information Elements": [
        {{ "name": "...", "value": "0x…" }},
        …
      ],
      "Optional Information Elements": [
        {{ "name": "...", "iei": "0xXX", "length": "N octets", "value": "0x…" }},
        …
      ]
    }},
    …
  ]
}}
""".strip()

    def dump_all_raw(self, out_file: str):
        nas_templates  = self.get_nas_templates()
        nas_techniques = self.get_nas_techniques()

        with open(out_file, "w", encoding="utf-8") as f:
            f.write("=== RAW LLM OUTPUTS FOR NAS TEMPLATES ===\n\n")
            for message_name, tmpl in nas_templates.items():
                for tech in nas_techniques:
                    prompt = self._build_prompt(tech, message_name, tmpl)
                    response = self.ask_llm(prompt)
                    print(f"--- PROMPT for {tech['id']} + {message_name} ---\n{prompt}\n")
                    print(f"--- RESPONSE ---\n{response}\n")
                    f.write(f"### {tech['id']} - {message_name}\n")
                    f.write(response + "\n\n")

        print(f"✅ Dumped all raw LLM outputs to {out_file}")

if __name__ == "__main__":
    gen = SecurityTestCaseGenerator()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"nas_llm_raw_{ts}.txt"
    gen.dump_all_raw(out_filename)
    print(f"✅ All done, raw outputs in {out_filename}")
