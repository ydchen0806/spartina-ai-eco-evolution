"""Build an editable DOCX working manuscript from the evidence-calibrated Markdown."""
import argparse
import base64
import html
from pathlib import Path
import re

from docx import Document
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--pdf', action='store_true', help='Also render a PDF using optional Playwright/Chromium.')
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Inches(.8)
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(7)
    style.paragraph_format.line_spacing = 1.15
    for block in (ROOT / 'docs/MANUSCRIPT_WORKING_DRAFT.md').read_text().split('\n\n'):
        block = block.strip()
        if not block:
            continue
        if block.startswith('# '):
            doc.add_heading(block[2:], 0)
        elif block.startswith('### '):
            doc.add_heading(block[4:], 2)
        elif block.startswith('## '):
            doc.add_heading(block[3:], 1)
        else:
            doc.add_paragraph(block)
    doc.add_page_break()
    doc.add_heading('Figures for review', 1)
    figure_paths = [
        ('Figure 1', 'figures/recovery_20261007/recovered_rgb_mask_contact_sheet.png'),
        ('Figure 2', 'data/derived/trajectory_audit_20261007/growth_endpoint_sensitivity.png'),
        ('Figure 3', 'data/derived/strict_benchmark_20261007/strict_benchmark.png'),
        ('Extended Data Figure 1', 'data/derived/trajectory_audit_20261007/image_alignment_diagnostic.png')]
    for label, path in figure_paths:
        doc.add_heading(label, 2)
        doc.add_picture(str(ROOT / path), width=Inches(6.5))
    footer = section.footer.paragraphs[0]
    footer.text = 'Working draft · 7 October 2026 · Independent validation incomplete'
    footer.style = doc.styles['Caption']
    doc.core_properties.title = 'Separating biological change from observation in an invasive plant time series'
    doc.core_properties.subject = 'Working manuscript with completed audits and explicit evidence limitations'
    doc.save(args.output)
    reopened = Document(args.output)
    assert len(reopened.inline_shapes) == 4
    assert any('not ready for submission' in p.text for p in reopened.paragraphs)
    words = len(re.findall(r"\b[\w’−]+\b", (ROOT / 'docs/MANUSCRIPT_WORKING_DRAFT.md').read_text()))
    print('Saved', args.output, 'Markdown words including references/captions:', words, 'embedded figures:', len(reopened.inline_shapes))
    if args.pdf:
        from playwright.sync_api import sync_playwright
        body = []
        for block in (ROOT / 'docs/MANUSCRIPT_WORKING_DRAFT.md').read_text().split('\n\n'):
            if not block.strip():
                continue
            level = len(block) - len(block.lstrip('#'))
            tag = f'h{level}' if level in [1, 2, 3] else 'p'
            content = block[level:].strip() if tag != 'p' else block.strip()
            body.append(f'<{tag}>{html.escape(content)}</{tag}>')
        for label, path in figure_paths:
            data = base64.b64encode((ROOT / path).read_bytes()).decode()
            body.append(f'<figure><h2>{label}</h2><img src="data:image/png;base64,{data}"></figure>')
        page_html = ('<!doctype html><meta charset="utf-8"><style>'
            'body{font:11pt Arial,sans-serif;line-height:1.45;color:#172a33}'
            'h1{font-size:21pt}h2{font-size:15pt}h3{font-size:12pt}'
            'h1,h2,h3{break-after:avoid}p{overflow-wrap:anywhere;orphans:3;widows:3}'
            'figure{break-before:page;margin:0;break-inside:avoid}img{max-width:100%;height:auto}'
            '</style>'+''.join(body))
        with sync_playwright() as runner:
            browser = runner.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.set_content(page_html, wait_until='load')
            page.pdf(path=str(args.output.with_suffix('.pdf')), format='A4',
                margin=dict(top='20mm', bottom='22mm', left='20mm', right='20mm'),
                display_header_footer=True, header_template='<span></span>',
                footer_template='<div style="font-size:8px;width:100%;text-align:center">Working draft — independent validation incomplete · <span class="pageNumber"></span></div>')
            browser.close()
        print('Saved', args.output.with_suffix('.pdf'))


if __name__ == '__main__':
    main()
