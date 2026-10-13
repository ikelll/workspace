#!/usr/bin/env python3
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

p = argparse.ArgumentParser()
p.add_argument('--identifier', required=True)
p.add_argument('--version', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()

root = ET.Element('installer-gui-script', {'minSpecVersion': '2'})
ET.SubElement(root, 'title').text = 'Gorizont-VS-VDI'
ET.SubElement(root, 'options', {'customize': 'never', 'require-scripts': 'false', 'hostArchitectures': 'arm64'})
ET.SubElement(root, 'background', {'file': 'background.png', 'alignment': 'bottomleft', 'scaling': 'tofit'})
ET.SubElement(root, 'welcome', {'file': 'welcome.html', 'mime-type': 'text/html'})
ET.SubElement(root, 'conclusion', {'file': 'conclusion.html', 'mime-type': 'text/html'})
outline = ET.SubElement(root, 'choices-outline')
ET.SubElement(outline, 'line', {'choice': 'default'})
choice = ET.SubElement(root, 'choice', {'id': 'default', 'visible': 'false', 'title': 'Gorizont-VS-VDI'})
ET.SubElement(choice, 'pkg-ref', {'id': a.identifier})
ET.SubElement(root, 'pkg-ref', {'id': a.identifier, 'version': a.version}).text = 'component.pkg'
output = Path(a.output)
output.parent.mkdir(parents=True, exist_ok=True)
ET.indent(root, space='  ')
output.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='utf-8'))
