"""Prepare a pinned local tracker extension; never install browser permissions."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from urllib.parse import quote
from pathlib import Path

REPO = "ljkss/autumn-job-assistant-tracker"
COMMIT = "a24b328aef7d62bf81ee4d4581b701a45ebe848e"
EMPTY_RESUME = {"优先信息": {}, "基本信息": {}, "教育经历": [],
                "实习经历": [], "项目经历": [], "获奖经历": [], "校园经历": [], "竞赛与技能": {}}


def request(url):
    with urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "job-apply-skill-installer"}), timeout=45) as response:
        return response.read()


def source_entries():
    return [e for e in json.loads(request(
        f"https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1"))["tree"]
        if e["type"] == "blob"]


def verify_blob(data, entry):
    blob = b"blob " + str(len(data)).encode() + b"\0" + data
    if hashlib.sha1(blob).hexdigest() != entry["sha"]:
        raise ValueError(f"Upstream hash mismatch: {entry['path']}")


def download_source(destination, cache=None):
    entries = source_entries()
    def download(entry):
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe upstream file path")
        existing = cache / relative if cache else None
        data = existing.read_bytes() if existing and existing.is_file() else request(
            f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{quote(entry['path'])}")
        verify_blob(data, entry)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return entry["path"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(download, entries):
            print("Verified: " + name)


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Upstream compatibility marker changed: {old[:55]}")
    return source.replace(old, new, 1)


def patch_profile_editor(destination):
    """Upgrade only extension files; browser profile/records are never written."""
    adapter = Path(__file__).resolve().parents[1] / "assets" / "resume-editor.js"
    (destination / "job-apply-resume-editor.js").write_bytes(adapter.read_bytes())
    path = destination / "dashboard.js"
    source = path.read_text(encoding="utf-8")
    if "JobApplyResumeEditor.render" not in source:
        start = source.index("  function renderResumeEditor() {")
        end = source.index("  // 添加 KV", start)
        source = source[:start] + """
  function renderResumeEditor() {
    window.JobApplyResumeEditor.render(document, currentResume);
  }

""" + source[end:]
        start = source.index("  async function collectAndSaveResume() {")
        end = source.index("  $('#saveAllResumeBtn')", start)
        source = source[:start] + """
  async function collectAndSaveResume() {
    try {
      const updated = window.JobApplyResumeEditor.collect(document, currentResume);
      await storageSet(RESUME_STORAGE_KEY, updated);
      currentResume = updated;
      saveSnapshot(records, currentResume);
      showToast('简历全部模块已保存并同步');
    } catch (error) {
      showToast('保存未完成：' + error.message);
    }
  }

""" + source[end:]
        path.write_text(source, encoding="utf-8")
    html_path = destination / "dashboard.html"
    markup = html_path.read_text(encoding="utf-8")
    if 'src="job-apply-resume-editor.js"' not in markup:
        markup = replace_once(markup, '<script src="dashboard.js"></script>',
                              '<script src="job-apply-resume-editor.js"></script>\n'
                              '  <script src="dashboard.js"></script>')
        html_path.write_text(markup, encoding="utf-8")


def patch_source(destination):
    # Only original integration code is distributed in this repository. Upstream
    # files are fetched directly by the installer and remain in the user's folder.
    for name in ("background.js", "content.js", "dashboard.js"):
        path = destination / name
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r"(const DEFAULT_RESUME(?:_DATA)? = )\{.*?^\s*};",
            lambda m: m[1] + json.dumps(EMPTY_RESUME, ensure_ascii=False) + ";",
            source, count=1, flags=re.S | re.M)
        if count != 1:
            raise ValueError(f"Resume initializer not found: {name}")
        if name == "dashboard.js":
            source = replace_once(source, "records = getExampleRecords();", "records = [];")
            source = replace_once(source, "if (importedRecords.length > 0) {",
                                  "if (Array.isArray(parsed) || Array.isArray(parsed?.records)) {")
        elif name == "background.js":
            source = replace_once(source, "records.unshift(newRecord);", """
        const normalize = value => String(value || '').normalize('NFKC').replace(/\\s+/g, '').toLowerCase();
        const previous = records.find(record =>
          (newRecord.applicationUrl && record.applicationUrl === newRecord.applicationUrl) ||
          (normalize(record.company) === normalize(newRecord.company) &&
           normalize(record.position) === normalize(newRecord.position)));
        if (previous) {
          sendResponse({ ok: false, message: '此岗位已有记录，请在看板核对并更新，未重复收录' });
          return;
        }
        records.unshift(newRecord);""")
            source = replace_once(source, "String(request.record.stage || '已投递')",
                                  "String(request.record.stage || '待投递')")
        else:
            # Keep explicit saved values and useful field aliases. Do not infer
            # demographics, availability, address equivalence or missing dates.
            start = source.index("  function buildResumeFlatMap(resume) {")
            end = source.index("  function extractFieldLabel(el)", start)
            source = source[:start] + """
  function buildResumeFlatMap(resume) {
    const flatMap = {};
    if (!resume || typeof resume !== 'object') return flatMap;
    for (const section of Object.values(resume)) {
      if (!section || typeof section !== 'object') continue;
      const entries = Array.isArray(section) ? section : [section];
      entries.forEach((row, index) => {
        if (!row || typeof row !== 'object') return;
        for (const [key, value] of Object.entries(row)) {
          if (key.startsWith('_') || value == null || String(value).trim() === '') continue;
          if (typeof value !== 'string' && typeof value !== 'number') continue;
          const text = String(value).trim();
          if (index === 0 && !flatMap[key]) flatMap[key] = text;
          if (Array.isArray(section)) flatMap[key + '_' + index] = text;
        }
      });
    }
    const education = Array.isArray(resume['教育经历']) ? resume['教育经历'][0] : null;
    if (education) {
      if (education['开始时间']) flatMap['入学时间'] = education['开始时间'];
      if (education['结束时间']) flatMap['毕业时间'] = education['结束时间'];
    }
    return flatMap;
  }

""" + source[end:]
            source = replace_once(
                source,
                "cleanLabel === k || cleanLabel.includes(k) || (k.length >= 2 && cleanLabel.startsWith(k))",
                "cleanLabel === k")
            source = replace_once(source, "    const cleanLabel = label.trim();",
                                  "    const cleanLabel = label.trim();\n"
                                  "    if (/出生|生日|birthday|birth.?date/i.test(cleanLabel) && "
                                  "!flatMap[cleanLabel]) return null;")
            marker = "      for (const el of allElements) {"
            source = replace_once(source, marker, """
      const labelCounts = new Map();
      for (const field of allElements) {
        const label = extractFieldLabel(field);
        if (label && field.type !== 'radio') labelCounts.set(label, (labelCounts.get(label) || 0) + 1);
      }
      for (const el of allElements) {
        if ((labelCounts.get(extractFieldLabel(el)) || 0) > 1) {
          skippedCount++;
          processedElements.add(el);
          continue;
        }""")
        path.write_text(source, encoding="utf-8")
    patch_profile_editor(destination)
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version_name"] = "2.0.0 - job-apply local compatibility"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "JOB_APPLY_LOCAL_PATCH.json").write_text(json.dumps({
        "upstream": REPO, "commit": COMMIT, "compatVersion": 3,
        "changes": ["empty initial profile and records", "explicit values only",
                    "skip repeated native field labels", "reject duplicate captured jobs",
                    "empty-record backup import support",
                    "render and preserve every imported resume module"],
    }, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    destination = args.dest.expanduser().absolute()
    if destination.exists() and any(destination.iterdir()):
        parser.error("Destination must be empty; choose a new versioned directory")
    destination.mkdir(parents=True, exist_ok=True)
    download_source(destination, args.cache)
    patch_source(destination)
    print(f"Prepared extension: {destination}")
    print("In Chrome/Edge extensions, enable developer mode and Load unpacked this folder yourself.")
    print("No extension has been enabled and no personal data has been migrated.")


if __name__ == "__main__":
    main()
