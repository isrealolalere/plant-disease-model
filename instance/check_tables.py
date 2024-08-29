import sqlite3

# Path to your SQLite database file
db_path = 'user_database.db'  # Adjust the path if necessary

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query to check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(table[0])

# Close the connection
conn.close()
