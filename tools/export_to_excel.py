# export_to_excel.py
import csv
import zipfile
import xml.etree.ElementTree as ET
import os

def create_excel_from_csv(csv_path, excel_path):
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        r = csv.reader(f)
        for row in r:
            rows.append(row)

    # Calculate summary / pivot
    cls_counts = {}
    dept_counts = {}
    univ_counts = {}
    for row in rows[1:]:
        cls = row[3]
        dept = row[5]
        univ = row[6]
        cls_counts[cls] = cls_counts.get(cls, 0) + 1
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        univ_counts[univ] = univ_counts.get(univ, 0) + 1

    total_docs = len(rows) - 1

    # XML Templates for openxml .xlsx
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Metadata_Raw" sheetId="1" r:id="rId1"/>
    <sheet name="Pivot_Statistics" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>'''

    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
  </cellXfs>
</styleSheet>'''

    def escape_xml(s):
        return (str(s).replace("&", "&amp;")
                      .replace("<", "&lt;")
                      .replace(">", "&gt;")
                      .replace('"', "&quot;")
                      .replace("'", "&apos;"))

    # Generate Sheet 1 (Metadata_Raw)
    sheet1_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '  <sheetData>'
    ]
    for r_idx, row in enumerate(rows, start=1):
        sheet1_lines.append(f'    <row r="{r_idx}">')
        for c_idx, val in enumerate(row, start=1):
            col_letter = chr(64 + c_idx) if c_idx <= 26 else 'A' + chr(64 + c_idx - 26)
            cell_ref = f"{col_letter}{r_idx}"
            s_attr = ' s="1"' if r_idx == 1 else ''
            # Check if number
            val_clean = val.strip()
            if r_idx > 1 and val_clean.isdigit():
                sheet1_lines.append(f'      <c r="{cell_ref}"{s_attr}><v>{val_clean}</v></c>')
            else:
                esc = escape_xml(val)
                sheet1_lines.append(f'      <c r="{cell_ref}" t="inlineStr"{s_attr}><is><t>{esc}</t></is></c>')
        sheet1_lines.append('    </row>')
    sheet1_lines.append('  </sheetData>')
    sheet1_lines.append('</worksheet>')

    # Generate Sheet 2 (Pivot_Statistics)
    sheet2_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '  <sheetData>'
    ]
    
    pivot_rows = [
        ("BẢNG TỔNG HỢP PIVOT: SỐ LƯỢNG VÀ TỶ LỆ THEO CLASSIFICATION", "", ""),
        ("Classification", "Số lượng tài liệu", "Tỷ lệ (%)"),
        ("Public", str(cls_counts.get("Public", 0)), f"{cls_counts.get('Public', 0) / total_docs * 100:.2f}%"),
        ("Internal", str(cls_counts.get("Internal", 0)), f"{cls_counts.get('Internal', 0) / total_docs * 100:.2f}%"),
        ("Restricted", str(cls_counts.get("Restricted", 0)), f"{cls_counts.get('Restricted', 0) / total_docs * 100:.2f}%"),
        ("Tổng cộng", str(total_docs), "100.00%"),
        ("", "", ""),
        ("THỐNG KÊ THEO TRƯỜNG THAM KHẢO", "", ""),
        ("University", "Số lượng", "Tỷ lệ (%)")
    ]
    for u, cnt in sorted(univ_counts.items(), key=lambda x: -x[1]):
        pivot_rows.append((u, str(cnt), f"{cnt / total_docs * 100:.2f}%"))

    for r_idx, r_data in enumerate(pivot_rows, start=1):
        sheet2_lines.append(f'    <row r="{r_idx}">')
        for c_idx, val in enumerate(r_data, start=1):
            col_letter = chr(64 + c_idx)
            cell_ref = f"{col_letter}{r_idx}"
            s_attr = ' s="1"' if r_idx in [1, 2, 6, 8, 9] else ''
            esc = escape_xml(val)
            sheet2_lines.append(f'      <c r="{cell_ref}" t="inlineStr"{s_attr}><is><t>{esc}</t></is></c>')
        sheet2_lines.append('    </row>')

    sheet2_lines.append('  </sheetData>')
    sheet2_lines.append('</worksheet>')

    # Package into xlsx zip
    with zipfile.ZipFile(excel_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('xl/_rels/workbook.xml.rels', wb_rels)
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/styles.xml', styles)
        z.writestr('xl/worksheets/sheet1.xml', '\n'.join(sheet1_lines))
        z.writestr('xl/worksheets/sheet2.xml', '\n'.join(sheet2_lines))

    print(f"Excel created successfully: {excel_path}")

if __name__ == "__main__":
    create_excel_from_csv("data/metadata/documents_metadata.csv", "data/metadata/documents_metadata.xlsx")

