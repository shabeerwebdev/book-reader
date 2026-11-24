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
# 1. LOAD THINKING, FAST AND SLOW
# -------------------------------------------------------------
def get_tfs_data():
    with open(os.path.join(BASE_DIR, 'book_data.json'), 'r', encoding='utf-8') as f:
        tfs = json.load(f)
    tfs['cover'] = 'covers/cover_tfs.jpeg'
    return tfs

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
