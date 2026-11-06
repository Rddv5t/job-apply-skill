/* Local record controls for browser automation. Runs in the extension isolated world. */
(() => {
  'use strict';
  if (location.origin !== 'http://127.0.0.1:18765' || location.pathname !== '/records') return;
  if (document.getElementById('job-apply-record-control')) return;
  const KEY = 'autumnRecruitmentTracker.records.v1';
  const BACKUP = 'jobApply.recordSync.backups.v1';
  const stages = new Set(['待投递', '已投递', '筛选中', '笔试', '一面', '二面', 'HR面', 'Offer', '已结束']);
  const advanced = new Set(['筛选中', '笔试', '一面', '二面', 'HR面', 'Offer', '已结束']);
  const normalize = value => String(value || '').normalize('NFKC').replace(/\s+/g, '').toLowerCase();
  const position = value => ['', '待补充', '待确认岗位'].includes(String(value || '').trim()) ? '' : normalize(value);
  const pair = r => normalize(r.company) + '\0' + position(r.position);
  const canonical = value => JSON.stringify(value, function(key, item) {
    return item && typeof item === 'object' && !Array.isArray(item)
      ? Object.fromEntries(Object.keys(item).sort().map(k => [k, item[k]])) : item;
  });
  const fields = ['id', 'company', 'position', 'city', 'applicationDate', 'stage',
    'jobApplyStatus', 'applicationUrl', 'nextAction', 'source', 'evidence', 'note'];
  const root = document.createElement('section');
  root.id = 'job-apply-record-control';
  root.innerHTML = `<h1>秋招助手 · 投递记录控制</h1>
    <p>仅合并投递记录，不读取或修改简历。原有记录不会因导入而删除。</p>
    <label for="job-apply-record-file">选择仅记录 JSON 文件</label>
    <input id="job-apply-record-file" type="file" accept=".json,application/json">
    <p id="job-apply-record-preview" role="status">尚未选择文件</p>
    <button id="job-apply-record-sync" disabled>合并同步投递记录</button>
    <button id="job-apply-record-refresh">刷新看板状态</button>
    <button id="job-apply-record-open">打开扩展看板</button>
    <button id="job-apply-record-rollback" disabled>撤回上次同步（仅记录）</button>
    <p id="job-apply-record-result" role="status"></p>
    <p id="job-apply-record-summary"></p>`;
  document.body.prepend(root);
  const fileInput = root.querySelector('input');
  const sync = root.querySelector('#job-apply-record-sync');
  const preview = root.querySelector('#job-apply-record-preview');
  const result = root.querySelector('#job-apply-record-result');
  let incoming = null;
  let busy = false;
  let rollbackRows = null;
  function validate(data) {
    if (!data || Array.isArray(data) || typeof data !== 'object' ||
        Object.keys(data).some(k => !['schemaVersion', 'savedAt', 'recordCount', 'records'].includes(k))) {
      throw new Error('只接受仅记录备份，拒绝包含简历或其他模块的文件');
    }
    if (!Array.isArray(data.records) || data.records.length > 10000) throw new Error('记录列表无效或超过10000条');
    const seen = new Set();
    return data.records.map(r => {
      if (!r || typeof r !== 'object' || Array.isArray(r)) throw new Error('记录格式错误');
      const clean = {};
      for (const key of fields) {
        const value = r[key] ?? '';
        if (typeof value !== 'string' || value.length > 20000) throw new Error('字段格式错误：' + key);
        clean[key] = value.trim();
      }
      if (!clean.company || !stages.has(clean.stage)) throw new Error('公司或阶段无效');
      if (clean.applicationDate && !/^\d{4}-\d{2}-\d{2}$/.test(clean.applicationDate)) throw new Error('日期格式无效');
      if (clean.applicationUrl && !/^https?:\/\//i.test(clean.applicationUrl)) throw new Error('岗位链接仅支持http/https');
      if (!clean.evidence) throw new Error('每条记录需要来源证据');
      const identity = pair(clean);
      if (seen.has(identity)) throw new Error('文件含重复公司与岗位');
      seen.add(identity);
      return clean;
    });
  }
  async function refresh() {
    const data = await chrome.storage.local.get([KEY, BACKUP]);
    const rows = Array.isArray(data[KEY]) ? data[KEY] : [];
    const pending = rows.filter(r => r.stage === '待投递').length;
    root.querySelector('#job-apply-record-summary').textContent =
      `扩展已保存：${rows.length}条记录；已投及后续阶段${rows.length - pending}条，待投递${pending}条。`;
    root.dataset.recordCount = String(rows.length);
    rollbackRows = Array.isArray(data[BACKUP]) ? [...data[BACKUP]].reverse()
      .find(backup => Array.isArray(backup.records) && canonical(backup.records) !== canonical(rows))?.records : null;
    root.querySelector('#job-apply-record-rollback').disabled = !Array.isArray(rollbackRows);
    root.querySelector('#job-apply-record-rollback').textContent = Array.isArray(rollbackRows)
      ? `撤回上次同步（恢复${rollbackRows.length}条，仅记录）` : '撤回上次同步（无不同版本）';
    return rows;
  }
  fileInput.addEventListener('change', async () => {
    incoming = null;
    sync.disabled = true;
    try {
      const file = fileInput.files[0];
      if (!file || file.size > 10 * 1024 * 1024) throw new Error('请选择不超过10MB的JSON');
      incoming = validate(JSON.parse((await file.text()).replace(/^\uFEFF/, '')));
      preview.textContent = `已校验${incoming.length}条记录，点击合并后写入；不会覆盖简历。`;
      sync.disabled = false;
    } catch (error) { preview.textContent = '未导入：' + error.message; }
  });
  sync.addEventListener('click', async event => {
    if (!event.isTrusted || busy || !incoming) return;
    busy = true;
    sync.disabled = true;
    try {
      const current = await refresh();
      const merged = current.map(r => ({...r}));
      let added = 0, updated = 0, conflicts = 0;
      for (const row of incoming) {
        const index = merged.findIndex(r => (row.id && r.id === row.id && normalize(r.company) === normalize(row.company)) || pair(r) === pair(row) ||
          (row.applicationUrl && r.applicationUrl === row.applicationUrl));
        if (index < 0) {
          merged.push({...row, id: row.id || crypto.randomUUID(), updatedAt: Date.now()});
          added++;
        } else {
          const old = merged[index];
          // Importing an old "applied" record must not erase newer interview/offer facts.
          if (advanced.has(old.stage) && old.stage !== row.stage) { conflicts++; continue; }
          const same = fields.filter(k => k !== 'id').every(k => (old[k] || '') === row[k]);
          if (!same) {
            merged[index] = {...old, ...row, id: old.id || crypto.randomUUID(), updatedAt: Date.now()};
            updated++;
          }
        }
      }
      if (added || updated) {
        const saved = await chrome.storage.local.get([BACKUP]);
        const backups = Array.isArray(saved[BACKUP]) ? saved[BACKUP] : [];
        // Save rollback data BEFORE writing. Never request the resume storage key.
        backups.push({savedAt: new Date().toISOString(), records: current});
        await chrome.storage.local.set({[BACKUP]: backups});
        const latest = (await chrome.storage.local.get([KEY]))[KEY] || [];
        if (canonical(latest) !== canonical(current)) throw new Error('看板记录刚发生变化，请重新同步');
        await chrome.storage.local.set({[KEY]: merged});
      }
      const verified = await refresh();
      if (canonical(verified) !== canonical(merged)) throw new Error('保存核验未通过，请重新检查');
      result.textContent = `同步成功：新增${added}，更新${updated}，保留原有后续阶段${conflicts}；共${verified.length}条。简历未修改。`;
      root.dataset.syncStatus = conflicts ? 'conflicts' : 'success';
    } catch (error) {
      result.textContent = '同步未完成：' + error.message;
      root.dataset.syncStatus = 'error';
    } finally { busy = false; sync.disabled = !incoming; }
  });
  root.querySelector('#job-apply-record-refresh').addEventListener('click', () => refresh().catch(e => {result.textContent = e.message;}));
  root.querySelector('#job-apply-record-rollback').addEventListener('click', async event => {
    if (!event.isTrusted || busy) return;
    busy = true;
    try {
      await refresh();
      if (!Array.isArray(rollbackRows)) throw new Error('没有可恢复的同步前备份');
      const data = await chrome.storage.local.get([KEY, BACKUP]);
      const target = rollbackRows;
      const backups = data[BACKUP];
      // Keep the current version too, so rollback is itself recoverable.
      await chrome.storage.local.set({[BACKUP]: [...backups, {savedAt:new Date().toISOString(), records:data[KEY]}]});
      await chrome.storage.local.set({[KEY]: target});
      const verified = await refresh();
      if (canonical(verified) !== canonical(target)) throw new Error('恢复核验未通过');
      result.textContent = `已撤回上次同步，恢复${verified.length}条记录；简历未修改。`;
      root.dataset.syncStatus = 'rolled-back';
    } catch (error) { result.textContent = '恢复未完成：' + error.message; }
    finally { busy = false; }
  });
  root.querySelector('#job-apply-record-open').addEventListener('click', event => {
    if (event.isTrusted) chrome.runtime.sendMessage({type: 'OPEN_DASHBOARD', targetHash: '#records'});
  });
  refresh().catch(e => { result.textContent = '连接失败：' + e.message; });
})();
