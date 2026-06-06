# Demo Video Script — Insight Engine (≤ 3 minutes)

> Format: MP4, ≥ 720p, max 3 min. **Live walkthrough of the working app — not a
> slideshow.** Record your screen with voiceover, upload to YouTube (unlisted).
> Recommended tools: OBS Studio (free) or Windows Game Bar (`Win+G`).
> Total target: ~2:45. Times are cumulative.

---

## Setup before recording

- Backend + frontend running (or the live Vercel link, warmed up).
- Have `backend/data/messy_sales.csv` ready on the desktop.
- Browser zoomed so text is readable at 720p. Close noisy tabs/notifications.
- Do one dry run so the LLM responses are warm and you know the timing.

---

## [0:00–0:20] Hook + problem  *(screen: the app's empty upload screen)*

> "Every business has messy sales spreadsheets — inconsistent dates, dollar
> signs, duplicate region names, missing values. To get answers, you normally
> need someone to clean the data *and* someone who can write SQL. **Insight
> Engine** removes both steps. Let me show you."

## [0:20–0:35] Solution in one line  *(screen: still on upload screen)*

> "You upload a raw CSV, it cleans itself and shows you exactly what changed,
> and then you just ask questions in plain English. Here's a deliberately messy
> sales file."

## [0:35–1:05] Upload + cleaning report  *(action: drag messy_sales.csv onto the uploader)*

> "I'll drop in the file… and instantly it's cleaned and loaded. Look at the
> **'What we cleaned' panel**: it dropped 2 duplicate rows, collapsed region
> labels — `N. America`, `north america`, `EUROPE` all became clean canonical
> names — parsed money like `$2.5k` and `(50)` for a refund, and filled missing
> ages with the median. **Nothing is hidden — every transformation is reported.**"

*(Point cursor at each line of the cleaning summary as you say it.)*

## [1:05–1:50] First question — the core magic  *(action: type a question)*

> "Now the fun part. I'll ask in plain English: *'Which regions have the highest
> total sales?'*"

*(Submit. When the result appears:)*

> "Here's what happened: the AI translated my question into **SQL** — you can see
> the exact query it generated — it ran against the cleaned data, gave me a
> **table**, a **chart**, and a **plain-English takeaway** explaining the result.
> No SQL knowledge needed on my end."

## [1:50–2:25] Second question — show depth  *(action: ask a harder one)*

> "Let's push it. *'Which regions have high sales but low profit margins?'*"

*(Submit.)*

> "It handles the more analytical question too — generating the aggregation,
> ranking, and a clear explanation of the trade-off. Behind the scenes every
> generated query is validated and sandboxed to read-only SELECTs, so it's safe."

## [2:25–2:45] AI flexibility + close  *(screen: app, or briefly the README AI section)*

> "The AI is pluggable — it runs on open-source models via Hugging Face by
> default, and can switch to Anthropic Claude with a single setting, so there's
> no vendor lock-in. That's **Insight Engine**: messy CSV in, clean data and
> real answers out — for anyone, no SQL required. Thanks for watching."

---

## Recording checklist

- [ ] Under 3:00, ≥ 720p, MP4
- [ ] Real live app shown (cleaning panel + SQL + chart + insight all visible)
- [ ] Clear voiceover throughout
- [ ] At least two different questions demonstrated
- [ ] Uploaded to YouTube as **Unlisted**, link tested in incognito
