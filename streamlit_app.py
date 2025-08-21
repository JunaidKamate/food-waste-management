# streamlit_app.py
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Food Waste Management", page_icon="🍲", layout="wide")

# -------- DB CONNECTION (cached) --------
@st.cache_resource
def get_conn():
    # Path to DB file (portable for Windows + Streamlit Cloud)
    db_path = os.path.join(os.path.dirname(__file__), "lfwms.db")
    if not os.path.exists(db_path):
        st.error(f"❌ Database file not found at: {db_path}")
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_conn()

def run_query(sql, params=None):
    return pd.read_sql_query(sql, conn, params=params)

def execute_write(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    return cur.rowcount

# Quick check: show available tables
try:
    tables = run_query("SELECT name FROM sqlite_master WHERE type='table';")
    st.sidebar.write("✅ Tables detected:", tables["name"].tolist())
except Exception as e:
    st.sidebar.error(f"DB Error: {e}")

# -------- SIDEBAR NAV --------
st.sidebar.title("Food Waste Management")
section = st.sidebar.radio("Go to", ["Home", "Search Listings", "Provider Contacts", "Analysis", "CRUD"])

# -------- HOME --------
if section == "Home":
    st.title("🍲 Food Waste Management System")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Providers", run_query("SELECT COUNT(*) AS n FROM providers")["n"][0])
    c2.metric("Receivers", run_query("SELECT COUNT(*) AS n FROM receivers")["n"][0])
    c3.metric("Food Listings", run_query("SELECT COUNT(*) AS n FROM food_listings")["n"][0])
    c4.metric("Claims", run_query("SELECT COUNT(*) AS n FROM claims")["n"][0])

    st.markdown("---")
    st.subheader("Quick Peek: 10 Newest Listings (by Expiry Date)")
    df_home = run_query("""
        SELECT Food_ID, Food_Name, Quantity, DATE(Expiry_Date) AS Expiry_Date,
               Provider_ID, Provider_Type, Location, Food_Type, Meal_Type
        FROM food_listings
        ORDER BY DATE(Expiry_Date) DESC
        LIMIT 10;
    """)
    st.dataframe(df_home, use_container_width=True)

# -------- SEARCH LISTINGS --------
elif section == "Search Listings":
    st.header("🔍 Filter Food Listings")

    cities = ["All"] + sorted(run_query("SELECT DISTINCT Location FROM food_listings")["Location"].tolist())
    food_types = ["All"] + sorted(run_query("SELECT DISTINCT Food_Type FROM food_listings")["Food_Type"].tolist())
    meal_types = ["All"] + sorted(run_query("SELECT DISTINCT Meal_Type FROM food_listings")["Meal_Type"].tolist())

    c1, c2, c3 = st.columns(3)
    city = c1.selectbox("City", cities)
    ftype = c2.selectbox("Food Type", food_types)
    mtype = c3.selectbox("Meal Type", meal_types)

    sql = """
        SELECT Food_ID, Food_Name, Quantity, DATE(Expiry_Date) AS Expiry_Date,
               Provider_ID, Provider_Type, Location, Food_Type, Meal_Type
        FROM food_listings
        WHERE 1=1
    """
    params = []
    if city != "All":
        sql += " AND Location = ?"
        params.append(city)
    if ftype != "All":
        sql += " AND Food_Type = ?"
        params.append(ftype)
    if mtype != "All":
        sql += " AND Meal_Type = ?"
        params.append(mtype)

    df = run_query(sql, params or None)
    st.dataframe(df, use_container_width=True)

# -------- PROVIDER CONTACTS --------
elif section == "Provider Contacts":
    st.header("📞 Provider Contacts by City")
    cities = sorted(run_query("SELECT DISTINCT Location FROM providers")["Location"].tolist())
    city = st.selectbox("Choose City", cities)
    df = run_query("SELECT Provider_Name, Provider_Type, Contact FROM providers WHERE Location=?", (city,))
    st.dataframe(df, use_container_width=True)

# -------- ANALYSIS --------
elif section == "Analysis":
    st.header("📊 Insights (SQL)")
    choice = st.selectbox("Choose Analysis", [
        "Q1: Providers & Receivers per Location",
        "Q2: Top Provider Types by Quantity",
        "Q4: Receivers with Most Claims",
        "Q6: Locations with Highest Listings",
        "Q7: Most Common Food Types",
        "Q8: Claim Counts per Food Item",
        "Q9: Providers with Most Successful Claims",
        "Q10: Claim Status Distribution (Pie)",
        "Q11: Avg Quantity Claimed per Receiver",
        "Q12: Most-Claimed Meal Type",
        "Q13: Total Quantity Donated per Provider",
        "Q14: Listings Expiring Next 7 Days",
        "Q15: Avg Time-to-Claim per Location (days)",
        "Q16: Daily Claims Trend (March 2025)",
    ])

    if choice == "Q1: Providers & Receivers per Location":
        df = run_query("""
        SELECT r.Location,
               (SELECT COUNT(*) FROM providers p WHERE p.Location = r.Location) AS Provider_Count,
               COUNT(*) AS Receiver_Count
        FROM receivers r
        GROUP BY r.Location
        ORDER BY Provider_Count DESC, Receiver_Count DESC
        LIMIT 10;""")
        st.write("Top locations by providers & receivers:")
        st.bar_chart(df.set_index("Location"))

    elif choice == "Q2: Top Provider Types by Quantity":
        df = run_query("""
        SELECT p.Provider_Type, SUM(f.Quantity) AS Total_Quantity
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Provider_Type
        ORDER BY Total_Quantity DESC
        LIMIT 10;""")
        st.bar_chart(df.set_index("Provider_Type"))

    elif choice == "Q4: Receivers with Most Claims":
        df = run_query("""
        SELECT r.Receiver_Name, COUNT(c.Claim_ID) AS Total_Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Receiver_ID, r.Receiver_Name
        ORDER BY Total_Claims DESC
        LIMIT 10;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q6: Locations with Highest Listings":
        df = run_query("""
        SELECT Location, COUNT(*) AS Listings_Count
        FROM food_listings
        GROUP BY Location
        ORDER BY Listings_Count DESC
        LIMIT 10;""")
        st.bar_chart(df.set_index("Location"))

    elif choice == "Q7: Most Common Food Types":
        df = run_query("""
        SELECT Food_Type, COUNT(*) AS Listings_Count, SUM(Quantity) AS Total_Quantity
        FROM food_listings
        GROUP BY Food_Type
        ORDER BY Listings_Count DESC;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q8: Claim Counts per Food Item":
        df = run_query("""
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claim_Count
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
        ORDER BY Claim_Count DESC
        LIMIT 15;""")
        st.bar_chart(df.set_index("Food_Name"))

    elif choice == "Q9: Providers with Most Successful Claims":
        df = run_query("""
        SELECT p.Provider_Name, COUNT(c.Claim_ID) AS Successful_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE c.Status = 'Completed'
        GROUP BY p.Provider_ID, p.Provider_Name
        ORDER BY Successful_Claims DESC
        LIMIT 10;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q10: Claim Status Distribution (Pie)":
        df = run_query("""
        SELECT Status, COUNT(*) AS Claim_Count
        FROM claims
        GROUP BY Status;""")
        st.write("Claim status breakdown:")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            fig, ax = plt.subplots()
            ax.pie(df["Claim_Count"], labels=df["Status"], autopct="%1.1f%%", startangle=90)
            ax.axis('equal')
            st.pyplot(fig)

    elif choice == "Q11: Avg Quantity Claimed per Receiver":
        df = run_query("""
        SELECT r.Receiver_Name, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY r.Receiver_ID, r.Receiver_Name
        HAVING COUNT(c.Claim_ID) > 2
        ORDER BY Avg_Quantity DESC
        LIMIT 10;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q12: Most-Claimed Meal Type":
        df = run_query("""
        SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Claim_Count
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Meal_Type
        ORDER BY Claim_Count DESC;""")
        st.bar_chart(df.set_index("Meal_Type"))

    elif choice == "Q13: Total Quantity Donated per Provider":
        df = run_query("""
        SELECT p.Provider_Name, SUM(f.Quantity) AS Total_Quantity
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Provider_ID, p.Provider_Name
        ORDER BY Total_Quantity DESC
        LIMIT 10;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q14: Listings Expiring Next 7 Days":
        df = run_query("""
        SELECT f.Food_Name, f.Quantity, DATE(f.Expiry_Date) AS Expiry_Date,
               p.Provider_Name, f.Location
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE DATE(f.Expiry_Date) BETWEEN DATE('now') AND DATE('now', '+7 days')
        ORDER BY DATE(f.Expiry_Date) ASC;""")
        if df.empty:
            st.info("No listings expiring in the next 7 days.")
        else:
            st.dataframe(df, use_container_width=True)

    elif choice == "Q15: Avg Time-to-Claim per Location (days)":
        df = run_query("""
        SELECT f.Location,
               ROUND(AVG(JULIANDAY(c.Claim_Date) - JULIANDAY(f.Expiry_Date)), 2) AS Avg_Days_To_Claim,
               COUNT(c.Claim_ID) AS Total_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Location
        HAVING Total_Claims > 1
        ORDER BY Avg_Days_To_Claim ASC
        LIMIT 10;""")
        st.dataframe(df, use_container_width=True)

    elif choice == "Q16: Daily Claims Trend (March 2025)":
        df = run_query("""
        SELECT DATE(c.Claim_Date) AS Claim_Date,
               COUNT(c.Claim_ID) AS Daily_Claims
        FROM claims c
        WHERE strftime('%Y-%m', c.Claim_Date) = '2025-03'
        GROUP BY Claim_Date
        ORDER BY Claim_Date;""")
        if df.empty:
            st.info("No claims found for March 2025.")
        else:
            st.line_chart(df.set_index("Claim_Date"))

# -------- CRUD --------
elif section == "CRUD":
    st.header("✍ Manage Food Listings / Claims")
    action = st.radio("Action", ["Add Listing", "Update Claim Status", "Delete Listing"])
    # (your CRUD code stays the same)
