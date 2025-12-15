import json
import chromadb
import time
import os

# === STEP 1: Load NAS and NGAP test cases from two separate JSON files ===
# These files contain test case data generated
with open("nas_testcases_fixed.json", "r", encoding="utf-8") as f:
    nas_data = json.load(f).get("test_cases", [])

with open("ngap_testcaseV3.json", "r", encoding="utf-8") as f:
    ngap_data = json.load(f).get("test_cases", [])

# Combine NAS and NGAP data into a single list for unified ingestion into the RAG DB
combined_data = nas_data + ngap_data
print(f"[✓] Loaded {len(nas_data)} NAS and {len(ngap_data)} NGAP test cases.")

# === STEP 2: Convert each JSON test case into plain text for embedding ===
def json_to_text(doc):
    """
    Converts structured test case JSON into a flat string for semantic search embedding.
    """
    return " ".join([
        doc.get("protocol", ""),
        doc.get("message_name", ""),
        doc.get("attack_description", ""),
        doc.get("message_type_hex", ""),
        doc.get("mitre_fight_id", "")
    ])

# === STEP 3: Sanitize metadata for ChromaDB ingestion ===
def sanitize_metadata(doc):
    """
    Prepares metadata dictionary by converting complex structures to strings.
    Skips null/empty values to ensure clean ingestion.
    """
    meta = {
        k: json.dumps(v) if isinstance(v, (list, dict)) else v
        for k, v in doc.items()
        if v is not None and v != ""
    }
    return meta if meta else None

# === STEP 4: Prepare documents, metadata, and IDs for ingestion ===
documents, metadatas, ids = [], [], []
extracted_all = []
skipped_docs = 0  # To count and log skipped documents

for i, doc in enumerate(combined_data):
    metadata = sanitize_metadata(doc)
    if metadata is None:
        skipped_docs += 1  # Document is skipped if metadata is empty
        continue

    doc_id = f"doc_{len(ids)+1}"
    documents.append(json_to_text(doc))
    metadatas.append(metadata)
    ids.append(doc_id)
    extracted_all.append({"id": doc_id, "document": doc})

# Logging total processed and skipped
total_loaded = len(combined_data)
total_ingested = len(documents)
print(f"[✓] Total test cases loaded: {total_loaded}")
print(f"[✓] {total_ingested} test cases ingested into ChromaDB.")
if skipped_docs > 0:
    print(f"[!] Skipped {skipped_docs} test case(s) due to missing or empty metadata fields.")

# === STEP 5: Connect to ChromaDB with persistent storage ===
# This ensures that previously ingested data remains in the collection across runs
print("[*] Connecting to ChromaDB with persistent storage...")
chroma_path = os.path.join(os.getcwd(), "chroma_db")
client = chromadb.PersistentClient(path=chroma_path)

# Create or get the persistent collection for protocol test cases
collection = client.get_or_create_collection(name="protocol_testcases")

# Only ingest if collection is empty (to avoid duplication)
if collection.count() == 0:
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[✓] {len(documents)} test cases ingested into ChromaDB.")
else:
    print(f"[✓] ChromaDB already has {collection.count()} documents. Skipping ingestion.")

# === STEP 6: Save all extracted test cases to a file for transparency/debugging ===
with open("extracted_protocol_testcases.json", "w", encoding="utf-8") as f:
    json.dump(extracted_all, f, indent=2, ensure_ascii=False)
    print("[✓] Extracted NAS and NGAP test cases saved to 'extracted_protocol_testcases.json'.")

# === STEP 7: Prompt user to input protocol to retrieve relevant test cases ===
user_protocol = input("\nEnter protocol to query (e.g., 'nas' or 'ngap'): ").strip().lower()

# === STEP 8: Filter results based on the specified protocol ===
with open("extracted_protocol_testcases.json", "r", encoding="utf-8") as f:
    results = json.load(f)

print(f"\n[*] Retrieving test cases for protocol = '{user_protocol}'...\n")
start = time.time()

# Perform exact match filtering by 'protocol' field
matching = [r for r in results if r["document"].get("protocol", "").lower() == user_protocol]

# === STEP 9: Output the results of the protocol-based query ===
if not matching:
    print(f"[!] No test cases found for protocol '{user_protocol}'.")
else:
    for r in matching:
        print(f"Case ID: {r['id']}\n{'-'*50}")
        print(json.dumps(r["document"], indent=2, ensure_ascii=False))
        print(f"{'-'*50}\n")

    duration = round(time.time() - start, 2)
    print(f"[✓] Retrieved {len(matching)} test case(s) in {duration}s.")

    out_file = f"retrieved_results_{user_protocol}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matching, f, indent=2, ensure_ascii=False)
    print(f"[✓] Results saved to '{out_file}'.")
