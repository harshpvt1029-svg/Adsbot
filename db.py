from pymongo.mongo_client import MongoClient

# Hardcoded MongoDB URI (replace with environment variable later for safety)
MONGO_URI = "mongodb+srv://saritabai808_db_user:YVOkMFOv2vxoxo4k@cluster0.dwtlbfm.mongodb.net/cosmic_ads?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client.get_database()  # defaults to the database in URI

def ping_db():
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)
