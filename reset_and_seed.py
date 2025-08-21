import sqlite3
import datetime

DB = "lfwms.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# === Step 1: Drop old tables if they exist
cur.executescript("""
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS food_listings;
DROP TABLE IF EXISTS receivers;
DROP TABLE IF EXISTS providers;
""")

# === Step 2: Recreate schema (correct structure)
cur.executescript("""
CREATE TABLE providers (
  Provider_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
  Provider_Name   TEXT NOT NULL,
  Provider_Type   TEXT NOT NULL,
  Location        TEXT,
  Contact         TEXT
);

CREATE TABLE receivers (
  Receiver_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
  Receiver_Name   TEXT NOT NULL,
  Receiver_Type   TEXT NOT NULL,
  Location        TEXT,
  Contact         TEXT
);

CREATE TABLE food_listings (
  Food_ID       INTEGER PRIMARY KEY AUTOINCREMENT,
  Food_Name     TEXT NOT NULL,
  Quantity      INTEGER NOT NULL,
  Expiry_Date   TEXT NOT NULL,
  Provider_ID   INTEGER,
  Provider_Type TEXT,
  Location      TEXT,
  Food_Type     TEXT,
  Meal_Type     TEXT,
  FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID)
);

CREATE TABLE claims (
  Claim_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
  Food_ID     INTEGER,
  Receiver_ID INTEGER,
  Claim_Date  TEXT NOT NULL,
  Status      TEXT NOT NULL,
  FOREIGN KEY(Food_ID) REFERENCES food_listings(Food_ID),
  FOREIGN KEY(Receiver_ID) REFERENCES receivers(Receiver_ID)
);
""")

# === Step 3: Insert demo Providers
providers = [
    ("FreshMart", "Supermarket", "Mumbai", "+91-9876543210"),
    ("City Hospital", "Hospital", "Delhi", "+91-8765432109"),
    ("GreenFarm", "NGO", "Bangalore", "+91-7654321098"),
    ("Star Hotel", "Restaurant", "Mumbai", "+91-6543210987"),
    ("Happy Foods", "Caterer", "Chennai", "+91-5432109876")
]
cur.executemany("INSERT INTO providers (Provider_Name, Provider_Type, Location, Contact) VALUES (?,?,?,?)", providers)

# === Step 4: Insert demo Receivers
receivers = [
    ("Hope Foundation", "NGO", "Mumbai", "+91-9123456780"),
    ("Helping Hands", "NGO", "Delhi", "+91-9234567890"),
    ("Food Bank", "NGO", "Bangalore", "+91-9345678901"),
    ("Sunrise Shelter", "Orphanage", "Chennai", "+91-9456789012")
]
cur.executemany("INSERT INTO receivers (Receiver_Name, Receiver_Type, Location, Contact) VALUES (?,?,?,?)", receivers)

# === Step 5: Insert demo Food Listings
today = datetime.date.today()
food_listings = [
    ("Rice Packets", 100, today + datetime.timedelta(days=5), 1, "Supermarket", "Mumbai", "Grain", "Lunch"),
    ("Vegetables", 50, today + datetime.timedelta(days=3), 3, "NGO", "Bangalore", "Veg", "Dinner"),
    ("Bread Loaves", 30, today + datetime.timedelta(days=2), 4, "Restaurant", "Mumbai", "Bakery", "Breakfast"),
    ("Milk Cartons", 200, today + datetime.timedelta(days=7), 2, "Hospital", "Delhi", "Dairy", "Breakfast"),
    ("Dal Packets", 80, today + datetime.timedelta(days=4), 5, "Caterer", "Chennai", "Grain", "Lunch")
]
cur.executemany("""
INSERT INTO food_listings 
(Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type) 
VALUES (?,?,?,?,?,?,?,?)""", food_listings)

# === Step 6: Insert demo Claims
claims = [
    (1, 1, today.isoformat(), "Pending"),
    (2, 2, today.isoformat(), "Completed"),
    (3, 3, today.isoformat(), "Pending"),
    (4, 1, today.isoformat(), "Cancelled")
]
cur.executemany("INSERT INTO claims (Food_ID, Receiver_ID, Claim_Date, Status) VALUES (?,?,?,?)", claims)

conn.commit()

# === Step 7: Show row counts
for table in ["providers", "receivers", "food_listings", "claims"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

print("\n✅ Database reset and seeded successfully.")
conn.close()
