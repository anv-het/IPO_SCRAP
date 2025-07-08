from pymongo import MongoClient

# MongoDB connection with authentication
client = MongoClient(
    "mongodb://sa:963852@192.168.102.120:27017"
)

# Select the database and collection
db = client["GETMASTERDATA"]
collection = db["MASTERDATA"]

# Query the data where Series = "EQ"
query = {"Series": "EQ"}

# Count the number of matching documents
count = collection.count_documents(query)

# Print the count of documents
print(f"Number of documents where Series = 'EQ': {count}")

# # Fetch all documents matching the query with projection to include only 'Name' and 'Series'
# documents = collection.find(query, {"Name": 1, "Series": 1, "_id": 0})

# # Print the results
# for document in documents:
#     # Print only the 'Name' and 'Series' columns
#     print(f"Name: {document['Name']}, Series: {document['Series']}")
