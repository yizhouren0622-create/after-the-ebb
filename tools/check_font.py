"""Check shipped text against the actual bundled TTF, with no dependencies."""
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
data = (ROOT / 'game/fonts/SourceHanSansLite.ttf').read_bytes()
def u16(offset): return struct.unpack_from('>H', data, offset)[0]
def u32(offset): return struct.unpack_from('>I', data, offset)[0]
tables = {data[12+i*16:16+i*16]: u32(20+i*16) for i in range(u16(4))}
cmap = tables[b'cmap']
subtables = [cmap+u32(cmap+8+i*8) for i in range(u16(cmap+2))
             if u16(cmap+4+i*8) in (0, 3)]
def present(code):
    for offset in subtables:
        form = u16(offset)
        if form == 12:
            for i in range(u32(offset+12)):
                start, end, glyph = struct.unpack_from('>III', data, offset+16+i*12)
                if start <= code <= end and glyph+code-start: return True
        elif form == 4 and code <= 65535:
            count = u16(offset+6)//2
            for i in range(count):
                end = u16(offset+14+i*2)
                start = u16(offset+16+count*2+i*2)
                if not start <= code <= end: continue
                delta = u16(offset+16+count*4+i*2)
                position = offset+16+count*6+i*2
                distance = u16(position)
                glyph = u16(position+distance+(code-start)*2) if distance else code
                if glyph and (glyph+delta) % 65536: return True
    return False

chars = {c for p in list((ROOT/'game').glob('*.rpy')) + list((ROOT/'game/python-packages').glob('*.py'))
         for c in p.read_text('utf-8') if '\u4e00' <= c <= '\u9fff'}
missing = sorted(c for c in chars if not present(ord(c)))
result = {'unique_characters': len(chars), 'missing_characters': missing}
(ROOT/'tests/font-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', 'utf-8')
print(json.dumps(result, ensure_ascii=False))
assert not missing, 'Shipped font lacks Chinese characters'
