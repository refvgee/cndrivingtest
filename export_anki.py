import html
import os
import sqlite3
import genanki

MODEL_ID = 1607392319
DECK_ID = 2059384721

# CSS styling compatible with both Light and Dark Anki modes
CARD_CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: #24292f;
  background-color: #ffffff;
  padding: 16px;
  max-width: 640px;
  margin: 0 auto;
}

.nightMode .card {
  color: #c9d1d9;
  background-color: #0d1117;
}

.badge-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge {
  padding: 3px 8px;
  border-radius: 12px;
  background: #e1e4e8;
  color: #444d56;
}

.nightMode .badge {
  background: #21262d;
  color: #8b949e;
}

.badge-type {
  background: #ddf4ff;
  color: #0969da;
}

.nightMode .badge-type {
  background: #033870;
  color: #58a6ff;
}

.img-container {
  text-align: center;
  margin: 14px 0;
}

.img-container img {
  max-width: 100%;
  max-height: 280px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  border: 1px solid #e1e4e8;
}

.nightMode .img-container img {
  border-color: #30363d;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.question-en {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #1f2328;
}

.nightMode .question-en {
  color: #f0f6fc;
}

.question-zh {
  font-size: 14px;
  color: #656d76;
  margin-bottom: 16px;
}

.nightMode .question-zh {
  color: #8b949e;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 16px 0;
}

.option-item {
  padding: 10px 14px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #f6f8fa;
  font-size: 15px;
}

.nightMode .option-item {
  border-color: #30363d;
  background: #161b22;
}

.option-correct {
  border: 2px solid #2da44e !important;
  background: #dafbe1 !important;
  color: #1a7f37 !important;
  font-weight: 600;
}

.nightMode .option-correct {
  border-color: #3fb950 !important;
  background: #0d381e !important;
  color: #3fb950 !important;
}

.answer-banner {
  margin: 16px 0;
  padding: 12px 16px;
  border-radius: 6px;
  background: #dafbe1;
  border-left: 4px solid #2da44e;
  font-size: 17px;
  font-weight: bold;
  color: #1a7f37;
}

.nightMode .answer-banner {
  background: #0d381e;
  border-color: #3fb950;
  color: #3fb950;
}

.section-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.45;
}

.section-why {
  background: #f0f7ff;
  border: 1px solid #b6e3ff;
  color: #0969da;
}

.nightMode .section-why {
  background: #071f38;
  border-color: #0d419d;
  color: #79c0ff;
}

.section-law {
  background: #f6f8fa;
  border: 1px solid #d0d7de;
  color: #57606a;
}

.nightMode .section-law {
  background: #161b22;
  border-color: #30363d;
  color: #8b949e;
}

.section-title {
  font-weight: bold;
  margin-bottom: 4px;
  display: block;
}
"""

FRONT_TEMPLATE = """
<div class="card">
  <div class="badge-row">
    <span class="badge">{{Chapter}}</span>
    <span class="badge badge-type">{{Type}}</span>
    <span class="badge">#{{QuestionNum}}</span>
  </div>

  {{#Image}}
  <div class="img-container">
    {{Image}}
  </div>
  {{/Image}}

  <div class="question-en">{{QuestionEN}}</div>
  {{#QuestionZH}}
  <div class="question-zh">{{QuestionZH}}</div>
  {{/QuestionZH}}

  <div class="options-list">
    {{{Options}}}
  </div>
</div>
"""

BACK_TEMPLATE = """
<div class="card">
  <div class="badge-row">
    <span class="badge">{{Chapter}}</span>
    <span class="badge badge-type">{{Type}}</span>
    <span class="badge">#{{QuestionNum}}</span>
  </div>

  {{#Image}}
  <div class="img-container">
    {{Image}}
  </div>
  {{/Image}}

  <div class="question-en">{{QuestionEN}}</div>
  {{#QuestionZH}}
  <div class="question-zh">{{QuestionZH}}</div>
  {{/QuestionZH}}

  <div class="answer-banner">
    Correct Answer: {{Answer}}
  </div>

  <div class="options-list">
    {{{OptionsWithAnswer}}}
  </div>

  {{#WhyEN}}
  <div class="section-box section-why">
    <span class="section-title">💡 Explanation:</span>
    {{WhyEN}}
  </div>
  {{/WhyEN}}

  {{#ExplanationZH}}
  <div class="section-box section-law">
    <span class="section-title">📜 Legal Basis / 法规:</span>
    {{ExplanationZH}}
  </div>
  {{/ExplanationZH}}
</div>
"""

def generate_anki_deck():
    db_path = "china_driving_test.db"
    apkg_output = "China_Driving_Test_Subject_1.apkg"
    
    print(f"Connecting to database {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
    SELECT 
        id, question_num, chapter_en, type, question_en, question_zh,
        answer, why_en, explanation_zh, has_image, image_path, tags,
        option_a_en, option_a_zh, option_b_en, option_b_zh,
        option_c_en, option_c_zh, option_d_en, option_d_zh
    FROM questions
    ORDER BY question_num ASC;
    """)
    rows = cur.fetchall()
    print(f"Fetched {len(rows)} questions from database.")
    
    my_model = genanki.Model(
        MODEL_ID,
        'China Driving Test (Subject 1) Model',
        fields=[
            {'name': 'Id'},
            {'name': 'QuestionNum'},
            {'name': 'Chapter'},
            {'name': 'Type'},
            {'name': 'QuestionEN'},
            {'name': 'QuestionZH'},
            {'name': 'Image'},
            {'name': 'Options'},
            {'name': 'Answer'},
            {'name': 'OptionsWithAnswer'},
            {'name': 'WhyEN'},
            {'name': 'ExplanationZH'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': FRONT_TEMPLATE,
                'afmt': BACK_TEMPLATE,
            },
        ],
        css=CARD_CSS
    )
    
    my_deck = genanki.Deck(
        DECK_ID,
        "China Driving Test::Subject 1 (English)"
    )
    
    media_files = []
    
    for r in rows:
        (
            q_id, q_num, ch_en, q_type, q_en, q_zh,
            answer, why_en, expl_zh, has_img, img_path, tags_str,
            opt_a_en, opt_a_zh, opt_b_en, opt_b_zh,
            opt_c_en, opt_c_zh, opt_d_en, opt_d_zh
        ) = r
        
        # Prepare tags: sanitize spaces into underscores
        tags = ["Subject_1"]
        ch_tag = "Chapter::" + ch_en.replace(" ", "_").replace("&", "and").replace(",", "")
        tags.append(ch_tag)
        
        if tags_str:
            for t in tags_str.split(", "):
                clean_t = t.strip().replace(" ", "_")
                if clean_t:
                    tags.append(f"Topic::{clean_t}")
                    
        # Image tag
        img_html = ""
        if has_img and img_path and os.path.exists(img_path):
            img_filename = os.path.basename(img_path)
            img_html = f'<img src="{img_filename}">'
            media_files.append(img_path)
            
        # Format options
        opts_front = []
        opts_back = []
        
        opt_data = [
            ("A", opt_a_en, opt_a_zh),
            ("B", opt_b_en, opt_b_zh),
            ("C", opt_c_en, opt_c_zh),
            ("D", opt_d_en, opt_d_zh),
        ]
        
        for lbl, t_en, t_zh in opt_data:
            if not t_en and not t_zh:
                continue
            zh_part = f' <span style="opacity:0.65;font-size:0.9em">({html.escape(t_zh)})</span>' if t_zh else ""
            content = f'<strong>{lbl}.</strong> {html.escape(t_en)}{zh_part}'
            
            opts_front.append(f'<div class="option-item">{content}</div>')
            
            is_correct = (lbl == answer)
            cls = "option-item option-correct" if is_correct else "option-item"
            prefix = "✔ " if is_correct else ""
            opts_back.append(f'<div class="{cls}">{prefix}{content}</div>')
            
        options_html = "\n".join(opts_front)
        options_with_ans_html = "\n".join(opts_back)
        
        type_display = "True / False" if q_type == "judgement" else "Multiple Choice"
        
        note = genanki.Note(
            model=my_model,
            fields=[
                str(q_id),
                str(q_num),
                html.escape(ch_en),
                type_display,
                html.escape(q_en),
                html.escape(q_zh) if q_zh else "",
                img_html,
                options_html,
                html.escape(answer),
                options_with_ans_html,
                html.escape(why_en) if why_en else "",
                html.escape(expl_zh) if expl_zh else "",
            ],
            tags=tags
        )
        my_deck.add_note(note)
        
    print(f"Total cards added to deck: {len(my_deck.notes)}")
    print(f"Packaging {len(media_files)} media files into {apkg_output}...")
    
    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files
    my_package.write_to_file(apkg_output)
    
    print(f"Successfully generated Anki deck: {apkg_output} ({os.path.getsize(apkg_output) / (1024*1024):.2f} MB)")
    conn.close()

if __name__ == "__main__":
    generate_anki_deck()
