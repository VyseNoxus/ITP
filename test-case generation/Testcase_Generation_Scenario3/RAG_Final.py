import json
import chromadb
import time

# === STEP 1: Load the test cases JSON file ===
# This loads the pre-cleaned NAS protocol test cases from a JSON file.
print("[*] Loading JSON data from 'nas_testcases_fixed.json'...")
with open("nas_testcases_fixed.json", "r", encoding="utf-8") as f:
    data = json.load(f)
test_cases = data.get("test_cases", [])
print(f"[✓] Loaded {len(test_cases)} test cases.")

# === Utility Function: Convert each JSON test case to plain text string ===
# This is used as input to ChromaDB. It helps index text from structured JSON.
def json_to_text(doc):
    fields = [
        doc.get("protocol", ""),
        doc.get("message_name", ""),
        doc.get("attack_description", ""),
        doc.get("message_type_hex", ""),
        doc.get("mitre_fight_id", "")
    ]
    return " ".join(fields)

# === Utility Function: Prepare metadata for ChromaDB storage ===
# Nested fields are serialized into strings to ensure metadata is valid
def sanitize_metadata(doc):
    return {
        k: json.dumps(v) if isinstance(v, (list, dict)) else v
        for k, v in doc.items()
        if v is not None and v != ""
    }

# === STEP 2: Sanitize and prepare test cases for ingestion ===
print("[*] Sanitizing and preparing documents...")
documents, metadatas, ids, valid_docs, invalid_docs = [], [], [], [], []

for i, doc in enumerate(test_cases):
    doc_id = f"doc_{i+1}"

    # Validate JSON format
    if doc is None or not isinstance(doc, dict):
        invalid_docs.append({
            "id": doc_id,
            "reason": "Invalid: Not a dictionary or null.",
            "document": str(doc)
        })
        continue

    meta = sanitize_metadata(doc)

    # Only ingest valid documents with proper metadata
    if meta:
        documents.append(json_to_text(doc))
        metadatas.append(meta)
        ids.append(doc_id)
        valid_docs.append(doc)
    else:
        invalid_docs.append({
            "id": doc_id,
            "reason": "Invalid: Metadata empty or malformed.",
            "document": doc
        })

print(f"[✓] Prepared {len(valid_docs)} valid test cases for ingestion.")
print(f"[!] Skipped {len(invalid_docs)} invalid test cases.")

# === STEP 3: Store valid test cases into ChromaDB ===
print("[*] Connecting to ChromaDB...")
client = chromadb.Client()
collection = client.get_or_create_collection(name="nas_testcases_collection")

# Only upsert if collection is empty (to prevent duplicates)
if collection.count() == 0:
    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
    print(f"[✓] {len(documents)} documents successfully stored in ChromaDB.")
else:
    print(f"[✓] ChromaDB already contains {collection.count()} documents. Skipping ingestion.")

# === STEP 4: Save valid and invalid test cases to JSON for auditing ===
with open("extracted_nas_testcases.json", "w", encoding="utf-8") as f:
    json.dump([{"id": ids[i], "document": valid_docs[i]} for i in range(len(valid_docs))], f, indent=2, ensure_ascii=False)
    print("[✓] Extracted valid test cases saved to 'extracted_nas_testcases.json'.")

# Note: Some invalid test cases show as `document: {}` because their metadata fields were empty or non-serializable.
# These were filtered by `sanitize_metadata()` to prevent ingestion corruption.
# For audit purposes, their count and reasons are printed in the terminal log.
with open("invalid_testcases.json", "w", encoding="utf-8") as f:
    json.dump(invalid_docs, f, indent=2, ensure_ascii=False)
    print("[!] Invalid test cases saved to 'invalid_testcases.json'.")

# === STEP 5: Load extracted test cases back for querying ===
print("[*] Loading extracted test cases...")
with open("extracted_nas_testcases.json", "r", encoding="utf-8") as f:
    test_cases = json.load(f)
print(f"[✓] Loaded {len(test_cases)} extracted test cases.\n")

# === STEP 6: Prompt user for protocol query (e.g., 'nas') ===
user_protocol = input("Enter protocol to query (e.g., 'nas'): ").strip().lower()

# === STEP 7: Perform the retrieval based on user input ===
print(f"\n[*] Retrieving test cases for protocol = '{user_protocol}'...\n")
start_time = time.time()

# Match all test cases with protocol matching user query
matching_cases = []
for entry in test_cases:
    doc_id = entry.get("id", "unknown_case")
    doc = entry.get("document", {})

    # Ensure valid JSON and protocol match
    if isinstance(doc, dict) and doc.get("protocol", "").strip().lower() == user_protocol:
        try:
            json.dumps(doc)
            matching_cases.append({"id": doc_id, "document": doc})
        except Exception as e:
            print(f"[!] Skipping malformed test case {doc_id}: {e}")

# === STEP 8: Display results and save to file ===
if not matching_cases:
    print(f"[!] No test cases found for protocol '{user_protocol}'.")
else:
    for entry in matching_cases:
        print(f"Case ID: {entry['id']}\n{'-'*50}")
        print(json.dumps(entry["document"], indent=2, ensure_ascii=False))
        print(f"{'-'*50}\n")

    duration = round(time.time() - start_time, 2)
    print(f"[✓] Retrieved {len(matching_cases)} test case(s) in {duration}s.")

    # Save retrieved results to a new file
    output_filename = f"retrieved_results_{user_protocol}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(matching_cases, f, indent=2, ensure_ascii=False)
    print(f"[✓] Saved retrieved results to '{output_filename}'")


