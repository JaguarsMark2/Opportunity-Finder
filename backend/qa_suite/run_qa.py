import json
from pathlib import Path
from datetime import datetime
from report import Report
from api_smoke import run_api_checks
from ui_smoke import run_ui_checks

def main():
    cfg_path = Path(__file__).parent / "qa_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    report = Report()

    print("Running QA suite...")
    print("=" * 60)

    run_api_checks(cfg, report)
    run_ui_checks(cfg, report)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("qa_reports") / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    report_md = report.to_md()
    (out_dir / "qa_report.md").write_text(report_md, encoding="utf-8")
    (out_dir / "qa_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"\nWROTE: {(out_dir / 'qa_report.md').resolve()}")
    print("\n" + "=" * 60)
    print("QA REPORT")
    print("=" * 60)
    print(report_md)
    print("=" * 60)

    # Print summary
    pass_count = sum(1 for r in report.rows if r[0] == "PASS")
    fail_count = sum(1 for r in report.rows if r[0] == "FAIL")
    print(f"\nSUMMARY: {pass_count} passed, {fail_count} failed, {len(report.rows)} total checks")

if __name__ == "__main__":
    main()
