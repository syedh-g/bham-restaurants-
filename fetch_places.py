import requests
import time
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------- CONFIG ----------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")

MAX_REQUESTS = 300
request_count = 0

# ---------------------------------------

def nearby_search(lat, lng, radius=1000, pagetoken=None):
    global request_count
    if request_count >= MAX_REQUESTS:
        raise RuntimeError("Max request limit reached")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": API_KEY,
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "restaurant",
    }
    if pagetoken:
        params["pagetoken"] = pagetoken

    res = requests.get(url, params=params, timeout=10)
    request_count += 1

    data = res.json()

    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        return None

    return data

def fetch_all_pages(lat, lng):
    results = []

    page = nearby_search(lat, lng)
    if not page:
        return results

    results.extend(page.get("results", []))

    while "next_page_token" in page:
        time.sleep(2)

        page = nearby_search(lat, lng, pagetoken=page["next_page_token"])
        if not page or page.get("status") != "OK":
            break

        results.extend(page.get("results", []))

    return results

# Birmingham bounds
"""
BIRMINGHAM_BOUNDS = {
    "lat_min": 52.38,  # Includes Longbridge and Northfield
    "lat_max": 52.58,  # Includes Sutton Coldfield
    "lng_min": -2.03,  # Includes Quinton and Frankley
    "lng_max": -1.75,  # Includes Sheldon and Chelmsley Wood
}
"""

BIRMINGHAM_BOUNDS = {
    "lat_min": 52.462,  # Digbeth / South city centre
    "lat_max": 52.490,  # Jewellery Quarter / North city centre
    "lng_min": -1.905,  # Broad Street / Westside
    "lng_max": -1.870,  # Eastside / Bullring
}


def generate_grid(bounds, step=0.004):
    lats = np.arange(bounds["lat_min"], bounds["lat_max"], step)
    lngs = np.arange(bounds["lng_min"], bounds["lng_max"], step)
    return [(float(lat), float(lng)) for lat in lats for lng in lngs]

# ---------------- DB SETUP ----------------
engine = create_engine("sqlite:///restaurants_centre.db")

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS restaurants (
            place_id TEXT PRIMARY KEY,
            name TEXT,
            rating REAL,
            user_ratings_total INTEGER,
            lat REAL,
            lng REAL
        )
    """))

# ---------------- CRAWL ----------------
all_places = {}
grid = generate_grid(BIRMINGHAM_BOUNDS)

for lat, lng in grid:
    places = fetch_all_pages(lat, lng)
    for p in places:
        all_places[p["place_id"]] = p

print(f"Total API requests used: {request_count}")

# ---------------- CLEAN ----------------
rows = []
for p in all_places.values():
    if p.get("rating") and p.get("user_ratings_total", 0) >= 150:
        rows.append({
            "place_id": p["place_id"],
            "name": p["name"],
            "rating": p["rating"],
            "user_ratings_total": p["user_ratings_total"],
            "lat": p["geometry"]["location"]["lat"],
            "lng": p["geometry"]["location"]["lng"],
        })

df = pd.DataFrame(rows)

df.to_sql("restaurants", engine, if_exists="append", index=False)

# ---------------- VIS ----------------
import folium

m = folium.Map(location=[52.48, -1.89], zoom_start=12)

for _, r in df.iterrows():
    folium.CircleMarker(
        [r["lat"], r["lng"]],
        radius=4,
        popup=f"{r['name']} ({r['rating']})"
    ).add_to(m)

m.save('restaurants_map_centre.html')
print(f"Map saved to restaurants_map_centre.html")
print(f"Total restaurants found: {len(df)}")
