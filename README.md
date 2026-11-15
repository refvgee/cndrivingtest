# China Driver's License Test (Subject 1 / 科目一) — SQLite & Anki Suite

A complete, offline-ready study and testing suite for the English-language Chinese driver's license theory test (Subject 1 / 科目一).

---

## 📦 What Is Included

| File | Description |
| :--- | :--- |
| **`china_driving_test.db`** | Full SQLite database containing all 2,545 questions, options, verified image paths, tags, and tracking tables. |
| **`China_Driving_Test_Subject_1.apkg`** | Ready-to-import Anki Deck package with 2,545 styled flashcards, tagged topics, and all 787 exam diagram images embedded. |
| **`index.html`** | Offline local browser mock exam app (timed 100-question simulation, topic filtering, instant feedback). |
| **`practice.py`** | Terminal-based interactive practice runner that logs your test history directly into the SQLite database. |
| **`images/`** | 787 exam illustration diagrams (traffic signs, hand gestures, road situations). |
| **`build_db.py`** | Script used to compile the raw JSON question bank into the indexed SQLite database. |
| **`export_anki.py`** | Script used to generate the `.apkg` file with custom card templates. |

---

## 🗄️ SQLite Database Schema

The database (`china_driving_test.db`) includes the following tables, views, and indexes:

### 1. `questions` Table
* `id` (TEXT, PK): Unique question identifier.
* `question_num` (INTEGER): Sequential 1–2545 question number.
* `chapter_id` / `chapter_en` / `chapter_zh`: Official category/chapter in English and Chinese.
* `type`: `'judgement'` (True/False) or `'single_choice'` (Multiple Choice).
* `question_en` / `question_zh`: Question prompt in English and Chinese.
* `answer`: Correct choice (`'A'`, `'B'`, `'C'`, or `'D'`).
* `why_en`: English explanation and rationale.
* `explanation_zh`: Chinese legal statutes and regulatory basis.
* `has_image` (0 or 1) & `image_path`: Path to exam diagram (e.g., `images/<id>.jpg`).
* `difficulty` & `error_rate`: Difficulty rating and statistical failure percentage.
* `tags`: Searchable keywords (`points_12`, `signs_markings`, `speed_limits`, `expressway`, `fines_and_penalties`, etc.).
* `option_a_en`, `option_a_zh`, `option_b_en`, etc.: Denormalized options for quick querying.

### 2. `options` Table
Normalized table linking each option label (`A`, `B`, `C`, `D`) and text to `question_id`.

### 3. `user_history` & `bookmarks` Tables
Tracks test attempts (`user_answer`, `is_correct`, `answered_at`) and bookmarked questions.

### 4. Built-in Views
* `v_chapter_summary`: Breakdown of question count, question types, and image counts per chapter.
* `v_question_performance`: Performance summary showing correct/wrong counts per question.

---

## ⚡ Useful SQLite Query Examples

```sql
-- 1. Get all questions regarding 12-point penalty deductions:
SELECT question_num, question_en, answer, why_en 
FROM questions 
WHERE tags LIKE '%points_12%';

-- 2. Drill questions that feature road signs and images:
SELECT question_num, question_en, image_path, answer 
FROM questions 
WHERE has_image = 1 AND tags LIKE '%signs%';

-- 3. Review all questions you have answered incorrectly in practice:
SELECT q.question_num, q.question_en, q.answer, q.why_en, COUNT(h.id) AS mistakes
FROM questions q
JOIN user_history h ON q.id = h.question_id
WHERE h.is_correct = 0
GROUP BY q.id
ORDER BY mistakes DESC;
```

---

## 🎴 Importing into Anki

1. Open **Anki**.
2. Go to **File -> Import...** (or double-click **`China_Driving_Test_Subject_1.apkg`**).
3. The deck **`China Driving Test::Subject 1 (English)`** will appear with all 2,545 cards and images.
4. **Using Custom Study / Filtered Decks:**
   * In Anki, click **Tools -> Create Filtered Deck**.
   * Use search queries such as:
     * `tag:Topic::points_12` (Only 12-point deductions)
     * `tag:Topic::warning_signs` (Only warning signs)
     * `tag:Topic::speed_limits` (Speed limit questions)

---

## 🚀 How to Run Local Practice Tests

### Option A: In Your Web Browser (`index.html`)
Simply double-click or open **`index.html`** in any web browser (Chrome, Edge, Firefox, Safari).
* Works 100% offline (no web server required).
* **Sequential Practice Mode (Default):** Go through all 2,545 questions in order. Automatically tracks your progress, user choices, and accuracy in the local DB (`localStorage`), allowing you to navigate back and review past answers with explanations. Reset progress anytime with the **Reset Progress** button.
* **Non-Obvious Technical & Rules Drill (~1,166 questions):** Separate mode for high-memorization technical topics (speed limits, penalty points, fines/penalties, distances, dashboard instruments, ABS/mechanics, police hand signals), filtering out common-sense questions (e.g. stopping at stop signs, yielding to pedestrians).
* **100-Question Mock Exam with Clean Exit:** Timed 45-minute simulation with 90-point pass criteria. Includes an on-screen **Exit Exam** button to return to practice at any time without having to refresh the page.
* **No-Scroll Desktop/Laptop Layout:** Responsive side-by-side horizontal layout on desktop and laptop screens so questions, diagrams, and options all fit on screen without vertical scrolling, while preserving the vertical touch flow on mobile screens.
* Keyboard shortcuts (Left/Right arrow for Prev/Next, A/B/C/D or 1/2/3/4 to choose options).

### Option B: In the Terminal (`practice.py`)
Run the interactive console test:
```powershell
python practice.py
```
* **Mode 1:** Sequential Practice (Questions 1–2,545 in Order, with DB tracking & resume).
* **Mode 2:** Non-Obvious Technical & Rules Drill (~1,166 questions).
* **Mode 3:** 100-question official mock exam simulation.
* **Mode 4:** Practice specific topics (points, speed limits, signs, etc.).
* **Mode 5:** Practice specific chapters.
* **Mode 6:** Practice with images only (road signs, hand signals).
* **Mode 7:** Review missed / mistake questions from SQLite history.
* **Mode 8:** View study stats & accuracy.
* **Mode 9:** Reset user history in DB.
