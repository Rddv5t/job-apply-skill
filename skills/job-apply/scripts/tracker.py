"""Private job records: screen, upsert and export. Python 3.10+, standard library."""
import argparse
import csv
import html
import json
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

STATUSES = ["待筛选", "待投递", "待登录", "待确认", "已投递", "筛选中",
            "测评中", "面试", "Offer", "拒绝/已结束", "跳过"]
SOUTHEAST_ASIA = [
    "新加坡", "马来西亚", "印度尼西亚", "印尼", "泰国", "越南", "菲律宾",
    "文莱", "柬埔寨", "老挝", "缅甸", "东帝汶", "singapore", "malaysia",
    "indonesia", "thailand", "vietnam", "philippines", "brunei", "cambodia",
    "laos", "myanmar", "timor-leste", "east timor",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def norm(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value))).casefold()


def company_key(value, aliases):
    mappings = {norm(k): norm(v) for k, v in aliases.items()}
    key, seen = norm(value), set()
    while key in mappings and mappings[key] != key:
        if key in seen:
            raise ValueError("Company aliases contain a cycle")
        seen.add(key)
        key = mappings[key]
    return key


def matches(text, values):
    return any(norm(v) in norm(text) for v in values if str(v).strip())


def screen(config, candidates, history):
    aliases = config.get("company_aliases", {})
    key = lambda name: company_key(name, aliases)
    scope = config.get("duplicate_scope", "company")
    if scope not in ("company", "company-role"):
        raise ValueError("duplicate_scope must be company or company-role")
    excluded = {key(x) for x in config.get("excluded_companies", [])}
    # Skipped candidates are not applications. Pending/uncertain submissions still
    # block automatic re-submission until the site history resolves their outcome.
    applied = [r for r in history if r.get("status") in {
        "已投递", "筛选中", "测评中", "面试", "Offer", "拒绝/已结束", "待确认"
    }]
    results = []
    for candidate in candidates:
        r = dict(candidate)
        if not r.get("company"):
            raise ValueError("Candidate must have company")
        ck = key(r["company"])
        previous = [h for h in applied if key(h["company"]) == ck]
        decision, reason = "eligible", "初筛符合；仍需核验具体JD与站内历史"
        if ck in excluded or (previous and scope == "company"):
            decision, reason = "skip_duplicate", "公司已在排除或历史记录中"
        elif previous and any(not h.get("position") for h in previous):
            decision, reason = "review_duplicate", "历史岗位未知，先核验再决定"
        elif previous and any(norm(h.get("position", "")) == norm(r.get("position", "")) for h in previous):
            decision, reason = "skip_duplicate", "同公司同岗位已有记录"
        elif matches(r.get("country", "") + " " + r.get("location", ""),
                     config.get("excluded_countries", [])):
            decision, reason = "skip_location", "位于排除国家"
        elif matches(r.get("region", ""), config.get("excluded_regions", [])):
            decision, reason = "skip_location", "位于排除地区"
        elif matches("东南亚 southeast asia", config.get("excluded_regions", [])) and matches(
                r.get("country", "") + " " + r.get("location", ""), SOUTHEAST_ASIA):
            decision, reason = "skip_location", "位于东南亚"
        elif not r.get("location"):
            decision, reason = "review_location", "缺少具体岗位地点"
        elif r.get("overseas"):
            if not config.get("allow_overseas", False):
                decision, reason = "skip_location", "未开放海外"
            elif not r.get("country") or (config.get("excluded_regions") and not r.get("region")):
                decision, reason = "review_location", "海外岗位需明确国家及地区"
            elif config.get("allowed_locations") and not matches(r["location"], config["allowed_locations"]):
                # Overseas can be independently enabled; domestic city whitelist
                # does not silently disable the explicitly enabled overseas scope.
                reason = "海外范围已开放；仍需核验国家、地区、资格与站内历史"
        elif config.get("allowed_locations") and not matches(r["location"], config["allowed_locations"]):
            decision, reason = "skip_location", "不在允许城市范围"
        if decision == "eligible" and re.search(r"[、,，;/]|全国|多地|海外", r.get("location", "")):
            decision, reason = "review_location", "汇总地点不代表具体职位，需确认实际申请城市"
        if decision == "eligible" and not r.get("position"):
            decision, reason = "review_role", "缺少具体岗位"

        def rank(field, config_key):
            priorities = config.get(config_key, [])
            return next((i for i, p in enumerate(priorities)
                         if norm(p) in norm(r.get(field, ""))), len(priorities))
        r.update(decision=decision, reason=reason, priority=[
            rank("position", "role_priority"),
            rank("industry", "industry_priority"),
            rank("location", "preferred_locations"),
        ])
        results.append(r)
    return sorted(results, key=lambda r: (r["decision"] != "eligible", r["priority"]))


def validate_record(record):
    if not str(record.get("company", "")).strip():
        raise ValueError("company is required")
    if record.get("status") not in STATUSES:
        raise ValueError("Unknown status")
    if not str(record.get("evidence", "")).strip():
        raise ValueError("evidence is required for every update")
    if record.get("date"):
        date.fromisoformat(record["date"])


def upsert(path, record):
    validate_record(record)
    records = read_json(path, [])
    if not isinstance(records, list):
        raise ValueError("Records must be a JSON array")
    k = (norm(record["company"]), norm(record.get("position", "")))
    index = next((i for i, row in enumerate(records)
                  if (norm(row["company"]), norm(row.get("position", ""))) == k), None)
    previous = records[index] if index is not None else {}
    merged = {**previous, **record, "updated_at": datetime.now(timezone.utc).isoformat()}
    if index is None:
        records.append(merged)
    else:
        records[index] = merged
    write_json(path, records)
    return merged


def export_records(records, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fields = ["company", "position", "location", "date", "status",
              "next", "url", "source", "evidence", "note", "updated_at"]
    with (out / "application-records.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for r in records:
            # Spreadsheet applications must not interpret user/site text as formulas.
            writer.writerow([
                "'" + str(r.get(k, "")) if str(r.get(k, "")).lstrip().startswith(("=", "+", "-", "@"))
                else r.get(k, "") for k in fields
            ])
    labels = ["公司", "岗位", "地点", "投递日期", "状态", "下一步", "链接",
              "来源", "证据", "备注", "更新时间"]
    rows = []
    for r in records:
        cells = "".join("<td>" + html.escape(str(r.get(k, ""))) + "</td>" for k in fields)
        rows.append('<tr data-status="' + html.escape(str(r.get("status", "")), quote=True)
                    + '">' + cells + "</tr>")
    options = "".join("<option>" + html.escape(s) + "</option>" for s in STATUSES)
    output = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>求职进度</title><style>
body{font:15px/1.6 system-ui,sans-serif;margin:32px;color:#183047;background:#f7f9fb}
h1{margin-bottom:8px}input,select{font:inherit;padding:8px;margin:8px;border:1px solid #bdcbd8;border-radius:6px}
.wrap{overflow:auto;background:white;border:1px solid #dce4eb;border-radius:8px}
table{border-collapse:collapse;min-width:1200px;width:100%}th,td{padding:12px;text-align:left;border-bottom:1px solid #e2e8ef;vertical-align:top}
th{background:#edf2f7;white-space:nowrap}td{max-width:360px;overflow-wrap:anywhere}p{color:#52677c}
@media print{input,select{display:none}body{margin:0;background:white}.wrap{overflow:visible}table{min-width:0;font-size:9px}}
</style><h1>求职进度</h1><p>本地导出视图 · 实际投递日期未知时留空 · JSON 为主记录</p>
<label>搜索<input id="search" placeholder="公司、岗位、证据或下一步"></label>
<label>状态<select id="status"><option value="">全部</option>__OPTIONS__</select></label>
<span id="count"></span><div class="wrap"><table><thead><tr>__HEAD__</tr></thead>
<tbody>__ROWS__</tbody></table></div><script>
const search=document.querySelector('#search'),status=document.querySelector('#status');
function filter(){let n=0;for(const r of document.querySelectorAll('tbody tr')){
const show=r.textContent.toLowerCase().includes(search.value.toLowerCase())&&(!status.value||r.dataset.status===status.value);
r.hidden=!show;if(show)n++;}document.querySelector('#count').textContent='显示 '+n+' 条';}
search.addEventListener('input',filter);status.addEventListener('change',filter);filter();
</script></html>"""
    output = output.replace("__OPTIONS__", options).replace(
        "__HEAD__", "".join("<th>" + s + "</th>" for s in labels)).replace("__ROWS__", "".join(rows))
    (out / "application-tracker.html").write_text(output, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("screen")
    p.add_argument("--config", required=True)
    p.add_argument("--candidates", required=True)
    p.add_argument("--history")
    p = sub.add_parser("upsert")
    p.add_argument("--data", required=True)
    p.add_argument("--record", required=True)
    p = sub.add_parser("export")
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        if args.command == "screen":
            result = screen(read_json(args.config), read_json(args.candidates),
                            read_json(args.history, []) if args.history else [])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "upsert":
            upsert(args.data, read_json(args.record))
            print("Record saved")
        else:
            records = read_json(args.data)
            if not isinstance(records, list):
                raise ValueError("Records must be a JSON array")
            export_records(records, args.out)
            print("Exported application-tracker.html and application-records.csv")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
