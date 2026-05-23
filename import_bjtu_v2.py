"""
Extract Chinese text from BJTU PDFs using pymupdf xhtml output (which respects ToUnicode CMaps).
"""
import os, re, html
import fitz

DATA_DIR = os.path.expanduser('~/Desktop/bjtu')
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

CATEGORIES = ["图书馆", "食堂", "宿舍", "校园服务", "选课", "考试", "毕业要求", "奖学金", "德育积分", "综合素质实践", "社团", "其他", "专业培养方案"]

def extract_text_xhtml(path):
    """Extract text using xhtml mode which correctly handles CJK ToUnicode mappings."""
    doc = fitz.open(path)
    all_text = []
    for i in range(len(doc)):
        page = doc[i]
        # xhtml output uses HTML entities for proper Unicode
        xhtml = page.get_text('xhtml')
        # Parse HTML entities back to text
        # Extract text from HTML tags
        text = re.sub(r'<[^>]+>', ' ', xhtml)
        # Decode HTML entities like &#x4ea4;
        text = html.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        all_text.append(text)
    doc.close()
    return '\n'.join(all_text)

def extract_text_html(path):
    """Alternative: use html output mode."""
    doc = fitz.open(path)
    all_text = []
    for i in range(len(doc)):
        page = doc[i]
        html_text = page.get_text('html')
        text = re.sub(r'<[^>]+>', ' ', html_text)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        all_text.append(text)
    doc.close()
    return '\n'.join(all_text)

def extract_qa_from_text(text, filename):
    """Parse extracted text into Q&A pairs."""
    pairs = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return pairs

    school_name = os.path.splitext(filename)[0]

    # Try to find meaningful content
    # Look for patterns: sections, numbered items, question-like text
    current_q = None
    current_a = []

    for line in lines:
        # Skip very short or empty lines
        if len(line) < 3:
            continue

        is_header = False
        # Numbered sections like "一、", "1.", "(1)" etc
        if re.match(r'^[一二三四五六七八九十]+[、．.]', line):
            is_header = True
        if re.match(r'^\(\d+\)', line):
            is_header = True
        if re.match(r'^\d+[\.、．]', line):
            is_header = True
        # Lines ending with ：or :
        if line.endswith('：') or line.endswith(':'):
            is_header = True
        # Lines with ？or ?
        if '？' in line or '?' in line:
            is_header = True

        if is_header and len(line) < 150:
            if current_q and current_a:
                a = ' '.join(current_a).strip()
                if len(a) > 10:
                    pairs.append((current_q, a[:2000]))
            current_q = line
            current_a = []
        elif current_q:
            current_a.append(line)

    if current_q and current_a:
        a = ' '.join(current_a).strip()
        if len(a) > 10:
            pairs.append((current_q, a[:2000]))

    # If no structured pairs found, create an intro entry
    if not pairs and len(''.join(lines)) > 50:
        intro = ' '.join(lines[:20])[:1000]
        clean_name = school_name.replace('_', ' ').replace('-', ' ')
        pairs.append((f'{clean_name} 专业培养方案', intro))

    return pairs

def categorize(filename):
    """Categorize based on filename."""
    name = filename.lower()
    if '交通运输' in name: return '专业培养方案'
    if '经管' in name or '经济管理' in name: return '专业培养方案'
    if '计算机' in name: return '专业培养方案'
    if '自动化' in name: return '专业培养方案'
    if '电子' in name or '通信' in name or '信息' in name: return '专业培养方案'
    if '培养方案' in name: return '专业培养方案'
    if '双学' in name: return '专业培养方案'
    if '2021' in name: return '专业培养方案'
    if '2022' in name: return '专业培养方案'
    return '专业培养方案'

def write_to_db(all_pairs):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cat_name = '专业培养方案'

    cur.execute(f'''CREATE TABLE IF NOT EXISTS "{cat_name}" (
        id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, answer TEXT
    )''')

    existing = set()
    try:
        rows = cur.execute(f'SELECT question FROM "{cat_name}"').fetchall()
        existing = set(r[0] for r in rows)
    except: pass

    new = 0
    dup = 0
    for cat, pairs in all_pairs.items():
        for q, a in pairs:
            q = q.strip()[:200]
            a = a.strip()[:2000]
            if not q or not a or len(q) < 4 or len(a) < 4:
                continue
            if q in existing:
                dup += 1
                continue
            cur.execute(f'INSERT INTO "{cat_name}" (question, answer) VALUES (?, ?)', (q, a))
            existing.add(q)
            new += 1
    conn.commit()
    conn.close()
    return new, dup

if __name__ == '__main__':
    import sqlite3

    print("=" * 60)
    print("Extracting text from BJTU PDFs using XHTML mode")
    print("=" * 60)

    all_pairs = {}
    files = sorted([f for f in os.listdir(DATA_DIR)
                    if f.endswith(('.pdf', '.docx')) and os.path.isfile(os.path.join(DATA_DIR, f))])

    print(f"Found {len(files)} files")

    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"\n--- Processing: {fname} ---")

        try:
            if fname.endswith('.pdf'):
                text = extract_text_xhtml(fpath)
            elif fname.endswith('.docx'):
                from docx import Document
                doc = Document(fpath)
                text = '\n'.join(p.text for p in doc.paragraphs)
            else:
                continue

            print(f"  Extracted {len(text)} chars")
            print(f"  Preview: {text[:100]}")

            if len(text) < 20:
                print(f"  SKIP: too short")
                continue

            pairs = extract_qa_from_text(text, fname)
            cat = categorize(fname)
            if cat not in all_pairs:
                all_pairs[cat] = []
            all_pairs[cat].extend(pairs)
            print(f"  → {len(pairs)} Q&A pairs")

            # Print first pair as sample
            if pairs:
                print(f"  Sample Q: {pairs[0][0][:80]}")
                print(f"  Sample A: {pairs[0][1][:80]}")

        except Exception as e:
            print(f"  ERROR: {e}")

    total = sum(len(v) for v in all_pairs.values())
    print(f"\n\nTotal Q&A pairs: {total}")

    if total > 0:
        new, dup = write_to_db(all_pairs)
        print(f"Written to DB: {new} new, {dup} duplicates skipped")
    else:
        print("No data to write.")
