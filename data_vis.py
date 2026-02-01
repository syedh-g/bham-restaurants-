import sqlite3
import pandas as pd

conn = sqlite3.connect('restaurants_centre.db')

df = pd.read_sql_query("""
    SELECT COUNT(*) FROM restaurants 
""", conn)
print(df)

df = pd.read_sql_query("""
    SELECT name, rating, user_ratings_total FROM restaurants
    ORDER BY rating DESC, user_ratings_total DESC
    LIMIT 135
""", conn)
print(df)
conn.close()


