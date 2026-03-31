from pathlib import Path

from scripts import check_enterprise_runtime_coverage


def write_coverage_xml(
    path: Path,
    *,
    enterprise_hits: int,
    enterprise_total: int,
    other_hits: int = 0,
    other_total: int = 0,
) -> None:
    enterprise_lines = "\n".join(
        f'<line number="{index + 1}" hits="{1 if index < enterprise_hits else 0}"/>'
        for index in range(enterprise_total)
    )
    other_lines = "\n".join(
        f'<line number="{index + 1}" hits="{1 if index < other_hits else 0}"/>'
        for index in range(other_total)
    )
    xml = f'''<?xml version="1.0" ?>
<coverage>
  <packages>
    <package name="sa_nom_governance">
      <classes>
        <class filename="sa_nom_governance/api/api_engine.py" name="api_engine">
          <lines>
            {enterprise_lines}
          </lines>
        </class>
        <class filename="sa_nom_governance/utils/config.py" name="config">
          <lines>
            {other_lines}
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
'''
    path.write_text(xml, encoding='utf-8')


def test_enterprise_runtime_coverage_script_passes_at_threshold(tmp_path: Path, monkeypatch) -> None:
    report = tmp_path / 'coverage.xml'
    write_coverage_xml(report, enterprise_hits=9, enterprise_total=10, other_hits=0, other_total=10)
    monkeypatch.setattr(check_enterprise_runtime_coverage.sys, 'argv', ['check', str(report), '90'])

    assert check_enterprise_runtime_coverage.main() == 0


def test_enterprise_runtime_coverage_script_fails_below_threshold(tmp_path: Path, monkeypatch) -> None:
    report = tmp_path / 'coverage.xml'
    write_coverage_xml(report, enterprise_hits=7, enterprise_total=10, other_hits=10, other_total=10)
    monkeypatch.setattr(check_enterprise_runtime_coverage.sys, 'argv', ['check', str(report), '80'])

    assert check_enterprise_runtime_coverage.main() == 1
