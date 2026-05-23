"""
Diagnose garbled CJK PDF encoding issues.
"""
import os, sys, re
import fitz  # pymupdf

DATA_DIR = os.path.expanduser('~/Desktop/bjtu')
PDF_PATH = os.path.join(DATA_DIR, '20211111102306.pdf')

def diagnose_pdf(path):
    print(f"{'='*80}")
    print(f"File: {os.path.basename(path)}")
    print(f"Size: {os.path.getsize(path)} bytes")
    print(f"{'='*80}")

    doc = fitz.open(path)
    print(f"Pages: {len(doc)}")
    print(f"Metadata: {doc.metadata}")
    print(f"PDF Version: {doc.metadata.get('format', 'N/A')}")
    print()

    # Check xref length
    print(f"Xref Length: {doc.xref_length()}")

    # Page-by-page text extraction
    print(f"\n{'='*80}")
    print("TEXT EXTRACTION (page by page)")
    print(f"{'='*80}")
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text('text')
        # Show first 200 chars
        preview = text[:200]
        print(f"\n--- Page {i+1} ({len(text)} chars total) ---")
        print(f"Raw repr: {repr(preview)}")

        # Check what it looks like as hex
        raw_bytes = text.encode('utf-8')
        print(f"UTF-8 bytes (first 100): {raw_bytes[:100].hex()}")

        # Try to count how many chars are ASCII vs non-ASCII
        ascii_count = sum(1 for c in text if ord(c) < 128)
        non_ascii = sum(1 for c in text if ord(c) >= 128)
        print(f"ASCII chars: {ascii_count}, Non-ASCII: {non_ascii}")

        if i >= 2:  # Just first 3 pages
            break

    # Font analysis
    print(f"\n{'='*80}")
    print("FONT ANALYSIS")
    print(f"{'='*80}")
    fonts_seen = set()
    for i in range(len(doc)):
        page = doc[i]
        blocks = page.get_text('dict')
        for b in blocks['blocks']:
            if b['type'] == 0:
                for line in b.get('lines', []):
                    for span in line.get('spans', []):
                        font_name = span['font']
                        if font_name not in fonts_seen:
                            fonts_seen.add(font_name)
                            print(f"Page {i+1}: Font='{font_name}', Size={span['size']:.1f}, "
                                  f"Flags={span['flags']}, Color=#{span['color']:06x}")

    # Try different text extraction methods
    print(f"\n{'='*80}")
    print("DIFFERENT EXTRACTION METHODS")
    print(f"{'='*80}")
    page0 = doc[0]

    methods = {
        'text': page0.get_text('text'),
        'blocks': page0.get_text('blocks'),
        'dict': str(page0.get_text('dict'))[:300],
        'rawdict': str(page0.get_text('rawdict'))[:300],
        'html': page0.get_text('html')[:300],
        'xml': page0.get_text('xml')[:300],
        'xhtml': page0.get_text('xhtml')[:300],
    }

    for name, content in methods.items():
        print(f"\n--- {name.upper()} ---")
        print(content[:300])

    # Check for images
    print(f"\n{'='*80}")
    print("IMAGE ANALYSIS")
    print(f"{'='*80}")
    for i in range(len(doc)):
        page = doc[i]
        # Get_images returns list of (xref, smask, width, height, bpc, colorspace, ...)
        img_list = page.get_images()
        if img_list:
            print(f"Page {i+1}: {len(img_list)} image(s)")
            for img in img_list[:3]:
                print(f"  xref={img[0]}, {img[2]}x{img[3]}, bpc={img[4]}")
        if i >= 2:
            break

    doc.close()
    return fonts_seen

def analyze_xref_objects(path):
    """Look at raw PDF objects related to fonts"""
    doc = fitz.open(path)
    print(f"\n{'='*80}")
    print("RAW XREF OBJECT ANALYSIS (Font-related)")
    print(f"{'='*80}")

    for i in range(1, doc.xref_length()):
        try:
            obj_str = doc.xref_object(i)
            if '/Font' in obj_str or '/ToUnicode' in obj_str or '/CMap' in obj_str or '/Type0' in obj_str or '/CIDFont' in obj_str:
                print(f"\n--- Object {i} ---")
                print(obj_str[:500])
        except:
            pass

    doc.close()

def analyze_raw_streams(path):
    """Try to look at raw content streams"""
    doc = fitz.open(path)
    print(f"\n{'='*80}")
    print("RAW CONTENT STREAMS (first page)")
    print(f"{'='*80}")

    page0 = doc[0]
    # Get the raw content stream
    xref = page0.get_contents()[0]
    raw = doc.xref_stream(xref)
    if raw:
        print(f"Stream xref={xref}, length={len(raw)} bytes")
        print(f"First 500 bytes (hex): {raw[:500].hex()}")
        # Try to decompress
        try:
            import zlib
            decompressed = zlib.decompress(raw)
            print(f"Decompressed length: {len(decompressed)}")
            print(f"Decoded (trying utf-8): {decompressed[:500].decode('utf-8', errors='replace')}")
        except:
            print("Could not decompress (maybe not compressed, or different compression)")
            # Try as plain text
            try:
                print(f"As latin-1: {raw[:500].decode('latin-1', errors='replace')}")
            except:
                pass
    doc.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = PDF_PATH

    fonts = diagnose_pdf(pdf_path)

    # If text is garbled, try deeper analysis
    print("\n\n=== DEEPER ANALYSIS ===")
    analyze_xref_objects(pdf_path)
    analyze_raw_streams(pdf_path)
