import os
import random
import sqlite3
import sys
import time

DB_PATH = "china_driving_test.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def record_attempt(conn, question_id, user_answer, is_correct):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_history (question_id, user_answer, is_correct) VALUES (?, ?, ?);",
        (question_id, user_answer, 1 if is_correct else 0)
    )
    conn.commit()

def run_quiz(questions, title="Practice Session"):
    if not questions:
        print("\nNo questions found matching criteria.")
        return

    conn = get_connection()
    total = len(questions)
    correct_count = 0
    start_time = time.time()

    print("\n" + "=" * 65)
    print(f"  {title.upper()} — {total} Questions")
    print("  Controls: Enter choice letter (A/B/C/D), 'S' to skip, 'Q' to quit.")
    print("=" * 65 + "\n")

    for i, q in enumerate(questions, start=1):
        (
            q_id, q_num, ch_en, q_type, q_en, q_zh,
            ans, why_en, expl_zh, has_img, img_path, tags,
            opt_a_en, opt_a_zh, opt_b_en, opt_b_zh,
            opt_c_en, opt_c_zh, opt_d_en, opt_d_zh
        ) = q[:20]

        print("-" * 65)
        print(f"Question {i}/{total}  |  #{q_num}  |  Chapter: {ch_en}  |  Type: {q_type.replace('_', ' ').title()}")
        if has_img and img_path:
            abs_img = os.path.abspath(img_path)
            print(f"[IMAGE AVAILABLE: {abs_img}]")
        print(f"\n{q_en}")
        if q_zh:
            print(f"({q_zh})")
        print()

        options = [
            ("A", opt_a_en, opt_a_zh),
            ("B", opt_b_en, opt_b_zh),
            ("C", opt_c_en, opt_c_zh),
            ("D", opt_d_en, opt_d_zh),
        ]
        valid_choices = []
        for lbl, t_en, t_zh in options:
            if t_en or t_zh:
                valid_choices.append(lbl)
                zh_sub = f" ({t_zh})" if t_zh else ""
                print(f"  [{lbl}] {t_en}{zh_sub}")

        while True:
            try:
                user_choice = input("\nYour answer > ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\nSession aborted.")
                conn.close()
                return

            if user_choice == "Q":
                print("\nQuitting session...")
                conn.close()
                return
            if user_choice == "S":
                print("Skipped.")
                break
            if user_choice in valid_choices:
                break
            print(f"Invalid input. Please choose from: {', '.join(valid_choices)}, S (skip), or Q (quit).")

        if user_choice in valid_choices:
            is_correct = (user_choice == ans)
            record_attempt(conn, q_id, user_choice, is_correct)

            if is_correct:
                correct_count += 1
                print("\n✅ Correct!")
            else:
                print(f"\n❌ Incorrect! The correct answer is: [{ans}]")

            if why_en:
                print(f"💡 Explanation: {why_en}")
            if expl_zh:
                print(f"📖 Legal Basis: {expl_zh}")
            print()

    conn.close()
    elapsed = int(time.time() - start_time)
    minutes, seconds = divmod(elapsed, 60)
    score_pct = (correct_count / total) * 100 if total > 0 else 0

    print("\n" + "=" * 65)
    print("SESSION SUMMARY")
    print(f"Total Answered : {total}")
    print(f"Score          : {correct_count}/{total} ({score_pct:.1f}%)")
    print(f"Time Taken     : {minutes}m {seconds}s")
    if total >= 100:
        if score_pct >= 90.0:
            print("Status         : 🏆 PASSED (Official standard: >= 90%)")
        else:
            print("Status         : ❌ FAILED (Official standard: >= 90%)")
    print("=" * 65 + "\n")

def list_topics():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT tags FROM questions WHERE tags IS NOT NULL;")
    all_tags = set()
    for row in cur.fetchall():
        for t in row[0].split(", "):
            all_tags.add(t.strip())
    conn.close()
    return sorted(list(all_tags))

def show_statistics():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_history;")
    total_attempts = cur.fetchone()[0]

    cur.execute("SELECT SUM(is_correct) FROM user_history;")
    total_correct = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(DISTINCT question_id) 
        FROM user_history 
        WHERE is_correct = 0;
    """)
    mistakes_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT question_id) 
        FROM user_history;
    """)
    distinct_answered = cur.fetchone()[0]

    print("\n" + "=" * 45)
    print("        STUDY PROGRESS & STATS")
    print("=" * 45)
    print(f"Total questions in bank : 2,545")
    print(f"Unique questions attempted : {distinct_answered} / 2,545")
    print(f"Total answers logged    : {total_attempts}")
    if total_attempts > 0:
        acc = (total_correct / total_attempts) * 100
        print(f"Overall Accuracy        : {acc:.1f}% ({total_correct}/{total_attempts})")
        print(f"Unique questions missed : {mistakes_count}")
    else:
        print("No attempts recorded yet. Start practicing!")
    print("=" * 45 + "\n")
    conn.close()

def reset_history():
    confirm = input("⚠️ Are you sure you want to reset all test history in SQLite DB? (yes/no) > ").strip().lower()
    if confirm in ("yes", "y"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_history;")
        conn.commit()
        conn.close()
        print("✅ User history database has been reset.")
    else:
        print("Cancelled.")

def main():
    while True:
        print("\n" + "=" * 58)
        print("🇨🇳 CHINA DRIVING TEST — LOCAL PRACTICE (SUBJECT 1)")
        print("=" * 58)
        print("1. Sequential Practice (Questions 1–2,545 in Order, with DB tracking)")
        print("2. Non-Obvious Technical & Rules Drill (~1,117 questions)")
        print("3. Mock Official Exam (100 random questions, 90% to pass)")
        print("4. Practice by Topic (Penalty Points, Signs, Speeds, etc.)")
        print("5. Practice by Chapter")
        print("6. Practice with Images Only (Road signs, hand signals)")
        print("7. Review Missed / Mistake Questions")
        print("8. View Study Stats & Progress")
        print("9. Reset User History in DB")
        print("10. Exit")
        print("-" * 58)

        try:
            choice = input("Select an option (1-10) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "1":
            # Sequential practice with resume
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT MAX(q.question_num)
                FROM user_history uh
                JOIN questions q ON uh.question_id = q.id;
            """)
            last_qnum = cur.fetchone()[0] or 0
            start_num = 1
            if last_qnum > 0 and last_qnum < 2545:
                resume = input(f"You previously answered up to Question #{last_qnum}. Resume from #{last_qnum + 1}? (Y/n) > ").strip().lower()
                if resume not in ("n", "no"):
                    start_num = last_qnum + 1

            cur.execute("""
                SELECT 
                    id, question_num, chapter_en, type, question_en, question_zh,
                    answer, why_en, explanation_zh, has_image, image_path, tags,
                    option_a_en, option_a_zh, option_b_en, option_b_zh,
                    option_c_en, option_c_zh, option_d_en, option_d_zh
                FROM questions
                WHERE question_num >= ?
                ORDER BY question_num;
            """, (start_num,))
            questions = cur.fetchall()
            conn.close()
            run_quiz(questions, title=f"Sequential Practice (Starting from #{start_num})")

        elif choice == "2":
            # Non-obvious technical drill
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, question_num, chapter_en, type, question_en, question_zh,
                    answer, why_en, explanation_zh, has_image, image_path, tags,
                    option_a_en, option_a_zh, option_b_en, option_b_zh,
                    option_c_en, option_c_zh, option_d_en, option_d_zh
                FROM questions
                WHERE is_technical = 1
                ORDER BY question_num;
            """)
            questions = cur.fetchall()
            conn.close()
            run_quiz(questions, title=f"Non-Obvious Technical & Rules Drill ({len(questions)} Questions)")

        elif choice == "3":
            # 100 question mock exam
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, question_num, chapter_en, type, question_en, question_zh,
                    answer, why_en, explanation_zh, has_image, image_path, tags,
                    option_a_en, option_a_zh, option_b_en, option_b_zh,
                    option_c_en, option_c_zh, option_d_en, option_d_zh
                FROM questions
                ORDER BY RANDOM()
                LIMIT 100;
            """)
            questions = cur.fetchall()
            conn.close()
            run_quiz(questions, title="Official Simulation Mock Exam (100 Questions)")

        elif choice == "4":
            tags = list_topics()
            print("\nAvailable Topics:")
            for idx, t in enumerate(tags, start=1):
                print(f"  {idx:2d}. {t}")
            try:
                sub_choice = input("\nEnter topic number or name > ").strip()
                selected_tag = None
                if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(tags):
                    selected_tag = tags[int(sub_choice) - 1]
                elif sub_choice in tags:
                    selected_tag = sub_choice
                
                if selected_tag:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(f"""
                        SELECT 
                            id, question_num, chapter_en, type, question_en, question_zh,
                            answer, why_en, explanation_zh, has_image, image_path, tags,
                            option_a_en, option_a_zh, option_b_en, option_b_zh,
                            option_c_en, option_c_zh, option_d_en, option_d_zh
                        FROM questions
                        WHERE tags LIKE ?
                        ORDER BY question_num;
                    """, (f"%{selected_tag}%",))
                    questions = cur.fetchall()
                    conn.close()
                    run_quiz(questions, title=f"Topic Practice: {selected_tag}")
                else:
                    print("Invalid topic.")
            except (EOFError, KeyboardInterrupt):
                continue

        elif choice == "5":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT chapter_en FROM questions ORDER BY chapter_en;")
            chapters = [r[0] for r in cur.fetchall()]
            print("\nAvailable Chapters:")
            for idx, ch in enumerate(chapters, start=1):
                print(f"  {idx}. {ch}")
            try:
                sub_choice = input("\nEnter chapter number > ").strip()
                if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(chapters):
                    sel_ch = chapters[int(sub_choice) - 1]
                    cur.execute("""
                        SELECT 
                            id, question_num, chapter_en, type, question_en, question_zh,
                            answer, why_en, explanation_zh, has_image, image_path, tags,
                            option_a_en, option_a_zh, option_b_en, option_b_zh,
                            option_c_en, option_c_zh, option_d_en, option_d_zh
                        FROM questions
                        WHERE chapter_en = ?
                        ORDER BY question_num;
                    """, (sel_ch,))
                    questions = cur.fetchall()
                    conn.close()
                    run_quiz(questions, title=f"Chapter Practice: {sel_ch}")
                else:
                    conn.close()
                    print("Invalid chapter.")
            except (EOFError, KeyboardInterrupt):
                conn.close()
                continue

        elif choice == "6":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, question_num, chapter_en, type, question_en, question_zh,
                    answer, why_en, explanation_zh, has_image, image_path, tags,
                    option_a_en, option_a_zh, option_b_en, option_b_zh,
                    option_c_en, option_c_zh, option_d_en, option_d_zh
                FROM questions
                WHERE has_image = 1
                ORDER BY RANDOM();
            """)
            questions = cur.fetchall()
            conn.close()
            run_quiz(questions, title="Visual Exam Questions (Road Signs & Signals)")

        elif choice == "7":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    q.id, q.question_num, q.chapter_en, q.type, q.question_en, q.question_zh,
                    q.answer, q.why_en, q.explanation_zh, q.has_image, q.image_path, q.tags,
                    q.option_a_en, q.option_a_zh, q.option_b_en, q.option_b_zh,
                    q.option_c_en, q.option_c_zh, q.option_d_en, q.option_d_zh
                FROM questions q
                INNER JOIN (
                    SELECT question_id, MAX(id) as last_attempt_id 
                    FROM user_history 
                    GROUP BY question_id
                ) latest ON q.id = latest.question_id
                INNER JOIN user_history uh ON uh.id = latest.last_attempt_id
                WHERE uh.is_correct = 0;
            """)
            questions = cur.fetchall()
            conn.close()
            if not questions:
                print("\n🎉 You have no recorded mistakes! Great job.")
            else:
                run_quiz(questions, title=f"Mistake Review ({len(questions)} Missed Questions)")

        elif choice == "8":
            show_statistics()

        elif choice == "9":
            reset_history()

        elif choice == "10":
            print("\nGoodbye and safe driving!")
            break

if __name__ == "__main__":
    main()
