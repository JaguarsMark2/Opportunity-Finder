from datetime import datetime


class Report:
    def __init__(self):
        self.rows = []
        self.notes = []

    def pass_(self, name: str):
        self.rows.append(("PASS", name, ""))

    def fail(self, name: str, detail: str):
        self.rows.append(("FAIL", name, detail))

    def note(self, msg: str):
        self.notes.append(msg)

    def to_md(self) -> str:
        out = []
        out.append(f"# QA Report\n\nGenerated: {datetime.utcnow().isoformat()}Z\n")
        out.append("## Checks\n")
        out.append("| Status | Check | Details |\n|---|---|---|\n")
        for status, name, detail in self.rows:
            detail = (detail or "").replace("\n", " ").replace("|", "\\|")
            out.append(f"| {status} | {name} | {detail} |\n")
        if self.notes:
            out.append("\n## Notes\n")
            for n in self.notes:
                out.append(f"- {n}\n")
        return "".join(out)
