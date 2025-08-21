# seed_data.py
import sqlite3
from datetime import date, timedelta

DB = "lfwms.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# --- 1) Ensure tables exist (safe if they already do) ---
cur.executescript("""
CREATE TABLE IF NOT EXISTS providers (
  Provider_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
  Provider_Name TEXT NOT NULL,
  Provider_Type TEXT NOT NULL,
  Location      TEXT,
  Contact       TEXT
);

CREATE TABLE IF NOT EXISTS receivers (
  Receiver_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
  Receiver_Name TEXT NOT NULL,
  Receiver_Type TEXT NOT NULL,
  Location      TEXT,
  Contact       TEXT
);

CREATE TABLE IF NOT EXISTS food_listings (
  Food_ID       INTEGER PRIMARY KEY AUTOINCREMENT,
  Food_Name     TEXT NOT NULL,
  Quantity      INTEGER NOT NULL,
  Expiry_Date   TEXT NOT NULL,     -- 'YYYY-MM-DD'
  Provider_ID   INTEGER,
  Provider_Type TEXT,
  Location      TEXT,
  Food_Type     TEXT,
  Meal_Type     TEXT,
  FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID)
);

CREATE TABLE IF NOT EXISTS claims (
  Claim_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
  Food_ID     INTEGER,
  Receiver_ID INTEGER,
  Claim_Date  TEXT NOT NULL,
  Status      TEXT NOT NULL,
  FOREIGN KEY(Food_ID) REFERENCES food_listings(Food_ID),
  FOREIGN KEY(Receiver_ID) REFERENCES receivers(Receiver_ID)
);
""")

def ensure_column(table, col, decl):
    cur.execute("PRAGMA table_info(%s)" % table)
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")

# Make sure app-required columns exist
ensure_column("food_listings", "Food_Type", "TEXT")
ensure_column("food_listings", "Meal_Type", "TEXT")
ensure_column("food_listings", "Provider_Type", "TEXT")

# --- 2) Seed providers (skip by name if already present) ---
providers = [
    ("GreenHarvest Restaurant", "Restaurant", "Bengaluru", "080-111-222"),
    ("CityCare NGO",               "NGO",        "Delhi",      "011-234-567"),
    ("Sunrise Bakery",             "Bakery",     "Pune",       "020-555-222"),
    ("FreshMart Supermarket",      "Supermarket","Mumbai",     "022-888-111"),
    ("Lotus Hotel",                "Hotel",      "Chennai",    "044-909-101"),
    ("Campus Community Kitchen",   "Community",  "Hyderabad",  "040-303-909"),
    ("Coastal Caterers",           "Caterer",    "Kochi",      "0484-303-000"),
    ("ByteWorks Cafeteria",        "Corporate",  "Noida",      "0120-787-888"),
]

cur.execute("SELECT Provider_Name, Provider_ID, Provider_Type FROM providers")
existing_prov = {name: (pid, ptype) for name, pid, ptype in cur.fetchall()}

for name, ptype, loc, contact in providers:
    if name not in existing_prov:
        cur.execute(
            "INSERT INTO providers (Provider_Name, Provider_Type, Location, Contact) VALUES (?,?,?,?)",
            (name, ptype, loc, contact)
        )

# Refresh map
cur.execute("SELECT Provider_Name, Provider_ID, Provider_Type, Location FROM providers")
prov_rows = cur.fetchall()
prov_by_name = {r[0]: {"id": r[1], "type": r[2], "location": r[3]} for r in prov_rows}

# --- 3) Seed receivers (skip by name if already present) ---
receivers = [
    ("Food For All Trust", "NGO", "Delhi", "011-101-202"),
    ("Shelter+ Night Home", "Shelter", "Mumbai", "022-343-454"),
    ("Govt School #77", "School", "Bengaluru", "080-787-909"),
    ("Hope Food Bank", "Food Bank", "Pune", "020-202-303"),
    ("Mother’s Care Orphanage", "Orphanage", "Chennai", "044-990-880"),
    ("StreetCare Foundation", "NGO", "Hyderabad", "040-212-313"),
]

cur.execute("SELECT Receiver_Name FROM receivers")
existing_recv = {r[0] for r in cur.fetchall()}

for name, rtype, loc, contact in receivers:
    if name not in existing_recv:
        cur.execute(
            "INSERT INTO receivers (Receiver_Name, Receiver_Type, Location, Contact) VALUES (?,?,?,?)",
            (name, rtype, loc, contact)
        )

# Map receiver names to IDs
cur.execute("SELECT Receiver_Name, Receiver_ID FROM receivers")
recv_by_name = {name: rid for name, rid in cur.fetchall()}

# --- 4) Seed food listings (attach to real providers) ---
today = date.today()
def d(days): return (today + timedelta(days=days)).isoformat()

food_samples = [
    # (Food_Name, Quantity, Expiry(±days), ProviderName, Food_Type, Meal_Type, Location_override_or_None)
    ("Veg Pulao Trays", 50,  2, "GreenHarvest Restaurant", "Vegetarian", "Lunch", None),
    ("Bread Loaves",    80,  1, "Sunrise Bakery",          "Vegetarian", "Breakfast", None),
    ("Fruit Baskets",   30,  5, "FreshMart Supermarket",   "Vegetarian", "Snack", "Mumbai"),
    ("Cooked Rice",    120,  2, "Campus Community Kitchen","Vegetarian", "Lunch", None),
    ("Chicken Curry",   60,  2, "Lotus Hotel",             "Non-Vegetarian", "Dinner", None),
    ("Veg Sandwiches", 100,  1, "ByteWorks Cafeteria",     "Vegetarian", "Snack", None),
    ("Samosa Packs",    90,  1, "GreenHarvest Restaurant", "Vegetarian", "Snack", None),
    ("Curd Cups",      150,  3, "FreshMart Supermarket",   "Vegetarian", "Lunch", "Mumbai"),
    ("Dal Tadka",       70,  2, "Coastal Caterers",        "Vegetarian", "Dinner", None),
    ("Idli Packs",     110,  1, "Lotus Hotel",             "Vegetarian", "Breakfast", None),
    ("Pastry Boxes",    40,  1, "Sunrise Bakery",          "Vegetarian", "Dessert", None),
    ("Veg Biryani",     75,  2, "GreenHarvest Restaurant", "Vegetarian", "Dinner", None),
    ("Chapati Bundles",200,  2, "Campus Community Kitchen","Vegetarian", "Dinner", None),
    ("Salad Bowls",     60,  2, "ByteWorks Cafeteria",     "Vegetarian", "Lunch", None),
    ("Fish Curry",      40,  1, "Coastal Caterers",        "Non-Vegetarian", "Dinner", None),
]

# Avoid duplicating exact same (name + provider + expiry)
cur.execute("SELECT Food_Name, Provider_ID, Expiry_Date FROM food_listings")
existing_keys = {(n, pid, e) for (n, pid, e) in cur.fetchall()}

for name, qty, delta, prov_name, ftype, mtype, loc_override in food_samples:
    if prov_name not in prov_by_name: 
        continue
    pid = prov_by_name[prov_name]["id"]
    ptype = prov_by_name[prov_name]["type"]
    loc = loc_override or prov_by_name[prov_name]["location"]
    exp = d(delta)
    key = (name, pid, exp)
    if key in existing_keys:
        continue
    cur.execute("""
        INSERT INTO food_listings
        (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
        VALUES (?,?,?,?,?,?,?,?)
    """, (name, qty, exp, pid, ptype, loc, ftype, mtype))

# --- 5) Seed claims for some of the latest listings ---
# Pick the 8 most recent (by Expiry_Date) and create claims to different receivers
cur.execute("""
    SELECT Food_ID FROM food_listings
    ORDER BY DATE(Expiry_Date) DESC, Food_ID DESC
    LIMIT 8
""")
food_ids = [r[0] for r in cur.fetchall()]
recv_cycle = list(recv_by_name.values()) or [None]

statuses = ["Pending", "Approved", "Completed"]
i = 0
for fid in food_ids:
    rid = recv_cycle[i % len(recv_cycle)]
    claim_dt = today.isoformat()
    status = statuses[i % len(statuses)]
    # Skip if an identical claim already exists
    cur.execute("SELECT 1 FROM claims WHERE Food_ID=? AND Receiver_ID=?", (fid, rid))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO claims (Food_ID, Receiver_ID, Claim_Date, Status) VALUES (?,?,?,?)",
            (fid, rid, claim_dt, status)
        )
    i += 1

conn.commit()

# --- 6) Print quick totals ---
def count(table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]

print("✅ Seed complete.")
print("Providers:", count("providers"))
print("Receivers:", count("receivers"))
print("Food Listings:", count("food_listings"))
print("Claims:", count("claims"))

conn.close()
