# Birmingham Restaurants Crawler

This project uses the Google Places API to collect restaurant data in Birmingham, UK,
filter by review count, store results in a SQLite database, and visualize them on a map.

## Features

- Grid-based restaurant search using Google Places API
- Deduplication via `place_id`
- Review cutoff filter 
- SQLite database storage
- Interactive map visualization with Folium
- Request limit safety cap to control API cost

