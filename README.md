# 🎯 Altron Dashboard

**Altron** is a personal productivity command center designed to help you track habits, manage tasks, and visualize your progress with stunning analytics. "Dream big, start small, act now."

![Altron Dashboard](frontend/favicon.png)

## ✨ Features

- **📊 Dashboard**: Visual overview of your daily progress.
- **✅ Habit Tracker**: Track daily habits with streaks and heatmaps.
- **📝 Task Manager**: Manage to-dos with priorities and categories.
- **📈 Analytics**: Deep dive into your productivity trends (Weekly/Monthly/Yearly).
- **📅 Calendar**: View your activity history.
- **📧 Automated Reports**: Weekly and Monthly productivity summaries via email.
- **🌓 Dark/Light Mode**: Beautiful UI with customizable themes.

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 (Variables, Animations), JavaScript (Vanilla).
- **Backend**: Python, Flask.
- **Database**: PostgreSQL (Aiven Cloud).
- **Deployment**: Vercel (Split-Stack: Static Frontend + Serverless Backend).

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL connection string (Aiven)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Altron.git
    cd Altron
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file in `backend/` with the following:
    ```ini
    SECRET_KEY=your_secret_key
    PG_HOST=your-aiven-host
    PG_USER=avnadmin
    PG_PASSWORD=your-password
    PG_DATABASE=defaultdb
    PG_PORT=your-port
    SMTP_PASSWORD=your-gmail-app-password
    ```

4.  **Run Locally**:
    ```bash
    cd backend
    python app.py
    ```
    Visit `http://localhost:5000`

## ☁️ Deployment (Vercel)

This project is configured for **Vercel** deployment.

1.  Push to GitHub.
2.  Import project in Vercel.
3.  Add Environment Variables in Vercel settings.
4.  Deploy!

---
Developed with ❤️ by Varad in India.
