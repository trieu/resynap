
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
load_dotenv(override=True)

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# the query for google search engine
query = "Sigmund Freud and CARL JUNG"

def google_search(query, api_key, search_engine_id, num_results=10):
    service = build("customsearch", "v1", developerKey=api_key)
    result = service.cse().list(q=query, cx=search_engine_id, num=num_results).execute()
    return result.get("items", [])

# Perform the search
results = google_search(query, GOOGLE_SEARCH_API_KEY, SEARCH_ENGINE_ID)

# Print results
for idx, item in enumerate(results):
    print(f"{idx+1}. {item['title']}")
    print(f"   {item['link']}\n")