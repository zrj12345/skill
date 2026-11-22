# -*- coding: utf-8 -*-
"""Strip document properties from docx files (软著交付前清理).

Removes from docProps/core.xml:
    作者      dc:creator, cp:lastModifiedBy
    备注      dc:description
    内容类型  cp:contentType
and the other free-text descriptive fields (title / subject / keywords /
category / contentStatus).

Leaves cp:revision, dcterms:created/modified and app.xml untouched, then
reports what remains so the caller can decide about further cleanup.

Usage:
    python strip_metadata.py <dir-or-file> [<dir-or-file> ...]
Each directory argument is scanned (non-recursively) for *.docx.
Files locked by another process (e.g. WPS) are reported and skipped.
"""
import os
import re
import shutil
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = {
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'dcmitype': 'http://purl.org/dc/dcmitype/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}
for _p, _u in NS.items():
    ET.register_namespace(_p, _u)

CORE = 'docProps/core.xml'
CP = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
DC = 'http://purl.org/dc/elements/1.1/'
REMOVE = [
    f'{{{DC}}}creator',
    f'{{{DC}}}description',
    f'{{{DC}}}title',
    f'{{{DC}}}subject',
    f'{{{CP}}}lastModifiedBy',
    f'{{{CP}}}contentType',
    f'{{{CP}}}contentStatus',
    f'{{{CP}}}keywords',
    f'{{{CP}}}category',
]


def dump_props(path, indent='      '):
    with zipfile.ZipFile(path) as z:
        for part in ('docProps/core.xml', 'docProps/app.xml'):
            if part not in z.namelist():
                continue
            x = z.read(part).decode('utf-8', 'replace')
            x = re.sub(r'>\s*<', '><', x)
            for m in re.finditer(r'<((?:dc|cp|dcterms)?:?[A-Za-z]+)[^>]*>([^<]{0,48})</\1>', x):
                tag, val = m.group(1), m.group(2).strip()
                if val:
                    print(f'{indent}{tag:22s} = {val}')


def strip(path):
    """Return (removed_tag_names, error_message_or_None)."""
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    if CORE not in [i.filename for i, _ in items]:
        return [], 'no docProps/core.xml'
    removed = []
    out = []
    for info, data in items:
        if info.filename == CORE:
            root = ET.fromstring(data)
            for el in list(root):
                if el.tag in REMOVE:
                    removed.append(el.tag.split('}')[1])
                    root.remove(el)
            data = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
        out.append((info, data))
    tmp = path + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for info, data in out:
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zo.writestr(zi, data)
    shutil.move(tmp, path)
    return removed, None


def targets(args):
    for a in args:
        if os.path.isdir(a):
            for f in sorted(os.listdir(a)):
                if f.lower().endswith('.docx'):
                    yield os.path.join(a, f)
        elif a.lower().endswith('.docx'):
            yield a


def main(argv):
    files = list(targets(argv))
    if not files:
        print('no .docx found'); return 1
    locked = []
    for p in files:
        try:
            open(p, 'r+b').close()
        except PermissionError:
            locked.append(p)
            print(f'SKIP (locked by another process): {p}')
            continue
        try:
            removed, err = strip(p)
        except Exception as e:
            print(f'ERROR {p}: {type(e).__name__}: {e}')
            continue
        print(f'{p}\n    removed: {", ".join(removed) if removed else "(none present)"}'
              + (f'  [{err}]' if err else ''))
    print('\n--- remaining properties ---')
    for p in files:
        if p in locked:
            continue
        print(f'{p}')
        try:
            dump_props(p)
        except Exception as e:
            print('      ERR', e)
    if locked:
        print('\nLOCKED (close the owning app, then re-run):')
        for p in locked:
            print('  ', p)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
