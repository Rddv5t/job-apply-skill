"""Import/export local autumn tracker backups without loading browser credentials."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from tracker import read_json, write_json, upsert, STATUSES

TO_STATUS = {"待投递": "待投递", "已投递": "已投递", "笔试": "测评中",
             "一面": "面试", "二面": "面试", "HR面": "面试", "Offer": "Offer",
             "已结束": "拒绝/已结束"}
TO_STAGE = {"待投递": "待投递", "已投递": "已投递", "筛选中": "已投递",
            "测评中": "笔试", "面试": "一面", "Offer": "Offer", "拒绝/已结束": "已结束"}


def import_backup(backup):
    records = backup if isinstance(backup, list) else backup.get("records")
    if not isinstance(records, list):
        raise ValueError("Backup must contain a records array")
    result = []
    for item in records:
        if not isinstance(item, dict) or not item.get("company"):
            raise ValueError("Each record must contain company")
        original = item.get("jobApplyStatus")
        status = original if original in STATUSES else TO_STATUS.get(item.get("stage"), "待确认")
        result.append({
            "company": str(item["company"]),
            "position": str(item.get("position", "")),
            "location": str(item.get("city", "")),
            "date": str(item.get("applicationDate", "")),
            "status": status,
            "url": str(item.get("applicationUrl", "")),
            "next": str(item.get("nextAction", "")),
            "source": str(item.get("source") or "autumn tracker 本地备份"),
            "evidence": str(item.get("evidence") or "从使用者提供的扩展备份导入；未重新核验站内投递"),
            "note": str(item.get("note", "")),
        })
    return result


def export_backup(records):
    result = []
    for item in records:
        status = item.get("status", "待确认")
        result.append({
            "id": item.get("id") or f"job-apply-{len(result)}",
            "company": item["company"], "position": item.get("position", ""),
            "city": item.get("location", ""), "applicationDate": item.get("date", ""),
            # The upstream dashboard has fewer states; keep original metadata so
            # round trips never promote an unverified record to an application.
            "stage": TO_STAGE.get(status, "待投递"), "jobApplyStatus": status,
            "applicationUrl": item.get("url", ""), "nextAction": item.get("next", ""),
            "source": item.get("source", ""), "evidence": item.get("evidence", ""),
            "note": item.get("note", ""), "updatedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
        })
    return {"schemaVersion": 2, "savedAt": datetime.now(timezone.utc).isoformat(),
            "recordCount": len(result), "records": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("import")
    p.add_argument("--backup", required=True)
    p.add_argument("--data", required=True)
    p = sub.add_parser("export")
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "import":
        # Validate the entire input before touching the destination.
        rows = import_backup(read_json(args.backup))
        from tracker import validate_record
        for row in rows:
            validate_record(row)
        for row in rows:
            upsert(args.data, row)
        print(f"Merged {len(rows)} records. Resume data was not imported.")
    else:
        output = Path(args.out)
        if output.exists():
            parser.error("Output already exists; choose a new backup path")
        write_json(output, export_backup(read_json(args.data)))
        print("Exported records only. Importing this file in the extension replaces its record list.")


if __name__ == "__main__":
    main()
