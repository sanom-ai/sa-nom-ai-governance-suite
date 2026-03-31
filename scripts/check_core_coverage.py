import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python scripts/check_core_coverage.py <coverage_xml_path> <min_percent>')
        return 2

    report_path = Path(sys.argv[1])
    min_percent = float(sys.argv[2])
    if not report_path.exists():
        print(f'Coverage report not found: {report_path}')
        return 2

    root = ET.parse(report_path).getroot()
    total_lines = 0
    covered_lines = 0

    for class_node in root.findall('.//class'):
        filename = (class_node.get('filename') or '').replace('\\', '/')
        if not (filename.startswith('core/') or filename.startswith('sa_nom_governance/core/')):
            continue
        for line_node in class_node.findall('./lines/line'):
            total_lines += 1
            if int(line_node.get('hits', '0')) > 0:
                covered_lines += 1

    if total_lines == 0:
        print('No core module lines found in coverage.xml.')
        return 2

    percent = (covered_lines / total_lines) * 100
    print(f'Core module coverage: {percent:.2f}% (required >= {min_percent:.2f}%)')
    if percent < min_percent:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
