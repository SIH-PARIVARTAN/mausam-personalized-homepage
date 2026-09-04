import sys
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('results.xml')
    for tc in tree.findall('.//testcase'):
        for fail in tc.findall('.//failure'):
            print(f"FAIL: {tc.attrib.get('name')}")
            sys.stdout.buffer.write(fail.text.encode('utf-8')[:500])
            print("\n---")
except Exception as e:
    print(e)
