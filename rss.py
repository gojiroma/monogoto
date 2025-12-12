import re
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET
from xml.dom import minidom

JST = timezone(timedelta(hours=9))

def parse_entries(markdown_text):
    entries = markdown_text.strip().split('---')
    parsed_entries = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        title_match = re.search(r'^title:\s*(.*)', entry, re.MULTILINE)
        date_match = re.search(r'^date:\s*(\d{8})', entry, re.MULTILINE)
        content_match = re.search(r'content:\s*\|\n([\s\S]*?)(?=\n---|\n$|\Z)', entry, re.MULTILINE)
        if title_match and date_match and content_match:
            title = title_match.group(1).strip()
            yyyymmdd = date_match.group(1)
            content = content_match.group(1).strip()
            content = re.sub(r'^\s*\|\s*', '', content, flags=re.MULTILINE)
            parsed_entries.append({'title': title, 'date': yyyymmdd, 'content': content})
    return parsed_entries

def format_date(yyyymmdd):
    dt = datetime.strptime(yyyymmdd, '%Y%m%d')
    return dt.strftime('%Y-%m-%d')

def generate_rss(entries, output_file):
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:atom': 'http://www.w3.org/2005/Atom',
        'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'xmlns:media': 'http://search.yahoo.com/mrss/'
    })
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = '誤字ロマの物事'
    ET.SubElement(channel, 'link').text = 'https://things.poet.blue'
    ET.SubElement(channel, 'description').text = '誤字ロマの物事です。'
    ET.SubElement(channel, 'language').text = 'ja'
    now_jst = datetime.now(JST)
    ET.SubElement(channel, 'lastBuildDate').text = now_jst.strftime('%a, %d %b %Y %H:%M:%S +0900')
    ET.SubElement(channel, 'itunes:image', href='https://things.poet.blue/cover.png')
    ET.SubElement(channel, 'media:thumbnail', url='https://things.poet.blue/cover.png')
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = 'https://things.poet.blue/cover.png'
    ET.SubElement(image, 'title').text = '誤字ロマの物事'
    ET.SubElement(image, 'link').text = 'https://things.poet.blue'
    ET.SubElement(channel, 'atom:link', {
        'href': 'https://things.poet.blue/rss.xml',
        'rel': 'self',
        'type': 'application/rss+xml'
    })

    for entry in sorted(entries, key=lambda x: x['date'], reverse=True):
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = entry['title']
        ET.SubElement(item, 'link').text = f"https://things.poet.blue#{entry['date']}"
        pub_dt = datetime.strptime(entry['date'], '%Y%m%d').replace(tzinfo=JST)
        ET.SubElement(item, 'pubDate').text = pub_dt.strftime('%a, %d %b %Y 00:00:00 +0900')
        ET.SubElement(item, 'description').text = entry['content'].replace('\n', '<br />')
        ET.SubElement(item, 'guid', isPermaLink='false').text = f"urn:things.poet.blue:{entry['date']}"
        ET.SubElement(item, 'media:content', {
            'url': f"https://nc.poet.blue/{entry['date']}",
            'type': 'image/svg+xml',
            'medium': 'image'
        })

    rough = ET.tostring(rss, encoding='utf-8', method='xml')
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent='  ')
    lines = [line for line in pretty.splitlines() if line.strip()][1:]
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines) + '\n'
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(final_xml)

if __name__ == '__main__':
    with open('entry.md', 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    entries = parse_entries(markdown_text)
    generate_rss(entries, 'rss.xml')
    print('rss.xml を生成しました！')
