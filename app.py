import sqlite3
import os, re, json, urllib.request
from flask import Flask, jsonify, request, render_template
from ddgs import DDGS
from dotenv import load_dotenv
import markdown as md

load_dotenv()

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions'

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

# Ordered list of categories for the nav
CATEGORIES = ["图书馆", "食堂", "宿舍", "校园服务", "选课", "考试", "毕业要求", "奖学金", "德育积分", "综合素质实践", "社团", "其他"]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_tables():
    conn = get_db()
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
    ).fetchall()
    conn.close()
    return [r['name'] for r in rows]


@app.route('/')
def index():
    return render_template('index.html')


# Return list of categories (ordered) for frontend nav
@app.route('/api/categories')
def list_categories():
    existing = get_tables()
    ordered = [c for c in CATEGORIES if c in existing]
    return jsonify(ordered)


# GET /api/qa?category=xxx — fetch Q&A for a single category
@app.route('/api/qa')
def get_qa():
    category = request.args.get('category', '')
    if not category:
        return jsonify({'error': 'missing category'}), 400
    conn = get_db()
    rows = conn.execute(f'SELECT * FROM "{category}"').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# 从问题提取关键词（工具函数）
def extract_keywords(text):
    parts = re.split(r'[，。？\s,\.\?!、：:；;()（）【】\[\]「」{}]', text)
    keywords = [p for p in parts if len(p) >= 1 and p.strip()]
    stop_chars = {'的', '了', '是', '在', '有', '和', '就', '不', '也', '都', '而', '之',
                  '吗', '呢', '吧', '啊', '呀', '么', '我', '你', '他', '它',
                  '这', '那', '哪', '什', '怎', '谁', '几', '多', '很', '太',
                  '能', '会', '要', '去', '到', '上', '下', '大', '小', '个',
                  '为', '与', '及', '或', '做', '对', '被', '把', '让', '给'}
    chars = [c for c in text if '一' <= c <= '鿿' and c not in stop_chars]
    return keywords, chars


# 联网搜索（带重试和备用引擎）
def search_web(question, max_retries=2):
    """搜索互联网，返回 (搜索结果列表, 抓取页面列表)"""
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)

    keywords, _ = extract_keywords(question)
    # 从问题提取有意义的2字词作为搜索关键词
    kw_terms = [kw for kw in keywords if len(kw) >= 2][:5]

    web_results = []
    search_urls = set()

    # 多角度搜索查询
    search_queries = [
        f'北京交通大学 {question}',
        f'交大 {question}',
        f'bjtu {question}',
        question,
    ]
    # 加上关键词搜索
    for kw in kw_terms:
        search_queries.append(f'北京交通大学 {kw}')

    seen_titles = set()

    for attempt in range(max_retries):
        try:
            # 每次尝试不同 region
            regions = ['cn', 'wt-wt', 'hk']
            region = regions[attempt] if attempt < len(regions) else 'wt-wt'

            with DDGS() as ddgs:
                for sq in search_queries:
                    try:
                        for r in ddgs.text(sq, max_results=5, region=region):
                            title = r.get('title', '').strip()
                            body = r.get('body', '').strip()
                            href = r.get('href', '').strip()
                            if not title or title in seen_titles:
                                continue
                            seen_titles.add(title)
                            search_urls.add(href)
                            web_results.append({
                                'title': title,
                                'body': body,
                                'href': href,
                                'query': sq
                            })
                    except Exception:
                        continue
            # 如果成功拿到结果，跳出重试
            if web_results:
                break
        except Exception:
            continue

    # 抓取搜索结果页面的正文内容
    scraped_pages = []
    if search_urls:
        url_list = list(search_urls)[:5]
        for url in url_list:
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                resp = urllib.request.urlopen(req, timeout=8)
                html = resp.read().decode('utf-8', errors='ignore')
                text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                lines = [l.strip() for l in text.split('。') if l.strip() and len(l.strip()) > 20]
                content = '。'.join(lines[:50])
                if len(content) > 100:
                    scraped_pages.append(f"来源：{url}\n正文：{content[:2000]}")
            except Exception:
                continue

    return web_results, scraped_pages


# Chat search — 知识库 + 联网搜索 + DeepSeek AI
@app.route('/api/handbook', methods=['POST'])
def search_all():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'answer': '请输入问题。'})

    keywords, chars = extract_keywords(question)

    # ===== 1. 知识库检索 =====
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
    ).fetchall()

    kb_results = []
    for t in tables:
        name = t['name']
        try:
            rows = conn.execute(f'SELECT question, answer FROM "{name}"').fetchall()
            for row in rows:
                q_text, a_text = row['question'], row['answer']
                score = 0
                matched_kws = set()
                if question in q_text or q_text in question:
                    score += 100
                    matched_kws.add('exact_q')
                if question in a_text:
                    score += 80
                    matched_kws.add('exact_a')
                for kw in keywords:
                    if len(kw) < 2:
                        continue
                    if kw in q_text:
                        score += 15
                        matched_kws.add(kw)
                    elif kw in a_text:
                        score += 8
                        matched_kws.add(kw)
                for c in chars:
                    if c in q_text:
                        score += 2
                    elif c in a_text:
                        score += 1
                if score > 0:
                    kb_results.append({
                        'question': q_text,
                        'answer': a_text,
                        'category': name,
                        'score': score,
                        'hits': len(matched_kws)
                    })
        except sqlite3.OperationalError:
            pass
    conn.close()

    kb_results.sort(key=lambda r: (-r['score'], -r['hits'], len(r['question'])))
    top_kb = kb_results[:8]

    # ===== 2. 联网搜索 =====
    web_results, scraped_pages = search_web(question)

    # ===== 3. 构建 AI 上下文 =====
    context_parts = []
    source_info = None

    if top_kb:
        context_parts.append('【校园知识库】')
        for r in top_kb:
            context_parts.append(f"[{r['category']}] 问：{r['question']}\n答：{r['answer']}")
        source_info = top_kb[0]

    if web_results:
        context_parts.append(f'\n【互联网搜索结果（共{len(web_results)}条）】')
        for r in web_results[:15]:
            context_parts.append(f"标题：{r['title']}\n摘要：{r['body']}\n链接：{r['href']}")

    if scraped_pages:
        context_parts.append(f'\n【搜索结果页面详情（共{len(scraped_pages)}个页面）】')
        context_parts.extend(scraped_pages)

    system_prompt = '''你是北京交通大学（BJTU）校园智能助手。你的核心能力是结合知识库和实时联网搜索结果，回答关于北交大的各类问题。

回答原则：
1. 优先使用【校园知识库】的官方数据，这是学校提供的权威信息
2. 如果知识库信息不足，用【互联网搜索结果】补充最新、最全面的信息
3. 回答必须具体、翔实，给出数字、时间、地点等细节，不能笼统敷衍
4. 语气像热心的学长学姐，自然亲切
5. 如果信息来自互联网，在回答末尾标注"来源：互联网搜索"
6. 如果信息来自知识库，标注"来源：校园知识库"
7. 如果确实找不到相关信息，诚实告知用户，建议咨询辅导员或教务处

格式要求：
- 使用 Markdown 格式排版，让回答清晰易读
- 比较型数据（时间表、评分标准、对比项等）务必用表格展示
- 多个要点用无序列表（-）或有序列表（1. 2. 3.）
- 重要数字、时间、地点用 **加粗** 突出
- 段落之间用空行分隔，不要大段堆叠文字

注意：你的回答必须基于上面提供的上下文信息，不要编造数据。'''

    if context_parts:
        system_content = '\n'.join(context_parts) + '\n\n' + system_prompt
        messages = [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': question}
        ]
    else:
        messages = [
            {'role': 'system', 'content': system_prompt + '\n注意：当前没有搜索到相关信息，请如实告知用户无法回答。'},
            {'role': 'user', 'content': question}
        ]

    # ===== 4. 调用 DeepSeek AI =====
    try:
        body = json.dumps({
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.3,
            'max_tokens': 1000
        }).encode('utf-8')

        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
            }
        )
        resp = opener.open(req, timeout=60)
        result = json.loads(resp.read().decode('utf-8'))
        answer = result['choices'][0]['message']['content']
        answer_html = md.markdown(answer, extensions=['extra', 'nl2br'])

        return jsonify({
            'answer': answer,
            'answer_html': answer_html,
            'category': source_info['category'] if source_info else 'AI',
            'related': source_info['question'] if source_info else ''
        })
    except Exception as e:
        return jsonify({
            'answer': f'AI 服务暂时不可用，请稍后再试。（{str(e)}）'
        })


@app.route('/api/stats')
def get_stats():
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
    ).fetchall()

    total_categories = len(tables)
    total_qa = 0
    for t in tables:
        row = conn.execute(f'SELECT COUNT(*) as cnt FROM "{t["name"]}"').fetchone()
        total_qa += row['cnt']

    conn.close()
    return jsonify({
        'categories': total_categories,
        'total_qa': total_qa,
        'avg_per_category': round(total_qa / total_categories) if total_categories > 0 else 0
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000)
