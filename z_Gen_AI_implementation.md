# ⚡ Day Pulse — Gen AI Implementation Notes

> Pre-implementation Q&A and decisions to be resolved before development begins.

---

## ❓ Query 1: Which Groq API Models Are Best for This Task?

### What We Need the Model to Do
- Analyze habit + task completion data (structured/tabular)
- Find patterns across 30-day windows (e.g., correlations, streaks, drops)
- Generate short, punchy, human-readable "Day Pulse Reports"
- Predict next-day performance score based on behavioral signals

---

### ✅ Recommended Free Models on Groq API

All models below are **100% free to use** on Groq's free tier (no credit card required — sign up at [console.groq.com](https://console.groq.com)). Rate limits apply but are generous enough for daily-per-user triggers.

---

#### 🥇 1. `llama-3.3-70b-versatile` — **BEST CHOICE** ✅ (Confirmed)

| Property | Value |
|---|---|
| **Provider** | Meta |
| **Context Window** | 131,072 tokens |
| **Free Tier RPD** | ~14,400 requests/day |
| **Speed** | Very fast (Groq LPU) |
| **Best For** | Pattern analysis + report generation |

**Why it's our pick:**
- Largest free model on Groq — best reasoning and pattern detection
- 131K context = can handle months of habit/task logs in one prompt
- Versatile instruction-following = great at generating structured, punchy report text
- Groq's inference is the fastest in the world (LPU hardware), so reports generate in < 2 seconds

---

#### 🥈 2. `llama-3.1-8b-instant` — **BACKUP / SPEED FALLBACK**

| Property | Value |
|---|---|
| **Provider** | Meta |
| **Context Window** | 131,072 tokens |
| **Free Tier RPD** | ~14,400 requests/day |
| **Speed** | Extremely fast |
| **Best For** | Quick/lightweight report generation |

**When to use this:**
- If the 70B model is rate-limited
- For users with very small datasets (< 7 days of data)
- For generating quick "preview" insights mid-day

---

#### 🥉 3. `deepseek-r1-distill-llama-70b` — **FOR COMPLEX REASONING**

| Property | Value |
|---|---|
| **Provider** | DeepSeek (distilled on Llama) |
| **Context Window** | 131,072 tokens |
| **Free Tier RPD** | ~1,000 requests/day |
| **Speed** | Moderate |
| **Best For** | Deep causal reasoning, "why" patterns |

**When to use this:**
- For users who've been on the app 60+ days (complex pattern mining)
- For generating multi-week trend summaries
- ⚠️ Lower daily limit (1,000 RPD) — use selectively

---

### 📊 Model Comparison Summary

| Model | Quality | Speed | Daily Requests | Context | Use Case |
|---|---|---|---|---|---|
| `llama-3.3-70b-versatile` | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ~14,400 | 131K | **Primary — Daily Pulse Report** |
| `llama-3.1-8b-instant` | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ~14,400 | 131K | Fallback / Quick Summary |
| `deepseek-r1-distill-llama-70b` | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | ~1,000 | 131K | Deep pattern analysis (power users) |

---

### 🔑 Groq API Integration Snippet (Python)

```python
from groq import Groq

client = Groq(api_key="YOUR_GROQ_API_KEY")

def generate_day_pulse_report(user_data: dict) -> str:
    prompt = f"""
    You are LifeSync's AI analyst. Analyze the following 30-day habit and task data
    and generate a short, punchy "Day Pulse Report" in this exact format:

    ⚡ Today's Day Pulse

    Your Power Combo: [habit] + [activity] = [X]% task completion rate
    Your Kryptonite: [pattern] → [X]x more likely to [outcome]
    Hidden Insight: [surprising pattern based on data]
    Tomorrow's Prediction: [X]% chance of a great day if [recommendation]

    User Data:
    {user_data}

    Keep it punchy, data-driven, and motivating. Use real numbers from the data.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # PRIMARY MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content
```

---

## ❓ Query 2: How Do We Send the Day Pulse Report to Users?

### The Report We're Sending
```
⚡ Today's Day Pulse

Your Power Combo: Gym + Deep Work = 94% task completion rate
Your Kryptonite: Skipping morning habits → 3x more likely to miss evening ones
Hidden Insight: You're 2x more productive on rainy days (based on 30-day pattern)
Tomorrow's Prediction: 78% chance of a great day if you start before 8 AM
```

---

### 📬 Delivery Options — Compared

#### ✅ Option A: **Email** (Recommended — We Already Have It!) ✅ (Confirmed)

Since LifeSync **already has an email service set up** (SMTP via Gmail + Render), this is the easiest and most impactful delivery channel.

| Property | Details |
|---|---|
| **Tool** | Existing Flask email (SMTP) |
| **Trigger Time** | Every night at 10:00 PM |
| **Format** | Styled HTML email |
| **Cost** | Free (already configured) |
| **Effort** | Low — reuse existing email infrastructure |

**What the email looks like:**

```
Subject: ⚡ Your Day Pulse Report — Friday, Feb 21

Hi [Name],

Here's what the AI found about your day:

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ TODAY'S DAY PULSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

💪 Your Power Combo:
   Gym + Deep Work = 94% task completion rate

⚡ Your Kryptonite:
   Skipping morning habits → 3x more likely to miss evening ones

🔍 Hidden Insight:
   You're 2x more productive on rainy days (based on 30-day pattern)

🔮 Tomorrow's Prediction:
   78% chance of a great day if you start before 8 AM

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open LifeSync → [View Full Analytics]
```

---

#### ✅ Option B: **In-App Notification / Dashboard Card**

Display the Day Pulse Report directly inside the LifeSync app as a highlighted card on the dashboard.

| Property | Details |
|---|---|
| **Location** | Dashboard homepage (top card / banner) |
| **Trigger** | Generated nightly, shown next morning |
| **Format** | Styled card with emoji + colored text |
| **Cost** | Free |
| **Effort** | Medium — requires frontend card component |

**Best for:** Users who open the app daily

---

#### 🟡 Option C: **Push Notifications** (Future Feature)

Send a short teaser notification that links to the full report.

| Property | Details |
|---|---|
| **Tool** | Firebase Cloud Messaging (FCM) — free |
| **Message** | "⚡ Your Day Pulse is ready! You hit a 94% rate today 🔥" |
| **Cost** | Free |
| **Effort** | High — requires FCM setup + device token management |

**Best for:** Mobile app version of LifeSync

---

#### 🔴 Option D: **SMS** (Not Recommended for Now)

| Property | Details |
|---|---|
| **Tool** | Twilio / AWS SNS |
| **Cost** | Paid (~$0.0079/SMS) |
| **Character Limit** | 160 chars — too short for full report |
| **Effort** | High |

**Verdict:** Too expensive + too limited for this rich report format. Skip for now.

---

### 🏆 Recommended Delivery Strategy

```
Phase 1 (Now):     Email  →  Nightly at 10 PM
                             (Reuse existing SMTP setup)

Phase 2 (Later):   In-App Dashboard Card
                             (Show report on homepage next morning)

Phase 3 (Future):  Push Notification (teaser)
                             (Link to in-app full report)
```

---

### ⏰ Trigger Architecture

```python
# Flask scheduler (existing thread-based scheduler)
# Runs every night at 10:00 PM

def send_daily_pulse_reports():
    users = get_all_users_with_email()
    for user in users:
        # 1. Fetch last 30 days of habit + task data
        user_data = get_user_analytics(user['id'], days=30)

        # 2. Call Groq API → generate the Day Pulse report
        report = generate_day_pulse_report(user_data)

        # 3. Send via email (existing email service)
        email_service.send_day_pulse_report(user['email'], user['username'], report)
```

---

## 📋 Summary

| Query | Decision |
|---|---|
| **AI Model** | `llama-3.3-70b-versatile` via Groq API (free, fast, 131K context) |
| **Fallback Model** | `llama-3.1-8b-instant` (same free limits, faster) |
| **Primary Delivery** | HTML Email — nightly at 10 PM via existing SMTP |
| **Secondary Delivery** | In-app dashboard card (Phase 2) |
| **Cost** | $0 (Groq free tier + existing email) |

---

## ❓ Query 3: What Exactly is "Day Pulse"?

### Simple Definition

> **Day Pulse** = The real-time heartbeat of your day's productivity, decoded by AI every night.

Just like a pulse measures the health of your heartbeat, your **Day Pulse** measures the health of your day — revealing the hidden rhythms in your habits and decisions that make some days great and others fall flat.

### Analogy Table

| Heartbeat / Pulse | Day Pulse |
|---|---|
| Measures heart rhythm | Measures your habit + task rhythm |
| Unique to every person | Unique to every person's daily pattern |
| Tells doctors your health | Tells you your productivity health |
| Monitored by doctors | Monitored nightly by Groq AI |
| Reveals heart risks | Reveals productivity risks (kryptonites) |
| Can spike or drop | Your energy and output spikes or drops |

### In Plain English

Every night, the AI looks at your **last 30 days** of data and asks:

- 🔗 **Which habits always go together?** → "Power Combos"
- 💀 **Which skipped habit triggers a bad day?** → "Kryptonites"
- 🔍 **What unusual pattern nobody told you about?** → "Hidden Insights"
- 🔮 **Based on all patterns, how good will tomorrow be?** → "Day Prediction"

It's not just a report — it's your **personal AI life coach** speaking in plain English, reading the pulse of your daily life.

### Why "Pulse"?
Because a pulse is **alive, real-time, and personal**. It rises when you do great things and drops when you skip your habits. The name immediately communicates that this isn't a static weekly report — it's a **live signal** reading your daily performance every single night.

---

## ❓ Query 4: Frontend Implementation — How Will It Look?

### The Plan

Similar to how the **Automated Reports** section (Weekly Report / Monthly Report) shows schedule cards with an "Active" badge in the Analytics page, the **Day Pulse** feature will get its own status card in the same section.

### 📍 Where It Lives

The Day Pulse card will appear as a **third card** in the existing `Automated Reports` section in the **Analytics page**, right alongside Weekly Report and Monthly Report:

```
┌─────────────────────────────────────────────────────────────┐
│  🤖  Automated Reports                                       │
│                                                             │
│  Your progress reports are generated automatically.         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  📅           │  │  📅           │  │  ⚡               │  │
│  │ Weekly Report │  │Monthly Report │  │  Day Pulse       │  │
│  │Every Sunday   │  │1st of Month   │  │ Every night 10PM │  │
│  │  ✅ Active    │  │  ✅ Active    │  │  ✅ Active       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 🎨 The Card Design (Matching Existing Style)

The Day Pulse card will look exactly like the existing Weekly/Monthly cards but with:
- Icon: ⚡ (lightning / pulse energy)
- Title: **Day Pulse**
- Schedule text: *Every night at 10:00 PM*
- Status badge: ✅ **Active** (green, same as existing cards)
- A subtle **green pulse glow** on the border to make it feel alive/AI

### 🔧 What Files Change

| File | What Changes |
|---|---|
| `backend/utils/` | **[NEW]** `ai_day_pulse.py` — Groq API call + report generation |
| `backend/utils/email_service.py` | **[MODIFY]** Add `send_day_pulse_report()` method |
| `backend/utils/scheduler.py` | **[MODIFY]** Add nightly 10 PM Day Pulse trigger |
| `backend/routes/analytics.py` | **[MODIFY]** Add `/api/daypulse/latest` endpoint (for in-app card) |
| `frontend/analytics.html` | **[MODIFY]** Add Day Pulse card to Automated Reports section |
| `backend/requirements.txt` | **[MODIFY]** Add `groq` package |
| `backend/.env` | **[MODIFY]** Add `GROQ_API_KEY` variable |

### 🔄 Full Data Flow

```
Every night at 10 PM
        │
        ▼
scheduler.py  ──triggers──►  ai_day_pulse.py
                                    │
                                    ▼
                          Query last 30 days
                          habit + task data
                          from PostgreSQL DB
                                    │
                                    ▼
                          Call Groq API
                          (llama-3.3-70b-versatile)
                                    │
                                    ▼
                          Generate Day Pulse Report
                          (Power Combo, Kryptonite,
                           Hidden Insight, Prediction)
                                    │
                                    ▼
                          email_service.send_day_pulse_report()
                                    │
                                    ▼
                          📧 Styled HTML Email
                          sent to user's inbox
```

### 📧 HTML Email Style (Preview)

The email will use the **same dark theme** as the existing welcome/weekly emails — dark background, green accents (`#00ff88`), rounded cards — but with Day Pulse-specific sections:

```
┌─────────────────────────────────┐
│  ⚡  Your Day Pulse Report       │  ← Green header
│  Friday, Feb 21, 2026           │
├─────────────────────────────────┤
│  💪 Power Combo                 │  ← Green card
│  Gym + Deep Work = 94% rate     │
├─────────────────────────────────┤
│  ⚡ Your Kryptonite              │  ← Orange/red card
│  Skipped morning → 3x worse     │
├─────────────────────────────────┤
│  🔍 Hidden Insight               │  ← Purple card
│  2x productive on rainy days    │
├─────────────────────────────────┤
│  🔮 Tomorrow's Prediction        │  ← Blue card
│  78% great day if start < 8 AM  │
└─────────────────────────────────┘
```

---

## ✅ Final Confirmed Decisions

| Decision | Choice |
|---|---|
| **Feature Name** | **Day Pulse** ⚡ |
| **AI Model** | `llama-3.3-70b-versatile` (Groq, free) |
| **Delivery** | Styled HTML Email via existing SMTP, nightly 10 PM |
| **Frontend** | New card in Automated Reports section (Analytics page) |
| **Card Icon** | ⚡ with green pulse glow border |
| **New backend file** | `backend/utils/ai_day_pulse.py` |
| **Env variable needed** | `GROQ_API_KEY` in `.env` and Render |

---

*Last Updated: Feb 20, 2026 | Feature: Day Pulse*
