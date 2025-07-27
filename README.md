# Manochitram Movie Recommender

A modern, user-friendly movie recommendation desktop app using Python, Tkinter, and The Movie Database (TMDB) API. It suggests movies based on your mood (sentiment analysis) and age, with a beautiful macOS-inspired interface, dark mode, and history export features.

---

## Features

- 🎭 **Personalized Movie Recommendations**
  - Get movie suggestions tailored to your current mood (happy, sad, neutral, etc.) and age group. The app uses both your emotional input and age to choose the most suitable genres for you.

- 🧠 **Sentiment Analysis**
  - Uses the TextBlob library to analyze your written feelings and detect whether your mood is positive, neutral, or negative. This sentiment is then used to select the right movie genres.

- 🎨 **macOS-inspired User Interface**
  - Enjoy a clean, modern, and visually appealing desktop app styled after the macOS look and feel. All controls are easy to use and visually consistent.

- 🌙 **Light/Dark Mode Toggle**
  - Instantly switch between light and dark themes for comfort and accessibility. Dark mode applies to all major windows, including the history page.

- 🖼️ **Movie Posters with Fallback**
  - See poster images for recommended movies. If a poster is missing or cannot be loaded, a default image is shown to keep the interface looking polished.

- 📜 **Recommendation History & Export**
  - View all your past recommendations in a dedicated history window. Easily export your full recommendation history to a CSV file for future reference or sharing.

- 🔒 **Secure API Key Handling**
  - Your TMDB API key is kept outside the main code, in a separate file, for better security. This makes it easy to change your API key without editing code or risking accidental exposure.

---

## Setup Instructions

### 1. Install Python dependencies
Open a terminal in your project folder and run:
```bash
pip install -r requirements.txt
```

### 2. Get a TMDB API Key
- Sign up at [themoviedb.org](https://www.themoviedb.org/)
- Go to your profile > Settings > API
- Apply for an API key (v3 auth)
- Copy your API key

### 3. Add your API key
- Open `apikeytmdb.txt`
- Add this line (replace with your key):
  ```
  tmdb api key :YOUR_TMDB_API_KEY
  ```

### 4. Run the app
```bash
python manochitramcode.py
```

---

## Usage
- Enter your name, feeling, gender, and age
- Click **Submit** to get movie recommendations
- Toggle dark mode for a different look
- Click **View History** to see/export past recommendations

---

#

---

## Dependencies
- Python 3.x
- requests
- textblob
- Pillow
- tkinter

---

## License
This project is for personal/non-commercial use. See TMDB’s [terms of use](https://www.themoviedb.org/terms-of-use) for API usage.

---

## Credits
- [TMDB API](https://www.themoviedb.org/documentation/api)
- [TextBlob](https://textblob.readthedocs.io/en/dev/)
- [Pillow](https://python-pillow.org/)
