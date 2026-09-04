import subprocess
import xml.etree.ElementTree as ET

subprocess.run(["pytest", "engine/tests/", "--junitxml=results.xml", "-q"])

tree = ET.parse('results.xml')
for list_obj in tree.findall('.//testcase'):
    for fail in list_obj.findall('failure'):
        print(f"FAILED: {list_obj.attrib['classname']}.{list_obj.attrib['name']}")
        print(fail.attrib.get('message', 'No message'))
        print(fail.text[:200])
