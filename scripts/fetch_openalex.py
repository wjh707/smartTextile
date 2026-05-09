#!/usr/bin/env python3
"""V3: Fetch smart textiles papers - bulk mode with title.search filter."""
import json
import os
import re
import time
from collections import Counter
from urllib.parse import quote
from urllib.request import urlopen

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard')
os.makedirs(DATA_DIR, exist_ok=True)

# 核心关键词（用于title.search过滤）
CORE_QUERIES = [
    "smart textile",
    "e-textile",
    "electronic textile",
    "conductive textile",
    "textile sensor",
    "textile electrode",
    "textile antenna",
    "textile supercapacitor",
    "textile nanogenerator",
    "textile triboelectric",
    "fabric sensor",
    "conductive fabric",
    "smart fabric",
    "conductive fiber sensor",
    "electronic fabric",
    "woven sensor",
    "knitted sensor",
    "embroidered sensor",
    "textile strain sensor",
    "textile pressure sensor",
    "washable textile sensor",
    "textile energy harvester",
    "textile biosensor",
    "yarn sensor",
    "fiber sensor textile",
]

def fetch_works_bulk(query, max_results=200):
    """Fetch papers using title.search filter for precision."""
    encoded = quote(query)
    url = (f"https://api.openalex.org/works?filter=title.search:{encoded}"
           f"&sort=cited_by_count:desc&per_page={max_results}"
           f"&select=id,doi,title,authorships,publication_year,cited_by_count,"
           f"primary_location,keywords,abstract_inverted_index")
    try:
        all_works = []
        page = 1
        while len(all_works) < max_results:
            page_url = url + f"&page={page}"
            resp = urlopen(page_url, timeout=30)
            data = json.loads(resp.read())
            works = data.get('results', [])
            if not works:
                break
            all_works.extend(works)
            page += 1
            time.sleep(0.1)
        return all_works
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    words_pos = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words_pos.append((pos, word))
    words_pos.sort()
    return ' '.join(w for _, w in words_pos)

def clean_keywords(keywords_list):
    GENERIC = {
        'computer science', 'engineering', 'key (lock)', 'geography',
        'telecommunications', 'mathematics', 'business', 'biology',
        'physics', 'environmental science', 'medicine', 'materials science',
        'chemistry', 'geology', 'psychology', 'sociology', 'economics',
        'art', 'history', 'political science', 'philosophy', 'law', 'education',
        'remote sensing', 'biochemistry', 'nanotechnology', 'composite material',
        'polymer', 'electrode', 'scanning electron microscope', 'nanoparticle',
        'aqueous solution', 'catalysis', 'adsorption', 'composite number',
        'organic chemistry', 'inorganic chemistry', 'spectroscopy',
        'ultrasound', 'chromatography', 'metallurgy',
    }
    cleaned = []
    for kw in keywords_list:
        if isinstance(kw, dict):
            kw = kw.get('display_name', '')
        elif not isinstance(kw, str):
            kw = str(kw)
        kw_lower = kw.lower().strip()
        if kw_lower not in GENERIC and len(kw_lower) > 2:
            cleaned.append(kw)
    return cleaned

def main():
    all_papers = []
    seen_titles = set()
    
    print("🚀 V3: Bulk fetching smart textiles papers (title.search)...\n")
    
    total_fetched = 0
    for query in CORE_QUERIES:
        works = fetch_works_bulk(query, max_results=100)
        for w in works:
            title = (w.get('title') or '').strip()
            key = title[:80].lower().strip()
            if not key or key in seen_titles:
                continue
            # Final relevance check
            t = title.lower()
            if not any(term in t for term in ['textile', 'fabric', 'yarn', 'fiber', 'fibre', 'garment', 'knitt', 'woven', 'embroider']):
                continue
            seen_titles.add(key)
            
            journal = ""
            primary = w.get('primary_location')
            if primary and primary.get('source'):
                journal = primary['source'].get('display_name', '')
            
            authors = []
            for a in w.get('authorships', []):
                if a.get('author', {}).get('display_name'):
                    authors.append(a['author']['display_name'])
            
            abstract = reconstruct_abstract(w.get('abstract_inverted_index'))
            keywords = clean_keywords(w.get('keywords', []))
            
            all_papers.append({
                'title': title,
                'authors': authors,
                'journal': journal,
                'year': w.get('publication_year'),
                'abstract': abstract,
                'doi': w.get('doi', ''),
                'cited_by_count': w.get('cited_by_count', 0),
                'keywords': keywords,
            })
        
        total_fetched += len(works)
        print(f"  '{query}' → fetched {len(works)} → {len(all_papers)} unique so far")
        time.sleep(0.3)
    
    print(f"\n📊 Total fetched: {total_fetched}, unique: {len(all_papers)}")
    
    # Sort by year desc, then cited desc
    all_papers.sort(key=lambda p: (-(p['year'] or 0), -(p['cited_by_count'] or 0)))
    
    # Save raw data
    output = {'records': all_papers, 'updatedAt': time.strftime('%Y-%m-%d')}
    
    raw_path = os.path.join(DATA_DIR, 'papers.json')
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"✅ Raw papers saved: {len(all_papers)} papers")
    
    # Analysis
    journals = Counter(p['journal'] for p in all_papers if p['journal'])
    years = Counter(p['year'] for p in all_papers if p['year'])
    
    STOPWORDS = set('the and for are with from this that these those were been have has had its their what which when where how who each all some any very just also other into about than then them more such here there only still through over between under before after during without within along among because since until while although though can may could would should will shall does not been being do did done has had having get got getting make made making use used using take took taking give gave given find found finding show showed shown showing been being having doing going said used according'.split())
    all_text = ' '.join(
        (p['title'] + ' ' + p.get('abstract', '') + ' ' + ' '.join(p.get('keywords', []))).lower()
        for p in all_papers
    )
    words = [w for w in re.findall(r'\b[a-z]{3,}\b', all_text) if w not in STOPWORDS and len(w) > 2]
    word_freq = Counter(words).most_common(30)
    
    analysis = {
        'total_papers': len(all_papers),
        'total_journals': len(journals),
        'total_authors': len(set(a for p in all_papers for a in p.get('authors', []))),
        'year_range': f"{min(y for y in years if y)}-{max(y for y in years if y)}",
        'top_journals': [{'name': j, 'count': c} for j, c in journals.most_common(20)],
        'year_distribution': [{'year': y, 'count': c} for y, c in sorted(years.items())],
        'top_cited': [{'title': p['title'], 'cited': p['cited_by_count'], 'year': p['year']} for p in sorted(all_papers, key=lambda p: -(p['cited_by_count'] or 0))[:10]],
        'keywords': [{'word': w, 'count': c} for w, c in word_freq[:25]],
    }
    
    # Build keyword phrase extraction for better keywords
    from collections import defaultdict
    
    # Save JS wrappers
    js_content = f"window.PAPERS_DATA = {json.dumps(output, ensure_ascii=False, indent=2)};\n"
    with open(os.path.join(DASHBOARD_DIR, 'data_papers.js'), 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    analysis_js = f"window.ANALYSIS_DATA = {json.dumps(analysis, ensure_ascii=False, indent=2)};\n"
    with open(os.path.join(DASHBOARD_DIR, 'data_analysis.js'), 'w', encoding='utf-8') as f:
        f.write(analysis_js)
    
    print(f"✅ Dashboard data files updated")
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Papers: {len(all_papers)}")
    print(f"  Journals: {len(journals)}")
    print(f"  Top 5 journals:")
    for j, c in journals.most_common(5):
        print(f"    {j}: {c}")
    print(f"  Years: {dict(sorted(years.items()))}")
    print(f"  Top keywords: {word_freq[:10]}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
