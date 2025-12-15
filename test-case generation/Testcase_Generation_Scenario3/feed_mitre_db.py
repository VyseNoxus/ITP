import json
import chromadb  # Import the ChromaDB library for vector database handling

# Step 1: Load MITRE Techniques JSON File
# This reads the MITRE techniques data from a local JSON file and stores it as a Python list of dictionaries
with open("mitre_techniques (1).json", "r", encoding="utf-8") as file:
    mitre_data = json.load(file)

# Step 2: Initialize ChromaDB client and create a collection to store MITRE techniques
client = chromadb.Client()  # Initializes an in-memory Chroma client
collection = client.create_collection(name="mitre_techniques")  # Creates a new collection named 'mitre_techniques'

# Step 3: Add techniques to collection
# Prepare lists of IDs, descriptions (as documents), and metadata for each technique
ids = []
documents = []
metadatas = []

# Loop through each technique entry in the original JSON and organize it for ChromaDB ingestion
for technique in mitre_data:
    ids.append(technique["ID"])  # Unique identifier for each entry
    documents.append(technique["Description"])  # Main searchable text content
    metadatas.append({
        "Name": technique["Name"],  # Additional metadata
        "ID": technique["ID"]
    })

# Add all techniques into the Chroma collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

# Step 4: Retrieve all stored data from the ChromaDB collection
results = collection.get()

# Prepare the output in the same structure as the original JSON
output_json = []
for i in range(len(results["ids"])):
    output_json.append({
        "ID": results["metadatas"][i]["ID"],
        "Name": results["metadatas"][i]["Name"],
        "Description": results["documents"][i]
    })

# Step 5: Save the retrieved data to a new JSON file
# This demonstrates successful extraction and conversion back into the original format
with open("retrieved_mitre_techniques.json", "w", encoding="utf-8") as outfile:
    json.dump(output_json, outfile, indent=4)

# Final confirmation message
print(" MITRE techniques stored and retrieved successfully.")
