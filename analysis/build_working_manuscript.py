"""Build a review DOCX/PDF with each figure beside its legend and vector PDF artwork."""
import argparse,base64,html,re
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt
ROOT=Path(__file__).resolve().parents[1]
FIGURES=[
 ('Figure 1','figures/recovery_20261007/recovered_rgb_mask_contact_sheet.png'),
 ('Figure 2','figures/publication_20261007/figure2_endpoint.png'),
 ('Figure 3','figures/publication_20261007/figure3_prediction.png'),
 ('Figure 4','figures/publication_20261007/figure4_landscape.png'),
 ('Extended Data Figure 1','data/derived/trajectory_audit_20261007/image_alignment_diagnostic.png'),
 ('Extended Data Figure 2','data/derived/ccav_20261007/ccav_sample_audit.png'),
 ('Extended Data Figure 3','data/derived/ccav_20261007/ccav_annual_site_maps.png'),
 ('Extended Data Figure 4','data/derived/ccav_20261007/isolated_mask_ccav_agreement.png'),
 ('Extended Data Figure 5','data/derived/clonal_common_garden_20261007/clonal_reaction_norms.png'),
 ('Extended Data Figure 6','data/derived/clonal_common_garden_20261007/clonal_block_sensitivity.png'),
 ('Extended Data Figure 7','data/derived/clonal_common_garden_20261007/clonal_leave_origin_out.png'),
 ('Extended Data Figure 8','data/derived/genet_ramet_20261007/genet_ramet_units.png'),
 ('Extended Data Figure 9','data/derived/local_sentinel_c1_20261007/local_sentinel_extension.png'),
 ('Extended Data Figure 10','data/derived/zhangjiang_uav_20261007/zhangjiang_uav_extension.png')]

def paragraph(doc,text):
    p=doc.add_paragraph()
    for part in re.split(r'(\[\d+(?:[,–\- ]+\d+)*\])',text):
        run=p.add_run(part[1:-1] if re.fullmatch(r'\[\d+(?:[,–\- ]+\d+)*\]',part) else part)
        if part.startswith('[') and part.endswith(']'):run.font.superscript=True
    return p

def htmltext(text):
    return re.sub(r'\[(\d+(?:[,–\- ]+\d+)*)\]',r'<sup>\1</sup>',html.escape(text))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--pdf',action='store_true');args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    raw=(ROOT/'docs/MANUSCRIPT_WORKING_DRAFT.md').read_text();main_text,legend_text=raw.split('## Figure legends',1)
    legends={}
    for block in legend_text.split('\n\n'):
        block=block.strip()
        if ' | ' in block:
            label,caption=block.split(' | ',1);legends[label]=re.sub(r' Source: [^ ]+\.(?= |$)','',caption)
    assert set(legends)==set(label for label,_ in FIGURES)
    doc=Document();section=doc.sections[0];section.page_width=Inches(8.27);section.page_height=Inches(11.69);section.left_margin=section.right_margin=Inches(.65);section.top_margin=section.bottom_margin=Inches(.75)
    style=doc.styles['Normal'];style.font.name='Arial';style.font.size=Pt(11);style.paragraph_format.space_after=Pt(7);style.paragraph_format.line_spacing=1.15
    body=[]
    for block in main_text.split('\n\n'):
        block=block.strip()
        if not block:continue
        level=len(block)-len(block.lstrip('#'))
        if level in [1,2,3]:
            content=block[level:].strip();doc.add_heading(content,level-1);body.append(f'<h{level}>{html.escape(content)}</h{level}>')
        else:
            paragraph(doc,block);body.append('<p>'+htmltext(block).replace('\n','<br>')+'</p>')
    for label,path in FIGURES:
        doc.add_page_break();doc.add_heading(label,2)
        from PIL import Image
        w,h=Image.open(ROOT/path).size;inches=min(6.85,6.7*w/h)
        p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(ROOT/path),width=Inches(inches))
        cap=paragraph(doc,legends[label]);cap.paragraph_format.keep_together=True
        for run in cap.runs:run.font.size=Pt(9)
        # Prefer editable vector text/lines in review PDF where available.
        source=(ROOT/path).with_suffix('.svg');mime='image/svg+xml'
        if not source.exists():source=ROOT/path;mime='image/png'
        data=base64.b64encode(source.read_bytes()).decode();body.append(f'<figure><h2>{label}</h2><img src="data:{mime};base64,{data}"><figcaption>{htmltext(legends[label])}</figcaption></figure>')
    section.footer.paragraphs[0].text='Working draft · 7 October 2026 · Independent validation incomplete'
    doc.core_properties.title=raw.splitlines()[0][2:];doc.core_properties.subject='Evidence-calibrated research manuscript; not ready for submission';doc.save(args.output)
    reopened=Document(args.output);assert len(reopened.inline_shapes)==len(FIGURES)
    assert any('not ready for submission' in p.text for p in reopened.paragraphs)
    print('DOCX:',args.output,'figures:',len(FIGURES),'words incl. references/captions:',len(raw.split()))
    if args.pdf:
        from playwright.sync_api import sync_playwright
        page_html='<!doctype html><meta charset="utf-8"><style>body{font:11pt Arial,sans-serif;line-height:1.45;color:#20252a}h1{font-size:21pt}h2{font-size:15pt}h3{font-size:12pt}h1,h2,h3{break-after:avoid}p{overflow-wrap:anywhere;orphans:3;widows:3}figure{break-before:page;margin:0;break-inside:avoid}figure h2{margin:0 0 5mm}img{display:block;max-width:100%;max-height:165mm;width:auto;height:auto;margin:0 auto 5mm}figcaption{font-size:9pt;line-height:1.35}sup{font-size:70%;line-height:0}</style>'+''.join(body)
        with sync_playwright() as runner:
            browser=runner.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page();page.set_content(page_html,wait_until='load');page.pdf(path=str(args.output.with_suffix('.pdf')),format='A4',margin=dict(top='18mm',bottom='20mm',left='16.5mm',right='16.5mm'),display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:8px;width:100%;text-align:center">Working draft · Independent validation incomplete · <span class="pageNumber"></span></div>');browser.close()
        print('PDF:',args.output.with_suffix('.pdf'))
if __name__=='__main__':main()
