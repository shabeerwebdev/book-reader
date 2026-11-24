import os
import sys
import json
import zipfile
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

BASE_DIR = '/Users/shabeerahamed/Downloads/book'
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloaded_from_repo')
COVERS_DIR = os.path.join(BASE_DIR, 'covers')
os.makedirs(COVERS_DIR, exist_ok=True)

# -------------------------------------------------------------
# GENERIC HTML PARSER FOR CLEAN EDITORIAL READING
# -------------------------------------------------------------
class EditorialHTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.sections = []
        self.in_head = False
        self.in_h1 = False
        self.in_h2 = False
        self.heading_text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        elif tag == 'h1':
            self.in_h1 = True
            self.heading_text = []
        elif tag in ('h2', 'h3'):
            self.in_h2 = True
            self.heading_text = []
        elif not self.in_head:
            if tag == 'p':
                self.output.append('<p class="book-p">')
            elif tag == 'blockquote':
                self.output.append('<blockquote class="book-quote">')
            elif tag in ('em', 'i'):
                self.output.append('<em>')
            elif tag in ('strong', 'b'):
                self.output.append('<strong>')
            elif tag == 'br':
                self.output.append('<br/>')

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        elif tag == 'h1':
            self.in_h1 = False
        elif tag in ('h2', 'h3'):
            self.in_h2 = False
            t = ' '.join(''.join(self.heading_text).split())
            if t:
                clean_t = t.title()
                sec_id = 'sec-' + re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
                self.sections.append({'id': sec_id, 'title': clean_t})
                self.output.append(f'<h2 class="section-heading" id="{sec_id}">{clean_t}</h2>\n')
        elif not self.in_head:
            if tag == 'p':
                self.output.append('</p>\n')
            elif tag == 'blockquote':
                self.output.append('</blockquote>\n')
            elif tag in ('em', 'i'):
                self.output.append('</em>')
            elif tag in ('strong', 'b'):
                self.output.append('</strong>')

    def handle_data(self, data):
        if self.in_head:
            return
        if self.in_h1 or self.in_h2:
            self.heading_text.append(data)
        elif self.output and self.output[-1].startswith('<p') or (len(self.output) > 1 and not self.output[-1].endswith('\n')):
            self.output.append(data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        else:
            txt = data.strip()
            if txt and not txt.startswith('@page'):
                self.output.append(f'<p class="book-p">{txt}</p>\n')

# -------------------------------------------------------------
# 1. THINKING, FAST AND SLOW (OFFICIAL RETAIL PENGUIN EPUB)
# -------------------------------------------------------------
class TFSRetailHTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.sections = []
        self.in_head = False
        self.in_h2 = False
        self.in_section_heading = False
        self.heading_text = []
        self.in_caption = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "head":
            self.in_head = True
            return
        if self.in_head:
            return

        if tag == "h2":
            self.in_h2 = True
            return
        elif tag in ("h3", "h4", "h5"):
            self.in_section_heading = True
            self.heading_text = []
            return
        elif tag == "p":
            self.output.append('<p class="book-p">')
        elif tag == "blockquote":
            self.output.append('<blockquote class="book-quote">')
        elif tag in ("em", "i"):
            self.output.append('<em>')
        elif tag in ("strong", "b"):
            self.output.append('<strong>')
        elif tag == "br":
            self.output.append('<br/>')
        elif tag == "ul":
            self.output.append('<ul class="book-list">')
        elif tag == "ol":
            self.output.append('<ol class="book-list">')
        elif tag == "li":
            self.output.append('<li>')
        elif tag == "table":
            self.output.append('<div class="table-wrap"><table class="book-table">')
        elif tag == "tr":
            self.output.append('<tr>')
        elif tag in ("td", "th"):
            self.output.append(f'<{tag}>')
        elif tag == "div" and "caption" in attrs_dict.get("class", ""):
            self.in_caption = True
            self.output.append('<div class="caption">')
        elif tag == "img":
            src = attrs_dict.get("src", "")
            if "PCHI_1" not in src and "penguinLogo" not in src and "prhuklogo" not in src:
                fname = os.path.basename(src)
                self.output.append(f'<div class="figure-container"><img class="book-img" src="images/{fname}" alt="Illustration" /></div>')

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
            return
        if self.in_head:
            return

        if tag == "h2":
            self.in_h2 = False
            return
        elif tag in ("h3", "h4", "h5"):
            self.in_section_heading = False
            t = " ".join("".join(self.heading_text).split())
            if t:
                clean_t = t.title()
                sec_id = "sec-" + re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
                self.sections.append({"id": sec_id, "title": clean_t})
                self.output.append(f'<h2 class="section-heading" id="{sec_id}">{clean_t}</h2>\n')
            return
        elif tag == "p":
            self.output.append('</p>\n')
        elif tag == "blockquote":
            self.output.append('</blockquote>\n')
        elif tag in ("em", "i"):
            self.output.append('</em>')
        elif tag in ("strong", "b"):
            self.output.append('</strong>')
        elif tag == "ul":
            self.output.append('</ul>\n')
        elif tag == "ol":
            self.output.append('</ol>\n')
        elif tag == "li":
            self.output.append('</li>\n')
        elif tag == "table":
            self.output.append('</table></div>\n')
        elif tag == "tr":
            self.output.append('</tr>\n')
        elif tag in ("td", "th"):
            self.output.append(f'</{tag}>')
        elif tag == "div":
            if self.in_caption:
                self.in_caption = False
                self.output.append('</div>\n')

    def handle_data(self, data):
        if self.in_head or self.in_h2:
            return
        if self.in_section_heading:
            self.heading_text.append(data)
            return

        txt = data.strip()
        if not txt:
            if data and self.output and not self.output[-1].endswith("\n") and not self.output[-1].endswith(">"):
                self.output.append(" ")
            return

        cleaned = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if self.output and (self.output[-1].startswith("<p") or self.output[-1].startswith("<td") or self.output[-1].startswith("<th") or self.output[-1].startswith("<li") or self.output[-1].startswith("<div class=\"caption") or not self.output[-1].endswith("\n")):
            self.output.append(cleaned)
        else:
            self.output.append(f'<p class="book-p">{cleaned}</p>\n')

def get_tfs_data():
    tfs_epub_path = os.path.join(DOWNLOADS_DIR, 'thinking-fast-and-slow-retail.epub')
    tfs_spec = [
        {"id": "intro", "number": 0, "part": "Introduction", "title": "Introduction", "file": "OPS/xhtml/introduction.xhtml"},
        {"id": "ch01", "number": 1, "part": "Part 1: Two Systems", "title": "1: The Characters of the Story", "file": "OPS/xhtml/chapter001.xhtml"},
        {"id": "ch02", "number": 2, "part": "Part 1: Two Systems", "title": "2: Attention and Effort", "file": "OPS/xhtml/chapter002.xhtml"},
        {"id": "ch03", "number": 3, "part": "Part 1: Two Systems", "title": "3: The Lazy Controller", "file": "OPS/xhtml/chapter003.xhtml"},
        {"id": "ch04", "number": 4, "part": "Part 1: Two Systems", "title": "4: The Associative Machine", "file": "OPS/xhtml/chapter004.xhtml"},
        {"id": "ch05", "number": 5, "part": "Part 1: Two Systems", "title": "5: Cognitive Ease", "file": "OPS/xhtml/chapter005.xhtml"},
        {"id": "ch06", "number": 6, "part": "Part 1: Two Systems", "title": "6: Norms, Surprises, and Causes", "file": "OPS/xhtml/chapter006.xhtml"},
        {"id": "ch07", "number": 7, "part": "Part 1: Two Systems", "title": "7: A Machine for Jumping to Conclusions", "file": "OPS/xhtml/chapter007.xhtml"},
        {"id": "ch08", "number": 8, "part": "Part 1: Two Systems", "title": "8: How Judgments Happen", "file": "OPS/xhtml/chapter008.xhtml"},
        {"id": "ch09", "number": 9, "part": "Part 1: Two Systems", "title": "9: Answering an Easier Question", "file": "OPS/xhtml/chapter009.xhtml"},
        {"id": "ch10", "number": 10, "part": "Part 2: Heuristics and Biases", "title": "10: The Law of Small Numbers", "file": "OPS/xhtml/chapter010.xhtml"},
        {"id": "ch11", "number": 11, "part": "Part 2: Heuristics and Biases", "title": "11: Anchors", "file": "OPS/xhtml/chapter011.xhtml"},
        {"id": "ch12", "number": 12, "part": "Part 2: Heuristics and Biases", "title": "12: The Science of Availability", "file": "OPS/xhtml/chapter012.xhtml"},
        {"id": "ch13", "number": 13, "part": "Part 2: Heuristics and Biases", "title": "13: Availability, Emotion, and Risk", "file": "OPS/xhtml/chapter013.xhtml"},
        {"id": "ch14", "number": 14, "part": "Part 2: Heuristics and Biases", "title": "14: Tom W’s Specialty", "file": "OPS/xhtml/chapter014.xhtml"},
        {"id": "ch15", "number": 15, "part": "Part 2: Heuristics and Biases", "title": "15: Linda: Less is More", "file": "OPS/xhtml/chapter015.xhtml"},
        {"id": "ch16", "number": 16, "part": "Part 2: Heuristics and Biases", "title": "16: Causes Trump Statistics", "file": "OPS/xhtml/chapter016.xhtml"},
        {"id": "ch17", "number": 17, "part": "Part 2: Heuristics and Biases", "title": "17: Regression to the Mean", "file": "OPS/xhtml/chapter017.xhtml"},
        {"id": "ch18", "number": 18, "part": "Part 2: Heuristics and Biases", "title": "18: Taming Intuitive Predictions", "file": "OPS/xhtml/chapter018.xhtml"},
        {"id": "ch19", "number": 19, "part": "Part 3: Overconfidence", "title": "19: The Illusion of Understanding", "file": "OPS/xhtml/chapter019.xhtml"},
        {"id": "ch20", "number": 20, "part": "Part 3: Overconfidence", "title": "20: The Illusion of Validity", "file": "OPS/xhtml/chapter020.xhtml"},
        {"id": "ch21", "number": 21, "part": "Part 3: Overconfidence", "title": "21: Intuitions vs. Formulas", "file": "OPS/xhtml/chapter021.xhtml"},
        {"id": "ch22", "number": 22, "part": "Part 3: Overconfidence", "title": "22: Expert Intuition: When Can We Trust It?", "file": "OPS/xhtml/chapter022.xhtml"},
        {"id": "ch23", "number": 23, "part": "Part 3: Overconfidence", "title": "23: The Outside View", "file": "OPS/xhtml/chapter023.xhtml"},
        {"id": "ch24", "number": 24, "part": "Part 3: Overconfidence", "title": "24: The Engine of Capitalism", "file": "OPS/xhtml/chapter024.xhtml"},
        {"id": "ch25", "number": 25, "part": "Part 4: Choices", "title": "25: Bernoulli’s Errors", "file": "OPS/xhtml/chapter025.xhtml"},
        {"id": "ch26", "number": 26, "part": "Part 4: Choices", "title": "26: Prospect Theory", "file": "OPS/xhtml/chapter026.xhtml"},
        {"id": "ch27", "number": 27, "part": "Part 4: Choices", "title": "27: The Endowment Effect", "file": "OPS/xhtml/chapter027.xhtml"},
        {"id": "ch28", "number": 28, "part": "Part 4: Choices", "title": "28: Bad Events", "file": "OPS/xhtml/chapter028.xhtml"},
        {"id": "ch29", "number": 29, "part": "Part 4: Choices", "title": "29: The Fourfold Pattern", "file": "OPS/xhtml/chapter029.xhtml"},
        {"id": "ch30", "number": 30, "part": "Part 4: Choices", "title": "30: Rare Events", "file": "OPS/xhtml/chapter030.xhtml"},
        {"id": "ch31", "number": 31, "part": "Part 4: Choices", "title": "31: Risk Policies", "file": "OPS/xhtml/chapter031.xhtml"},
        {"id": "ch32", "number": 32, "part": "Part 4: Choices", "title": "32: Keeping Score", "file": "OPS/xhtml/chapter032.xhtml"},
        {"id": "ch33", "number": 33, "part": "Part 4: Choices", "title": "33: Reversals", "file": "OPS/xhtml/chapter033.xhtml"},
        {"id": "ch34", "number": 34, "part": "Part 4: Choices", "title": "34: Frames and Reality", "file": "OPS/xhtml/chapter034.xhtml"},
        {"id": "ch35", "number": 35, "part": "Part 5: Two Selves", "title": "35: Two Selves", "file": "OPS/xhtml/chapter035.xhtml"},
        {"id": "ch36", "number": 36, "part": "Part 5: Two Selves", "title": "36: Life as a Story", "file": "OPS/xhtml/chapter036.xhtml"},
        {"id": "ch37", "number": 37, "part": "Part 5: Two Selves", "title": "37: Experienced Well-Being", "file": "OPS/xhtml/chapter037.xhtml"},
        {"id": "ch38", "number": 38, "part": "Part 5: Two Selves", "title": "38: Thinking About Life", "file": "OPS/xhtml/chapter038.xhtml"},
        {"id": "conclusions", "number": 39, "part": "Conclusions", "title": "Conclusions", "file": "OPS/xhtml/conclusions.xhtml"},
        {"id": "app_a", "number": 40, "part": "Appendices", "title": "Appendix A: Judgment Under Uncertainty: Heuristics and Biases", "file": "OPS/xhtml/appendix001.xhtml"},
        {"id": "app_b", "number": 41, "part": "Appendices", "title": "Appendix B: Choices, Values, and Frames", "file": "OPS/xhtml/appendix002.xhtml"}
    ]

    chapters = []
    total_words = 0

    with zipfile.ZipFile(tfs_epub_path) as z:
        for ch in tfs_spec:
            parser = TFSRetailHTMLCleaner()
            parser.feed(z.read(ch["file"]).decode('utf-8', errors='ignore'))
            body_html = ''.join(parser.output)

            words = len(re.sub(r'<[^>]+>', ' ', body_html).split())
            total_words += words
            read_time = max(1, round(words / 220))

            header_html = f'''
        <header class="chapter-header" id="sec-top">
          <div class="part-badge">{ch['part']}</div>
          <h1 class="chapter-title">{ch['title']}</h1>
          <div class="chapter-meta">
            <span>Daniel Kahneman</span> • <span class="ch-time-est">{read_time} min read</span>
          </div>
        </header>
'''
            chapters.append({
                'id': ch['id'],
                'number': ch['number'],
                'part': ch['part'],
                'title': ch['title'],
                'words': words,
                'readTime': read_time,
                'sections': parser.sections,
                'content': header_html + '\n' + body_html
            })

    tfs_book = {
        'id': 'thinking-fast-and-slow',
        'title': "Thinking, Fast and Slow",
        'author': "Daniel Kahneman",
        'cover': 'covers/cover_tfs.jpeg',
        'totalChapters': len(chapters),
        'totalWords': total_words,
        'parts': ["Introduction", "Part 1: Two Systems", "Part 2: Heuristics and Biases", "Part 3: Overconfidence", "Part 4: Choices", "Part 5: Two Selves", "Conclusions", "Appendices"],
        'chapters': chapters
    }

    with open(os.path.join(BASE_DIR, 'book_data.json'), 'w', encoding='utf-8') as f:
        json.dump(tfs_book, f, ensure_ascii=False)

    return tfs_book

# -------------------------------------------------------------
# 2. MAN'S SEARCH FOR MEANING
# -------------------------------------------------------------
def get_msm_data():
    msm_path = os.path.join(DOWNLOADS_DIR, 'mans-search-for-meaning.epub')
    with zipfile.ZipFile(msm_path) as z:
        chapters_spec = [
            {'id': 'frw', 'number': 1, 'part': 'Front Matter', 'title': 'Foreword by Harold S. Kushner', 'files': ['OEBPS/Text/Fran_9780807014288_epub_frw_r1.htm']},
            {'id': 'prf', 'number': 2, 'part': 'Front Matter', 'title': 'Preface to the 1992 Edition', 'files': ['OEBPS/Text/Fran_9780807014288_epub_prf_r1.htm']},
            {'id': 'c01', 'number': 3, 'part': 'Part One', 'title': 'Experiences in a Concentration Camp', 'files': ['OEBPS/Text/Fran_9780807014288_epub_c01_r1.htm']},
            {'id': 'c02', 'number': 4, 'part': 'Part Two', 'title': 'Logotherapy in a Nutshell', 'files': ['OEBPS/Text/Fran_9780807014288_epub_c02_r1.htm']},
            {'id': 'c03', 'number': 5, 'part': 'Part Three', 'title': 'The Case for a Tragic Optimism (Postscript 1984)', 'files': ['OEBPS/Text/Fran_9780807014288_epub_c03_r1.htm']},
            {'id': 'aft', 'number': 6, 'part': 'Afterword', 'title': 'Afterword by William J. Winslade', 'files': ['OEBPS/Text/Fran_9780807014288_epub_aft_r1.htm']}
        ]

        chapters = []
        total_words = 0

        for ch_info in chapters_spec:
            parser = EditorialHTMLCleaner()
            for f in ch_info['files']:
                parser.feed(z.read(f).decode('utf-8', errors='ignore'))
            body_html = ''.join(parser.output)

            if ch_info['id'] == 'c01':
                sections = [
                    {'id': 'sec-phase-1', 'title': 'Phase One: Admission & The Initial Shock'},
                    {'id': 'sec-phase-2', 'title': 'Phase Two: Entrenchment & Emotional Apathy'},
                    {'id': 'sec-phase-3', 'title': 'Phase Three: Liberation & Psychological Release'}
                ]
                sub_pos = body_html.find("the blunting of the emotions")
                if sub_pos > 0:
                    prev_p = body_html.rfind('<p class="book-p">', 0, sub_pos)
                    if prev_p != -1:
                        body_html = body_html[:prev_p] + '<h2 class="section-heading" id="sec-phase-2">Phase Two: Entrenchment &amp; Emotional Apathy</h2>\n' + body_html[prev_p:]
                sub_pos3 = body_html.find("the psychology of the prisoner after his liberation")
                if sub_pos3 > 0:
                    prev_p3 = body_html.rfind('<p class="book-p">', 0, sub_pos3)
                    if prev_p3 != -1:
                        body_html = body_html[:prev_p3] + '<h2 class="section-heading" id="sec-phase-3">Phase Three: Liberation &amp; Psychological Release</h2>\n' + body_html[prev_p3:]
            else:
                sections = parser.sections

            words = len(re.sub(r'<[^>]+>', ' ', body_html).split())
            total_words += words
            read_time = max(1, round(words / 220))

            header_html = f'''
        <header class="chapter-header" id="sec-top">
          <div class="part-badge">{ch_info['part']}</div>
          <h1 class="chapter-title">{ch_info['title']}</h1>
          <div class="chapter-meta">
            <span>Viktor E. Frankl</span> • <span class="ch-time-est">{read_time} min read</span>
          </div>
        </header>
'''
            chapters.append({
                'id': ch_info['id'],
                'number': ch_info['number'],
                'part': ch_info['part'],
                'title': ch_info['title'],
                'words': words,
                'readTime': read_time,
                'sections': sections,
                'content': header_html + '\n' + body_html
            })

        return {
            'id': 'mans-search-for-meaning',
            'title': "Man's Search for Meaning",
            'author': "Viktor E. Frankl",
            'cover': 'covers/cover_msm.jpg',
            'totalChapters': len(chapters),
            'totalWords': total_words,
            'parts': ["Front Matter", "Part One", "Part Two", "Part Three", "Afterword"],
            'chapters': chapters
        }

# -------------------------------------------------------------
# 3. THE POWER OF NOW
# -------------------------------------------------------------
def get_pon_data():
    pon_path = os.path.join(DOWNLOADS_DIR, 'power-of-now-150.epub')
    with zipfile.ZipFile(pon_path) as z:
        chapters_spec = [
            {'id': 'foreword', 'number': 0, 'part': 'Front Matter', 'title': 'Foreword by Russell E. DiCarlo', 'files': ['OEBPS/part2.xhtml']},
            {'id': 'intro', 'number': 0, 'part': 'Introduction', 'title': 'Introduction', 'files': ['OEBPS/part4.xhtml', 'OEBPS/part5_split_000.xhtml', 'OEBPS/part5_split_001.xhtml', 'OEBPS/part6.xhtml']},
            {'id': 'ch01', 'number': 1, 'part': 'Presence & Pain', 'title': '1. You Are Not Your Mind', 'files': [f'OEBPS/part{i}.xhtml' for i in range(7, 13)] + ['OEBPS/part7_split_000.xhtml', 'OEBPS/part7_split_001.xhtml']},
            {'id': 'ch02', 'number': 2, 'part': 'Presence & Pain', 'title': '2. Consciousness: The Way Out of Pain', 'files': ['OEBPS/part13_split_000.xhtml', 'OEBPS/part13_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(14, 20)]},
            {'id': 'ch03', 'number': 3, 'part': 'The Now Dimension', 'title': '3. Moving Deeply into the Now', 'files': ['OEBPS/part20_split_000.xhtml', 'OEBPS/part20_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(21, 34)]},
            {'id': 'ch04', 'number': 4, 'part': 'The Now Dimension', 'title': '4. Mind Strategies for Avoiding the Now', 'files': ['OEBPS/part34_split_000.xhtml', 'OEBPS/part34_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(35, 44)]},
            {'id': 'ch05', 'number': 5, 'part': 'Inner Realities', 'title': '5. The State of Presence', 'files': ['OEBPS/part44_split_000.xhtml', 'OEBPS/part44_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(45, 51)]},
            {'id': 'ch06', 'number': 6, 'part': 'Inner Realities', 'title': '6. The Inner Body', 'files': ['OEBPS/part51_split_000.xhtml', 'OEBPS/part51_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(52, 67)]},
            {'id': 'ch07', 'number': 7, 'part': 'Inner Realities', 'title': '7. Portals into the Unmanifested', 'files': ['OEBPS/part67_split_000.xhtml', 'OEBPS/part67_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(68, 77)]},
            {'id': 'ch08', 'number': 8, 'part': 'Spiritual Practice', 'title': '8. Enlightened Relationships', 'files': ['OEBPS/part77_split_000.xhtml', 'OEBPS/part77_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(78, 86)]},
            {'id': 'ch09', 'number': 9, 'part': 'Spiritual Practice', 'title': '9. Beyond Happiness and Unhappiness', 'files': ['OEBPS/part86_split_000.xhtml', 'OEBPS/part86_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(87, 94)]},
            {'id': 'ch10', 'number': 10, 'part': 'Surrender', 'title': '10. The Meaning of Surrender', 'files': ['OEBPS/part94_split_000.xhtml', 'OEBPS/part94_split_001.xhtml'] + [f'OEBPS/part{i}.xhtml' for i in range(95, 104)]}
        ]

        chapters = []
        total_words = 0
        all_names = z.namelist()

        for ch_info in chapters_spec:
            parser = EditorialHTMLCleaner()
            valid_files = [f for f in ch_info['files'] if f in all_names]
            def file_sort_key(name):
                m = re.search(r'part(\d+)(?:_split_(\d+))?', name)
                if m:
                    return (int(m.group(1)), int(m.group(2)) if m.group(2) else 0)
                return (999, 0)
            valid_files.sort(key=file_sort_key)

            for f in valid_files:
                parser.feed(z.read(f).decode('utf-8', errors='ignore'))
            body_html = ''.join(parser.output)

            clean_sections = [s for s in parser.sections if s['title'].lower() not in ch_info['title'].lower()]
            words = len(re.sub(r'<[^>]+>', ' ', body_html).split())
            total_words += words
            read_time = max(1, round(words / 220))

            header_html = f'''
        <header class="chapter-header" id="sec-top">
          <div class="part-badge">{ch_info['part']}</div>
          <h1 class="chapter-title">{ch_info['title']}</h1>
          <div class="chapter-meta">
            <span>Eckhart Tolle</span> • <span class="ch-time-est">{read_time} min read</span>
          </div>
        </header>
'''
            chapters.append({
                'id': ch_info['id'],
                'number': ch_info['number'],
                'part': ch_info['part'],
                'title': ch_info['title'],
                'words': words,
                'readTime': read_time,
                'sections': clean_sections,
                'content': header_html + '\n' + body_html
            })

        return {
            'id': 'the-power-of-now',
            'title': "The Power of Now",
            'author': "Eckhart Tolle",
            'cover': 'covers/cover_pon.jpeg',
            'totalChapters': len(chapters),
            'totalWords': total_words,
            'parts': ["Front Matter", "Introduction", "Presence & Pain", "The Now Dimension", "Inner Realities", "Spiritual Practice", "Surrender"],
            'chapters': chapters
        }

# -------------------------------------------------------------
# 4. GENERIC EPUB IMPORT (FOR ANY FUTURE BOOK DROPPED IN)
# -------------------------------------------------------------
def import_generic_epub(epub_path):
    print(f"Importing generic EPUB: {epub_path}")
    book_slug = re.sub(r'[^a-z0-9]+', '-', os.path.basename(epub_path).lower().replace('.epub', '')).strip('-')
    
    with zipfile.ZipFile(epub_path) as z:
        # Find OPF
        container = ET.fromstring(z.read('META-INF/container.xml'))
        rootfile = container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        opf_path = rootfile.get('full-path')
        base_dir = opf_path.rsplit('/', 1)[0] if '/' in opf_path else ''

        opf = ET.fromstring(z.read(opf_path))
        title_el = opf.find('.//{http://purl.org/dc/elements/1.1/}title')
        creator_el = opf.find('.//{http://purl.org/dc/elements/1.1/}creator')

        title = title_el.text if title_el is not None and title_el.text else book_slug.replace('-', ' ').title()
        author = creator_el.text if creator_el is not None and creator_el.text else "Unknown Author"

        # Manifest
        manifest = {}
        for it in opf.findall('.//{http://www.idpf.org/2007/opf}item'):
            href = it.get('href')
            full_href = (base_dir + '/' + href).lstrip('/') if base_dir else href
            manifest[it.get('id')] = full_href

        # Spine
        spine = [it.get('idref') for it in opf.findall('.//{http://www.idpf.org/2007/opf}itemref')]

        # Extract cover if present
        cover_path = None
        for it in opf.findall('.//{http://www.idpf.org/2007/opf}item'):
            media = it.get('media-type', '')
            prop = it.get('properties', '')
            item_id = it.get('id', '')
            if 'image' in media and ('cover' in item_id.lower() or 'cover' in prop.lower()):
                href = it.get('href')
                full_href = (base_dir + '/' + href).lstrip('/') if base_dir else href
                cover_dest = f"covers/cover_{book_slug}.jpg"
                with open(os.path.join(BASE_DIR, cover_dest), 'wb') as f_out:
                    f_out.write(z.read(full_href))
                cover_path = cover_dest
                break

        if not cover_path:
            cover_path = "covers/cover_tfs.jpeg"

        # Extract Chapters from Spine
        chapters = []
        total_words = 0
        ch_idx = 0

        for idref in spine:
            fname = manifest.get(idref)
            if not fname or not fname.lower().endswith(('.html', '.xhtml', '.htm')):
                continue

            raw = z.read(fname).decode('utf-8', errors='ignore')
            parser = EditorialHTMLCleaner()
            parser.feed(raw)
            body_html = ''.join(parser.output)
            words = len(re.sub(r'<[^>]+>', ' ', body_html).split())
            if words < 80:  # skip blank spacer pages
                continue

            ch_idx += 1
            ch_title = f"Section {ch_idx}"
            if parser.sections:
                ch_title = parser.sections[0]['title']
            
            read_time = max(1, round(words / 220))
            total_words += words

            header_html = f'''
        <header class="chapter-header" id="sec-top">
          <div class="part-badge">Chapter {ch_idx}</div>
          <h1 class="chapter-title">{ch_title}</h1>
          <div class="chapter-meta">
            <span>{author}</span> • <span class="ch-time-est">{read_time} min read</span>
          </div>
        </header>
'''
            chapters.append({
                'id': f"ch_{ch_idx}",
                'number': ch_idx,
                'part': f"Part {((ch_idx-1)//10)+1}",
                'title': ch_title,
                'words': words,
                'readTime': read_time,
                'sections': parser.sections,
                'content': header_html + '\n' + body_html
            })

        new_book_data = {
            'id': book_slug,
            'title': title,
            'author': author,
            'cover': cover_path,
            'totalChapters': len(chapters),
            'totalWords': total_words,
            'parts': list(set(ch['part'] for ch in chapters)),
            'chapters': chapters
        }

        # Add to existing library
        with open(os.path.join(BASE_DIR, 'library.json'), 'r', encoding='utf-8') as f:
            lib = json.load(f)
        
        # Remove if exists
        lib = [b for b in lib if b['id'] != book_slug]
        lib.append({
            'id': book_slug,
            'title': title,
            'author': author,
            'cover': cover_path,
            'totalChapters': len(chapters),
            'totalWords': total_words,
            'parts': new_book_data['parts'],
            'description': f"Added via Generic EPUB Importer: {title} by {author}."
        })

        with open(os.path.join(BASE_DIR, 'library.json'), 'w', encoding='utf-8') as f:
            json.dump(lib, f, indent=2)

        # Update book_data.js
        with open(os.path.join(BASE_DIR, 'book_data.js'), 'r', encoding='utf-8') as f:
            js_txt = f.read()

        # extract JSON
        m = re.search(r'window\.LIBRARY_BOOKS = (\{.*?\});', js_txt, re.S)
        if m:
            lib_dict = json.loads(m.group(1))
            lib_dict[book_slug] = new_book_data
            with open(os.path.join(BASE_DIR, 'book_data.js'), 'w', encoding='utf-8') as f:
                f.write('// Auto-generated library containing all verified books\n')
                f.write('window.LIBRARY_BOOKS = ')
                json.dump(lib_dict, f, ensure_ascii=False)
                f.write(';\n\n')
                f.write('// Default book for single-book backwards compatibility\n')
                f.write(f'window.BOOK_DATA = window.LIBRARY_BOOKS["{book_slug}"];\n')
            print(f"Successfully added '{title}' ({len(chapters)} chapters, {total_words} words) to library!")

# -------------------------------------------------------------
# MAIN BUILD OR IMPORT
# -------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'import':
        import_generic_epub(sys.argv[2])
    else:
        print("Building full standard 3-book library...")
        tfs = get_tfs_data()
        msm = get_msm_data()
        pon = get_pon_data()

        library_dict = {
            tfs['id']: tfs,
            msm['id']: msm,
            pon['id']: pon
        }

        library_manifest = [
            {
                'id': tfs['id'],
                'title': tfs['title'],
                'author': tfs['author'],
                'cover': tfs['cover'],
                'totalChapters': tfs['totalChapters'],
                'totalWords': sum(ch['words'] for ch in tfs['chapters']),
                'parts': tfs.get('parts', []),
                'description': "A masterwork on behavioral economics, cognitive biases, System 1 and System 2 thinking, and how human intuition diverges from statistical rationality."
            },
            {
                'id': msm['id'],
                'title': msm['title'],
                'author': msm['author'],
                'cover': msm['cover'],
                'totalChapters': msm['totalChapters'],
                'totalWords': msm['totalWords'],
                'parts': msm['parts'],
                'description': "Frankl's enduring classic on his experiences surviving Auschwitz and Dachau, articulating logotherapy and finding ultimate purpose in any circumstance."
            },
            {
                'id': pon['id'],
                'title': pon['title'],
                'author': pon['author'],
                'cover': pon['cover'],
                'totalChapters': pon['totalChapters'],
                'totalWords': pon['totalWords'],
                'parts': pon['parts'],
                'description': "A guide to spiritual enlightenment, disidentifying with the neurotic ego and psychological time, and discovering the profound peace of the present moment."
            }
        ]

        with open(os.path.join(BASE_DIR, 'library.json'), 'w', encoding='utf-8') as f:
            json.dump(library_manifest, f, indent=2)

        with open(os.path.join(BASE_DIR, 'book_data.js'), 'w', encoding='utf-8') as f:
            f.write('// Auto-generated library containing all verified books\n')
            f.write('window.LIBRARY_BOOKS = ')
            json.dump(library_dict, f, ensure_ascii=False)
            f.write(';\n\n')
            f.write('// Default book for single-book backwards compatibility\n')
            f.write('window.BOOK_DATA = window.LIBRARY_BOOKS["thinking-fast-and-slow"];\n')

        print("Library built successfully with 3 complete, verified books!")
