import json
import os
import re
import sqlite3

def extract_tags(q):
    tags = set()
    
    chapter = q.get("chapter", "").lower()
    text_en = q.get("question_en", "").lower()
    text_zh = q.get("question_zh", "")
    why_en = q.get("why_en", "").lower()
    expl_zh = q.get("explanation_zh", "")
    
    all_text = f"{chapter} {text_en} {why_en}".lower()
    all_zh = f"{chapter} {text_zh} {expl_zh}"
    
    # Question type
    if q.get("type") == "judgement":
        tags.add("true_false")
    else:
        tags.add("multiple_choice")
        
    # Images
    if q.get("image"):
        tags.add("has_image")
    
    # Penalty Points
    if re.search(r'\b12[\s-]points?\b', all_text) or "12分" in all_zh or "记12分" in all_zh:
        tags.add("points_12")
        tags.add("penalty_points")
    elif re.search(r'\b9[\s-]points?\b', all_text) or "9分" in all_zh or "记9分" in all_zh:
        tags.add("points_9")
        tags.add("penalty_points")
    elif re.search(r'\b6[\s-]points?\b', all_text) or "6分" in all_zh or "记6分" in all_zh:
        tags.add("points_6")
        tags.add("penalty_points")
    elif re.search(r'\b3[\s-]points?\b', all_text) or "3分" in all_zh or "记3分" in all_zh:
        tags.add("points_3")
        tags.add("penalty_points")
    elif re.search(r'\b1[\s-]points?\b', all_text) or "1分" in all_zh or "记1分" in all_zh:
        tags.add("points_1")
        tags.add("penalty_points")
    elif "point" in all_text or "记分" in all_zh or "扣分" in all_zh:
        tags.add("penalty_points")

    # Signs and Markings
    if "sign" in all_text or "标志" in all_zh or "标线" in all_zh or "marking" in all_text:
        tags.add("signs_markings")
    if "warning sign" in all_text or "警告标志" in all_zh:
        tags.add("warning_signs")
    if "prohibition" in all_text or "禁令标志" in all_zh:
        tags.add("prohibition_signs")
    if "indication" in all_text or "guide sign" in all_text or "指示标志" in all_zh or "指路标志" in all_zh:
        tags.add("guide_signs")
        
    # Signals / Police Hand Signals / Lights
    if "traffic light" in all_text or "signal light" in all_text or "信号灯" in all_zh:
        tags.add("traffic_lights")
    if "gesture" in all_text or "hand signal" in all_text or "police" in all_text or "手势" in all_zh or "交警" in all_zh:
        tags.add("police_gestures")
        
    # Speeds
    if "speed" in all_text or "km/h" in all_text or "时速" in all_zh or "速度" in all_zh or "限速" in all_zh:
        tags.add("speed_limits")
        
    # Expressway / Highway
    if "expressway" in all_text or "highway" in all_text or "freeway" in all_text or "高速公路" in all_zh:
        tags.add("expressway")
        
    # Fines & Legal Penalties
    if "fine" in all_text or "yuan" in all_text or "detention" in all_text or "prison" in all_text or "revok" in all_text or "suspend" in all_text or "罚款" in all_zh or "拘留" in all_zh or "有期徒刑" in all_zh or "吊销" in all_zh:
        tags.add("fines_and_penalties")
        
    # Distance rules
    if re.search(r'\b\d+\s*meters?\b', all_text) or "米" in all_zh:
        tags.add("distances")
        
    # Emergency / Breakdowns / Accidents
    if "emergency" in all_text or "blowout" in all_text or "brake failure" in all_text or "skid" in all_text or "fire" in all_text or "accident" in all_text or "爆胎" in all_zh or "刹车" in all_zh or "制动失效" in all_zh or "事故" in all_zh:
        tags.add("emergency_accidents")
        
    # Night driving & Lights
    if "night" in all_text or "headlight" in all_text or "beam" in all_text or "夜间" in all_zh or "远光灯" in all_zh or "近光灯" in all_zh:
        tags.add("night_and_lights")
        
    # Dashboard & Vehicle controls
    if "dashboard" in all_text or "instrument" in all_text or "pedal" in all_text or "abs" in all_text or "steering" in all_text or "仪表" in all_zh or "指示灯" in all_zh:
        tags.add("vehicle_controls")

    return sorted(list(tags))


def check_is_technical(q, tags_list):
    """
    Classifies non-obvious technical questions (speed limits, penalties, points,
    distances, vehicle mechanics, dashboard instruments, and legal terminology).
    Filters out common-sense morality and obvious courtesy questions.
    """
    q_en = q.get("question_en", "")
    q_zh = q.get("question_zh", "")
    why = q.get("why_en", "")
    opt_texts = " ".join(o.get("text_en", "") for o in q.get("options", []))
    opt_texts_zh = " ".join(o.get("text_zh", "") for o in q.get("options", []))
    text = f"{q_en} {why} {opt_texts}".lower()
    zh = f"{q_zh} {opt_texts_zh}".lower()
    tags = set(tags_list)

    # 1. Technical tags
    if any(p in tags for p in ["points_12", "points_9", "points_6", "points_3", "points_1", "penalty_points"]):
        return 1
    if "speed_limits" in tags and any(k in text for k in ["limit", "maximum", "minimum", "exceed", "km/h", "speeding", "sign shows"]):
        return 1
    if "fines_and_penalties" in tags and any(k in text for k in ["fine", "yuan", "detention", "prison", "revocation", "suspend", "confiscat", "jail"]):
        return 1
    if "distances" in tags:
        return 1

    # 2. Specific numerical rules
    num_match = re.search(r'\b\d+\s*(km/h|meters?|yuan|points?|months?|years?|days?|hours?|%)\b', q_en, re.I)
    num_match_opt = re.search(r'\b\d+\s*(km/h|meters?|yuan|points?|months?|years?|days?|hours?|%)\b', opt_texts, re.I)
    num_match_zh = re.search(r'\d+\s*(公里/小时|公里|米|元|分|个月|年|日|天|小时|%|度)', zh)
    if num_match or num_match_opt or num_match_zh:
        return 1

    # 3. Hardware, dashboard & mechanics
    hardware_terms = [
        "abs", "anti-lock", "coolant", "dashboard", "tachometer", "odometer",
        "accelerator pedal", "clutch pedal", "brake pedal", "parking brake", "service brake",
        "engine brake", "retarder", "gearbox", "transmission", "high beam", "low beam",
        "fog lamp", "clearance light", "hazard warning flashers", "indicator light",
        "warning triangle", "tire blowout", "blowout", "skid", "steering wheel",
        "fuse", "windshield wiper", "defroster"
    ]
    for term in hardware_terms:
        if re.search(r'\b' + term + r'\b', text, re.I):
            return 1

    # 4. Legal procedures & technical terms
    legal_terms = [
        "revocation", "revoked", "detention", "detained", "registration", "deregistration",
        "probationary period", "demerit", "hand signal", "police gesture",
        "tidal lane", "variable direction", "deceleration marking", "minimum speed",
        "pledged", "scrap", "inspection certificate", "temporary license plate"
    ]
    for term in legal_terms:
        if re.search(r'\b' + term + r'\b', text, re.I):
            return 1

    # Chinese technical terms
    zh_terms = [
        "防抱死", "仪表", "转速", "水温", "离合", "手刹", "示廓灯", "危险报警闪光灯",
        "远光灯", "近光灯", "雾灯", "实习期", "吊销", "拘留", "暂扣", "注销", "核发", "审验",
        "手势", "潮汐车道", "变速", "导向车道", "报废", "抵押", "检验合格标志"
    ]
    for term in zh_terms:
        if term in zh:
            return 1

    return 0


def build_sqlite():
    json_path = os.path.join("data", "questions_bilingual.json")
    db_path = "china_driving_test.db"
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    print(f"Loading questions from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    print(f"Loaded {len(questions)} questions. Initializing database {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Main questions table
    cur.execute("""
    CREATE TABLE questions (
        id TEXT PRIMARY KEY,
        question_num INTEGER,
        chapter_id TEXT,
        chapter_en TEXT,
        chapter_zh TEXT,
        type TEXT,
        question_en TEXT NOT NULL,
        question_zh TEXT,
        answer TEXT NOT NULL,
        why_en TEXT,
        explanation_zh TEXT,
        has_image INTEGER DEFAULT 0,
        image_path TEXT,
        difficulty INTEGER,
        error_rate REAL,
        tags TEXT,
        is_technical INTEGER DEFAULT 0,
        option_a_en TEXT,
        option_a_zh TEXT,
        option_b_en TEXT,
        option_b_zh TEXT,
        option_c_en TEXT,
        option_c_zh TEXT,
        option_d_en TEXT,
        option_d_zh TEXT
    );
    """)
    
    # 2. Options table
    cur.execute("""
    CREATE TABLE options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT NOT NULL,
        label TEXT NOT NULL,
        text_en TEXT,
        text_zh TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)
    
    # 3. User history table (records test attempts)
    cur.execute("""
    CREATE TABLE user_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)
    
    # 4. User bookmarks/flags
    cur.execute("""
    CREATE TABLE bookmarks (
        question_id TEXT PRIMARY KEY,
        notes TEXT,
        flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)
    
    # Insert statements
    q_insert_sql = """
    INSERT INTO questions (
        id, question_num, chapter_id, chapter_en, chapter_zh, type,
        question_en, question_zh, answer, why_en, explanation_zh,
        has_image, image_path, difficulty, error_rate, tags, is_technical,
        option_a_en, option_a_zh, option_b_en, option_b_zh,
        option_c_en, option_c_zh, option_d_en, option_d_zh
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    
    opt_insert_sql = """
    INSERT INTO options (question_id, label, text_en, text_zh)
    VALUES (?, ?, ?, ?);
    """
    
    for idx, q in enumerate(questions, start=1):
        q_id = q["id"]
        chapter_raw = q.get("chapter", "")
        if " / " in chapter_raw:
            parts = chapter_raw.split(" / ", 1)
            ch_en, ch_zh = parts[0].strip(), parts[1].strip()
        else:
            ch_en, ch_zh = chapter_raw, ""
            
        img_path = q.get("image")
        has_img = 1 if img_path and os.path.exists(img_path) else 0
        
        tags_list = extract_tags(q)
        tags_str = ", ".join(tags_list)
        is_tech = check_is_technical(q, tags_list)
        
        # Parse options
        opt_map = {"A": ("", ""), "B": ("", ""), "C": ("", ""), "D": ("", "")}
        for opt in q.get("options", []):
            lbl = opt.get("label", "").upper()
            t_en = opt.get("text_en", "")
            t_zh = opt.get("text_zh", "")
            if lbl in opt_map:
                opt_map[lbl] = (t_en, t_zh)
            cur.execute(opt_insert_sql, (q_id, lbl, t_en, t_zh))
            
        cur.execute(q_insert_sql, (
            q_id,
            idx,
            str(q.get("chapter_id", "")),
            ch_en,
            ch_zh,
            q.get("type", ""),
            q.get("question_en", ""),
            q.get("question_zh", ""),
            q.get("answer", ""),
            q.get("why_en", ""),
            q.get("explanation_zh", ""),
            has_img,
            img_path if has_img else None,
            q.get("difficulty"),
            float(q.get("error_rate", 0.0)) if q.get("error_rate") is not None else None,
            tags_str,
            is_tech,
            opt_map["A"][0], opt_map["A"][1],
            opt_map["B"][0], opt_map["B"][1],
            opt_map["C"][0], opt_map["C"][1],
            opt_map["D"][0], opt_map["D"][1],
        ))
        
    # Create Indexes
    cur.execute("CREATE INDEX idx_questions_chapter ON questions(chapter_en);")
    cur.execute("CREATE INDEX idx_questions_type ON questions(type);")
    cur.execute("CREATE INDEX idx_questions_has_image ON questions(has_image);")
    cur.execute("CREATE INDEX idx_questions_tags ON questions(tags);")
    cur.execute("CREATE INDEX idx_questions_technical ON questions(is_technical);")
    cur.execute("CREATE INDEX idx_options_qid ON options(question_id);")
    cur.execute("CREATE INDEX idx_history_qid ON user_history(question_id);")
    
    # Create Views
    cur.execute("""
    CREATE VIEW v_chapter_summary AS
    SELECT 
        chapter_en,
        COUNT(*) AS total_questions,
        SUM(CASE WHEN type = 'judgement' THEN 1 ELSE 0 END) AS true_false_count,
        SUM(CASE WHEN type = 'single_choice' THEN 1 ELSE 0 END) AS multiple_choice_count,
        SUM(has_image) AS questions_with_images
    FROM questions
    GROUP BY chapter_en;
    """)
    
    cur.execute("""
    CREATE VIEW v_question_performance AS
    SELECT 
        q.id,
        q.question_num,
        q.question_en,
        q.answer,
        COUNT(h.id) AS total_attempts,
        SUM(CASE WHEN h.is_correct = 1 THEN 1 ELSE 0 END) AS correct_attempts,
        SUM(CASE WHEN h.is_correct = 0 THEN 1 ELSE 0 END) AS wrong_attempts
    FROM questions q
    LEFT JOIN user_history h ON q.id = h.question_id
    GROUP BY q.id;
    """)
    
    conn.commit()

    # Also export synced test_data.js for browser offline usage
    print("Exporting test_data.js for web interface...")
    conn.row_factory = sqlite3.Row
    export_cur = conn.cursor()
    export_cur.execute("SELECT * FROM questions ORDER BY question_num;")
    all_rows = [dict(r) for r in export_cur.fetchall()]
    with open("test_data.js", "w", encoding="utf-8") as f:
        f.write("window.QUESTIONS_DATA = " + json.dumps(all_rows, ensure_ascii=False) + ";\n")
    print(f"Exported {len(all_rows)} questions to test_data.js.")

    conn.close()
    print(f"Database build complete: {db_path} with {len(questions)} rows.")

if __name__ == "__main__":
    build_sqlite()
