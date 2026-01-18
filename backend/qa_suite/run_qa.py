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

    run_api_checks(cfg, report)
    run_ui_checks(cfg, report)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("qa_reports") / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "qa_report.md").write_text(report.to_md(), encoding="utf-8")
    (out_dir / "qa_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print(f"WROTE: {(out_dir / 'qa_report.md').resolve()}")

if __name__ == "__main__":
    main()
