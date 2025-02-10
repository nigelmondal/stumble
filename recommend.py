import mysql.connector
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Connect to MySQL Database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="stumble"
)
cursor = conn.cursor()

# Fetch user data
cursor.execute("SELECT user_id, bio, strengths, weaknesses FROM user")
users = cursor.fetchall()

# Convert to DataFrame
df = pd.DataFrame(users, columns=["user_id", "bio", "strengths", "weaknesses"])

# Fill missing values with an empty string
df = df.fillna("")

# Combine bio, strengths, and weaknesses into a single column
df["content"] = df["bio"] + " " + df["strengths"] + " " + df["weaknesses"]

# Apply TF-IDF Vectorization
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(df["content"])

# Compute Cosine Similarity
cosine_sim = cosine_similarity(tfidf_matrix)

# Function to recommend similar users
def recommend_similar_users(user_id, top_n=5):
    if user_id not in df["user_id"].values:
        return f"User ID {user_id} not found!"

    # Get index of the given user_id
    idx = df[df["user_id"] == user_id].index[0]

    # Get similarity scores & sort them
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get top N similar users (excluding itself)
    sim_users = [df.iloc[i[0]]["user_id"] for i in sim_scores[1 : top_n + 1]]
 
    return sim_users

# Example: Find top 5 similar users for user_id 3
similar_users = recommend_similar_users(3, top_n=3)
print(f"Top 5 similar users to User 3: {similar_users}")

# Close connection
cursor.close()
conn.close()
