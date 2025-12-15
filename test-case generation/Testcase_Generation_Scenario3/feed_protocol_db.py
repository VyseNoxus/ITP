import json
import chromadb

# Step 1: Load the protocol database JSON file
with open("protocol_database.json", "r", encoding="utf-8") as file:
    protocol_data = json.load(file)

# Step 2: Initialize ChromaDB client
client = chromadb.Client()
collection = client.create_collection(name="protocol_templates")

# Step 3: Store only the 'templates' section into ChromaDB
ids = []
documents = []
metadatas = []

for idx, (msg_name, details) in enumerate(protocol_data["templates"].items()):
    doc = json.dumps(details["template"], indent=2)  # Store the 'template' dict as a JSON string
    ids.append(f"protocol_{idx}")
    documents.append(doc)
    metadatas.append({
        "message_name": details["message_name"],
        "protocol_type": details["protocol_type"],
        "message_type_hex": details["message_type_hex"]
    })

# Step 4: Add templates to ChromaDB collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

# Step 5: Retrieve and format stored templates
results = collection.get()
retrieved_templates = []

for i in range(len(results["ids"])):
    retrieved_templates.append({
        "id": results["ids"][i],
        "message_name": results["metadatas"][i]["message_name"],
        "protocol_type": results["metadatas"][i]["protocol_type"],
        "message_type_hex": results["metadatas"][i]["message_type_hex"],
        "template": json.loads(results["documents"][i])
    })

# Step 6: Write retrieved templates to file
with open("retrieved_protocol_templates.json", "w", encoding="utf-8") as outfile:
    json.dump(retrieved_templates, outfile, indent=4)

# Step 7: Also write message_type_reference to separate file
# Since it is a dictionary and not suitable for direct storage in vector DBs. It should be exported separately.
with open("retrieved_protocol_reference.json", "w", encoding="utf-8") as ref_out:
    json.dump({"message_type_reference": protocol_data["message_type_reference"]}, ref_out, indent=4)


print(" Protocol templates and message type references stored and retrieved successfully.")

