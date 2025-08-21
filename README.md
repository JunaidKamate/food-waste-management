# 🍲 Food Waste Management System
📖 Overview

A Streamlit + SQLite application to manage food donations and claims.
The project helps reduce food wastage by connecting providers (restaurants, NGOs, etc.) with receivers in need.

🚀 Features

📊 Dashboard: View counts of providers, receivers, listings, and claims.

🔍 Search Listings: Filter food by city, type, or meal.

📞 Provider Contacts: Find provider details by city.

📈 Analysis: 15 SQL-driven insights (e.g., top providers, expiry alerts, claim trends).

✍️ CRUD Operations: Add, update, or delete food listings.

⚡ Run Locally
# 1. Clone repo
git clone https://github.com/<your-username>/food-waste-management.git
cd food-waste-management

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run app
streamlit run app/streamlit_app.py

🗂️ Project Structure
food-waste-management/
│── app/streamlit_app.py      # Main Streamlit app
│── data/lfwms.db             # SQLite database
│── scripts/reset_and_seed.py # Reset + seed DB
│── *.csv                     # Seed data files
│── requirements.txt
│── README.md
│── .gitignore

👨‍💻 Author

Junaid Kamate

📧 E-mail: junaidkamate10@gmail.com

🔗 LinkedIn: https://www.linkedin.com/in/junaid-kamate/

💻 GitHub: https://github.com/JunaidKamate
