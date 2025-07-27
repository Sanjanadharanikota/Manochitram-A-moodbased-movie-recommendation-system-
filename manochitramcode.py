import requests

import sqlite3
import tkinter as tk
from tkinter.ttk import Combobox
from textblob import TextBlob
from PIL import Image, ImageTk
import io

# TMDB API details
def get_tmdb_api_key():
    try:
        with open('apikeytmdb.txt', 'r') as f:
            for line in f:
                if line.lower().startswith('tmdb api key'):
                    return line.split(':', 1)[1].strip()
    except Exception as e:
        print('Error reading TMDB API key:', e)
    return ''

API_KEY = get_tmdb_api_key()  # Read from file
BASE_URL = 'https://api.themoviedb.org/3'
IMG_URL = 'https://image.tmdb.org/t/p/w200'

# Genre mapping based on sentiment analysis
SENTIMENT_GENRE_MAP = {
    'positive': 35,  # Comedy
    'neutral': 28,   # Action
    'negative': 18   # Drama
}

# Genre mapping based on age
AGE_GENRE_MAP = {
    'child': 16,     # Animation
    'teen': 10749,   # Romance
    'adult': 18,     # Drama
}

# SQLite setup
def setup_database():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY,
            sentiment TEXT NOT NULL,
            movie_title TEXT NOT NULL,
            overview TEXT NOT NULL,
            release_date TEXT,
            rating REAL,
            user_name TEXT,
            user_age INTEGER,
            user_gender TEXT
        )
    ''')
    conn.commit()
    return conn, c

conn, c = setup_database()

# Sentiment prediction logic
def predict_sentiment(text):
    blob = TextBlob(text)
    if blob.sentiment.polarity > 0:
        return 'positive'
    elif blob.sentiment.polarity == 0:
        return 'neutral'
    else:
        return 'negative'

# Age category logic
def age_to_category(age):
    if age <= 12:
        return 'child'
    elif 13 <= age <= 19:
        return 'teen'
    else:
        return 'adult'

# Map sentiment and age to genre
def sentiment_and_age_to_genre_id(sentiment, age):
    age_category = age_to_category(age)
    genre_from_age = AGE_GENRE_MAP.get(age_category, 18)  # Default to Drama for adults
    genre_from_sentiment = SENTIMENT_GENRE_MAP.get(sentiment, 35)  # Default to Comedy
    return [genre_from_sentiment, genre_from_age]

# Fetch movie recommendations from TMDB
def get_movie_recommendations_from_tmdb(sentiment, age):
    genre_ids = sentiment_and_age_to_genre_id(sentiment, age)
    url = f"{BASE_URL}/discover/movie"
    query_params = {
        'api_key': API_KEY,
        'with_genres': ','.join(map(str, genre_ids)),
        'sort_by': 'popularity.desc',
        'language': 'en-US'
    }
    try:
        response = requests.get(url, params=query_params, timeout=10)
        response.raise_for_status()
        data = response.json().get('results', [])[:5]
        return [(movie['title'],
                 movie.get('overview', 'No description'),
                 movie.get('release_date', 'Unknown'),
                 movie.get('vote_average', 0),
                 IMG_URL + movie['poster_path'] if movie.get('poster_path') else None) for movie in data]
    except requests.RequestException as e:
        print("Error fetching data:", e)
        return []

# Display movie recommendations
def display_recommendations(recommendations):
    # Clear previous recommendations
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    if not recommendations:
        tk.Label(scrollable_frame, text="No recommendations available.", wraplength=500, bg="#F7F7F7", fg="black").pack()

    for title, overview, release_date, rating, poster_url in recommendations:
        frame = tk.Frame(scrollable_frame, bg="#F7F7F7")
        frame.pack(pady=10, anchor="w", fill="x")

        # Display poster image
        def get_default_img():
            # Simple gray image as default (100x150)
            from PIL import ImageDraw
            img = Image.new('RGB', (100, 150), color=(200, 200, 200))
            d = ImageDraw.Draw(img)
            d.text((10, 65), "No Image", fill=(100, 100, 100))
            return ImageTk.PhotoImage(img)

        if poster_url:
            try:
                response = requests.get(poster_url, stream=True)
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((100, 150), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Failed to load image for {title}: {e}")
                img_tk = get_default_img()
        else:
            img_tk = get_default_img()
        img_label = tk.Label(frame, image=img_tk, bg="#F7F7F7")
        img_label.image = img_tk
        img_label.grid(row=0, column=0, rowspan=4, padx=5, pady=5)

        # Display movie details
        tk.Label(frame, text=f"Title: {title}", font=("Helvetica Neue", 12, "bold"), bg="#F7F7F7", fg="#007AFF").grid(row=0, column=1, sticky='w')
        tk.Label(frame, text=f"Overview: {overview[:100]}...", wraplength=400, bg="#F7F7F7", fg="black").grid(row=1, column=1, sticky='w')
        tk.Label(frame, text=f"Release Date: {release_date}", bg="#F7F7F7", fg="black").grid(row=2, column=1, sticky='w')
        tk.Label(frame, text=f"Rating: {rating}", bg="#F7F7F7", fg="black").grid(row=3, column=1, sticky='w')

    # Update scrollregion after content is added
    canvas.config(scrollregion=canvas.bbox("all"))

# Save recommendations to database
def save_recommendations_to_db(recommendations, sentiment, user_name, user_age, user_gender):
    for title, overview, release_date, rating, _ in recommendations:
        c.execute(''' 
            INSERT INTO recommendations (sentiment, movie_title, overview, release_date, rating, user_name, user_age, user_gender)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sentiment, title, overview, release_date, rating, user_name, user_age, user_gender))
    conn.commit()

# Handle submit button click
def on_submit():
    user_name = name_entry.get().strip()
    user_feeling = feeling_entry.get().strip()
    user_gender = gender_combobox.get().strip()
    user_age_str = age_entry.get().strip()

    # Input validation
    if not user_name:
        messagebox.showerror("Input Error", "Please enter your name.")
        return
    if not user_feeling:
        messagebox.showerror("Input Error", "Please describe your feeling.")
        return
    if not user_gender:
        messagebox.showerror("Input Error", "Please select your gender.")
        return
    if not user_age_str.isdigit() or int(user_age_str) <= 0:
        messagebox.showerror("Input Error", "Please enter a valid age.")
        return
    user_age = int(user_age_str)

    sentiment = predict_sentiment(user_feeling)

    # Show detected sentiment
    if sentiment == 'positive':
        sentiment_text = 'Detected mood: Positive 😊'
    elif sentiment == 'neutral':
        sentiment_text = 'Detected mood: Neutral 😐'
    else:
        sentiment_text = 'Detected mood: Negative 🙁'
    sentiment_label.config(text=sentiment_text)
    root.update_idletasks()

    # Show loading indicator and disable submit
    loading_label.config(text="Loading recommendations...")
    submit_button.config(state=tk.DISABLED)
    root.update_idletasks()

    try:
        recommendations = get_movie_recommendations_from_tmdb(sentiment, user_age)
    except Exception as e:
        loading_label.config(text="")
        submit_button.config(state=tk.NORMAL)
        messagebox.showerror("Network Error", f"Failed to fetch recommendations: {e}")
        return

    loading_label.config(text="")
    submit_button.config(state=tk.NORMAL)

    if not recommendations:
        messagebox.showinfo("No Results", "No movie recommendations found. Please try again later.")
        return

    display_recommendations(recommendations)
    try:
        save_recommendations_to_db(recommendations, sentiment, user_name, user_age, user_gender)
    except Exception as e:
        messagebox.showwarning("Database Error", f"Could not save recommendations: {e}")

# Set up main window (macOS theme style)
root = tk.Tk()
root.title("Manochitram")
root.geometry("600x600")
root.config(bg="#F7F7F7")  # macOS light background

# Header
header_frame = tk.Frame(root, bg="#007AFF")
header_frame.pack(fill="x", pady=10)
header_label = tk.Label(header_frame, text="Manochitram - Movie Recommender", font=("Helvetica Neue", 16, "bold"), bg="#007AFF", fg="white")
header_label.pack(pady=10)

# Input Frame
form_frame = tk.Frame(root, bg="#F7F7F7")
form_frame.pack(pady=20)

tk.Label(form_frame, text="Name:", bg="#F7F7F7", fg="black").grid(row=0, column=0, padx=5, pady=5)
name_entry = tk.Entry(form_frame)
name_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Feeling:", bg="#F7F7F7", fg="black").grid(row=1, column=0, padx=5, pady=5)
feeling_entry = tk.Entry(form_frame)
feeling_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Gender:", bg="#F7F7F7", fg="black").grid(row=2, column=0, padx=5, pady=5)
gender_combobox = Combobox(form_frame, values=["Male", "Female", "Other"])
gender_combobox.grid(row=2, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Age:", bg="#F7F7F7", fg="black").grid(row=3, column=0, padx=5, pady=5)
age_entry = tk.Entry(form_frame)
age_entry.grid(row=3, column=1, padx=5, pady=5)

submit_button = tk.Button(form_frame, text="Submit", command=on_submit, bg="#007AFF", fg="white")
submit_button.grid(row=4, columnspan=2, pady=10)

# Loading indicator
loading_label = tk.Label(form_frame, text="", bg="#F7F7F7", fg="#007AFF", font=("Helvetica Neue", 10, "italic"))
loading_label.grid(row=5, columnspan=2, pady=5)

# Sentiment label
sentiment_label = tk.Label(form_frame, text="", bg="#F7F7F7", fg="#333333", font=("Helvetica Neue", 11, "bold"))
sentiment_label.grid(row=6, columnspan=2, pady=5)

# Scrollable Canvas for Recommendations
canvas = tk.Canvas(root, bg="#F7F7F7")
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F7F7F7")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Dark mode state
is_dark_mode = [False]

def toggle_dark_mode():
    if not is_dark_mode[0]:
        # Dark mode colors
        root.config(bg="#222222")
        header_frame.config(bg="#111111")
        header_label.config(bg="#111111", fg="#FFFB")
        form_frame.config(bg="#222222")
        for widget in form_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg="#222222", fg="#EEEEEE")
            elif isinstance(widget, tk.Entry):
                widget.config(bg="#333333", fg="#EEEEEE", insertbackground="#EEEEEE")
            elif isinstance(widget, tk.Button):
                widget.config(bg="#333366", fg="#EEEEEE")
            elif isinstance(widget, Combobox):
                widget.config(background="#333333", foreground="#EEEEEE")
        loading_label.config(bg="#222222", fg="#80BFFF")
        sentiment_label.config(bg="#222222", fg="#FFD700")
        canvas.config(bg="#222222")
        scrollable_frame.config(bg="#222222")
        # Update history window if open
        if history_window_ref['win'] is not None:
            history_window_ref['win'].config(bg="#222222")
            for w in history_window_ref['widgets']:
                if isinstance(w, tk.Label):
                    w.config(bg="#333333", fg="#FFD700")
                elif isinstance(w, tk.Button):
                    w.config(bg="#333366", fg="#FFD700")
        is_dark_mode[0] = True
    else:
        # Light mode colors
        root.config(bg="#F7F7F7")
        header_frame.config(bg="#007AFF")
        header_label.config(bg="#007AFF", fg="white")
        form_frame.config(bg="#F7F7F7")
        for widget in form_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg="#F7F7F7", fg="black")
            elif isinstance(widget, tk.Entry):
                widget.config(bg="white", fg="black", insertbackground="black")
            elif isinstance(widget, tk.Button):
                widget.config(bg="#007AFF", fg="white")
            elif isinstance(widget, Combobox):
                widget.config(background="white", foreground="black")
        loading_label.config(bg="#F7F7F7", fg="#007AFF")
        sentiment_label.config(bg="#F7F7F7", fg="#333333")
        canvas.config(bg="#F7F7F7")
        scrollable_frame.config(bg="#F7F7F7")
        # Update history window if open
        if history_window_ref['win'] is not None:
            history_window_ref['win'].config(bg="#F7F7F7")
            for w in history_window_ref['widgets']:
                if isinstance(w, tk.Label):
                    w.config(bg="#F7F7F7", fg="#333333")
                elif isinstance(w, tk.Button):
                    w.config(bg="#007AFF", fg="white")
        is_dark_mode[0] = False

dark_mode_button = tk.Button(form_frame, text="Toggle Dark Mode", bg="#333366", fg="#FFD700", command=toggle_dark_mode)
dark_mode_button.grid(row=8, columnspan=2, pady=10)

# View History button
history_button = tk.Button(form_frame, text="View History", bg="#34A853", fg="white", command=lambda: show_history())
history_button.grid(row=7, columnspan=2, pady=10)

import csv

history_window_ref = {'win': None, 'widgets': []}

def show_history():
    history_win = tk.Toplevel(root)
    history_win.title("Recommendation History")
    history_win.geometry("800x400")
    history_win.config(bg="#F7F7F7")
    history_window_ref['win'] = history_win
    history_window_ref['widgets'] = []

    # Table headers
    headers = ["Name", "Age", "Gender", "Sentiment", "Movie Title", "Release Date", "Rating"]
    for col, header in enumerate(headers):
        lbl = tk.Label(history_win, text=header, bg="#007AFF", fg="white", font=("Helvetica Neue", 10, "bold"), padx=5, pady=5)
        lbl.grid(row=0, column=col, sticky="nsew")
        history_window_ref['widgets'].append(lbl)

    # Fetch data
    c.execute("SELECT user_name, user_age, user_gender, sentiment, movie_title, release_date, rating FROM recommendations ORDER BY id DESC")
    rows = c.fetchall()
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, value in enumerate(row):
            lbl = tk.Label(history_win, text=value, bg="#F7F7F7", fg="#333333", wraplength=150, padx=3, pady=3)
            lbl.grid(row=row_idx, column=col_idx, sticky="nsew")
            history_window_ref['widgets'].append(lbl)

    def export_history():
        try:
            with open("recommendation_history.csv", "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(row)
            tk.messagebox.showinfo("Export Successful", "History exported to recommendation_history.csv")
        except Exception as e:
            tk.messagebox.showerror("Export Error", f"Could not export: {e}")

    export_btn = tk.Button(history_win, text="Export to CSV", bg="#007AFF", fg="white", command=export_history)
    export_btn.grid(row=len(rows)+1, columnspan=len(headers), pady=10)
    history_window_ref['widgets'].append(export_btn)

# Run the application
root.mainloop()