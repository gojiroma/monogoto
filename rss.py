from flask import Flask, send_file, request
from werkzeug.urls import unquote
import requests
import re
import random
from io import BytesIO

app = Flask(__name__)

def fetch_entry_md(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_entries(markdown_content):
    entries = []
    for entry_block in re.findall(r'---(.*?)---', markdown_content, re.DOTALL):
        entry = {}
        title_match = re.search(r'^title:\s*(.*)', entry_block, re.MULTILINE)
        date_match = re.search(r'^date:\s*(\d{8})', entry_block, re.MULTILINE)
        content_match = re.search(r'content:\s*\|\s*\n(.*?)(?=\n---|\n$|$)', entry_block, re.DOTALL)
        if title_match and date_match:
            entry['title'] = title_match.group(1).strip()
            entry['date'] = date_match.group(1)
            if content_match:
                content = content_match.group(1).strip()
                content = re.sub(r'^\s*\|?\s*', '', content, flags=re.MULTILINE)
                entry['content'] = content.replace('\n', ' ').strip()
            entries.append(entry)
    return entries

def random_pastel_color():
    r = random.randint(180, 255)
    g = random.randint(180, 255)
    b = random.randint(180, 255)
    return f"rgb({r},{g},{b})"

def generate_svg(title, content, width=358, height=128):
    bg_color = random_pastel_color()
    title_font_size = 12
    content_font_size = 13
    content_height = height - 30
    content_width = width - 30

    svg_content = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="{bg_color}" />
        <style>
            .title {{
                font-family: 'Hiragino Mincho Pro', 'Yu Mincho', serif;
                font-size: {title_font_size}px;
                fill: #333333;
                text-anchor: end;
                font-weight: bold;
                letter-spacing: 2px;
                dominant-baseline: middle;
            }}
            .title-bg {{
                fill: rgba(255, 255, 255, 0.9);
            }}
            foreignObject {{
                overflow: visible;
            }}
            .content {{
                font-family: 'Hiragino Mincho Pro', 'Yu Mincho', serif;
                font-size: {content_font_size}px;
                color: #333333;
                width: {content_width}px;
                word-wrap: break-word;
                white-space: pre-wrap;
                line-height: 1.4;
            }}
        </style>
        <foreignObject x="15" y="10" width="{content_width}" height="{content_height}">
            <div xmlns="http://www.w3.org/1999/xhtml" class="content">{content}</div>
        </foreignObject>
        <rect x="0" y="{height - 25}" width="{width}" height="25" class="title-bg" />
        <text x="{width - 10}" y="{height - 12}" class="title">{title}</text>
    </svg>"""
    return svg_content

@app.route('/<path:title>')
def diary_svg(title):
    decoded_title = unquote(title)
    entry_md_url = "https://things.poet.blue/entry.md"
    markdown_content = fetch_entry_md(entry_md_url)
    entries = parse_entries(markdown_content)
    for entry in entries:
        if entry['title'] == decoded_title:
            svg = generate_svg(entry['title'], entry['content'])
            svg_io = BytesIO(svg.encode('utf-8'))
            return send_file(svg_io, mimetype='image/svg+xml', as_attachment=False)
    return "Entry not found", 404

if __name__ == '__main__':
    app.run(port=5002, debug=True)
