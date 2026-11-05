/* Original job-apply editor adapter. Imported modules are rendered and saved intact. */
(() => {
  const defaults = {
    '优先信息': {}, '基本信息': {}, '教育经历': [], '实习经历': [],
    '工作经历': [], '项目经历': [], '获奖经历': [], '校园经历': [], '竞赛与技能': {}
  };
  const templates = {
    '教育经历': {'_rowName': '', '学校': '', '学历': '', '专业': '', '开始时间': '', '结束时间': ''},
    '实习经历': {'_rowName': '', '单位': '', '岗位': '', '开始': '', '结束': '', '岗位职责': ''},
    '工作经历': {'_rowName': '', '单位': '', '岗位': '', '开始': '', '结束': '', '岗位职责': ''},
    '项目经历': {'_rowName': '', '项目名称': '', '角色': '', '开始': '', '结束': '', '主要工作': ''},
    '获奖经历': {'_rowName': '', '奖项名称': '', '获奖时间': '', '描述': ''},
    '校园经历': {'_rowName': '', '职务': '', '职责': ''}
  };
  const initialized = new WeakSet();
  const node = (doc, tag, className, text) => {
    const el = doc.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  };
  function valueInput(doc, value) {
    const isJson = value !== null && typeof value === 'object';
    const text = isJson ? JSON.stringify(value, null, 2) : String(value ?? '');
    const el = doc.createElement(isJson || text.length > 80 || text.includes('\n') ? 'textarea' : 'input');
    if (el.tagName === 'INPUT') el.type = 'text';
    else el.rows = 4;
    el.className = 'kv-val';
    el.value = text;
    el.dataset.kind = value === null ? 'null' : (isJson ? 'json' : (typeof value === 'number' ? 'number' : (typeof value === 'boolean' ? 'boolean' : 'text')));
    return el;
  }
  function kvRow(doc, key, value) {
    const row = node(doc, 'div', 'kv-row');
    const name = node(doc, 'input', 'kv-key');
    name.type = 'text'; name.value = key; name.placeholder = '字段名称';
    const remove = node(doc, 'button', 'kv-del-btn', '删除');
    remove.type = 'button'; remove.dataset.jaAction = 'delete-field';
    row.append(name, valueInput(doc, value), remove);
    return row;
  }
  function experience(doc, item) {
    const row = node(doc, 'div', 'exp-item-card');
    const header = node(doc, 'div', 'exp-item-header');
    const title = node(doc, 'h4', '', item?._rowName || '经历');
    const remove = node(doc, 'button', 'btn-sm btn-danger', '删除此条');
    remove.type = 'button'; remove.dataset.jaAction = 'delete-experience';
    header.append(title, remove);
    const fields = node(doc, 'div', 'ja-experience-fields');
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      for (const [key, value] of Object.entries(item)) fields.append(kvRow(doc, key, value));
    } else {
      row.dataset.scalar = 'true';
      fields.append(valueInput(doc, item));
    }
    const add = node(doc, 'button', 'btn-sm', '+ 添加字段');
    add.type = 'button'; add.dataset.jaAction = 'add-field';
    add.dataset.target = 'experience';
    if (row.dataset.scalar) add.hidden = true;
    row.append(header, fields, add);
    return row;
  }
  function render(doc, profile) {
    const grid = doc.querySelector('.resume-editor-grid');
    if (!grid) throw new Error('Resume editor grid missing');
    grid.replaceChildren();
    const sections = {...defaults, ...profile};
    for (const [section, value] of Object.entries(sections)) {
      const card = node(doc, 'div', 'editor-card full-col');
      card.dataset.profileSection = section;
      const array = Array.isArray(value);
      card.dataset.sectionKind = array ? 'array' : (value && typeof value === 'object' ? 'object' : 'scalar');
      const header = node(doc, 'div', 'editor-card-head');
      header.append(node(doc, 'h3', '', section));
      const add = node(doc, 'button', 'btn-sm', array ? '+ 添加经历' : '+ 添加字段');
      add.type = 'button'; add.dataset.jaAction = array ? 'add-experience' : 'add-field';
      if (card.dataset.sectionKind === 'scalar') add.hidden = true;
      header.append(add);
      const body = node(doc, 'div', array ? 'exp-container ja-section-body' : 'kv-container ja-section-body');
      if (array) value.forEach(item => body.append(experience(doc, item)));
      else if (card.dataset.sectionKind === 'object') {
        Object.entries(value).forEach(([key, item]) => body.append(kvRow(doc, key, item)));
      } else body.append(valueInput(doc, value));
      card.append(header, body); grid.append(card);
    }
    if (!initialized.has(doc)) {
      initialized.add(doc);
      doc.addEventListener('click', event => {
        const button = event.target.closest('[data-ja-action]');
        if (!button || !grid.contains(button)) return;
        event.preventDefault();
        const action = button.dataset.jaAction;
        const card = button.closest('[data-profile-section]');
        if (action === 'delete-field') button.closest('.kv-row').remove();
        else if (action === 'delete-experience') button.closest('.exp-item-card').remove();
        else if (action === 'add-experience') {
          card.querySelector('.ja-section-body').append(experience(doc, templates[card.dataset.profileSection] || {'_rowName': ''}));
        } else if (action === 'add-field') {
          const target = button.dataset.target === 'experience'
            ? button.closest('.exp-item-card').querySelector('.ja-experience-fields')
            : card.querySelector('.ja-section-body');
          const row = kvRow(doc, '', ''); target.append(row); row.querySelector('.kv-key').focus();
        }
      });
    }
  }
  function inputValue(input) {
    if (input.dataset.kind === 'null' && input.value === '') return null;
    if (input.dataset.kind === 'json') return JSON.parse(input.value);
    if (input.dataset.kind === 'number' && input.value.trim() !== '' && Number.isFinite(Number(input.value))) return Number(input.value);
    if (input.dataset.kind === 'boolean' && ['true', 'false'].includes(input.value.trim())) return input.value.trim() === 'true';
    return input.value.trim();
  }
  function readObject(container) {
    const output = {};
    for (const row of container.children) {
      if (!row.matches('.kv-row')) continue;
      const key = row.querySelector('.kv-key').value.trim();
      if (!key) continue;
      if (Object.prototype.hasOwnProperty.call(output, key)) throw new Error('同一模块出现重复字段：' + key);
      Object.defineProperty(output, key, {value: inputValue(row.querySelector('.kv-val')), enumerable: true, configurable: true, writable: true});
    }
    return output;
  }
  function collect(doc, original) {
    const result = structuredClone(original || {});
    for (const card of doc.querySelectorAll('[data-profile-section]')) {
      const section = card.dataset.profileSection;
      const body = card.querySelector('.ja-section-body');
      let value;
      if (card.dataset.sectionKind === 'array') value = Array.from(body.children).map(row =>
        row.dataset.scalar ? inputValue(row.querySelector('.kv-val')) : readObject(row.querySelector('.ja-experience-fields')));
      else if (card.dataset.sectionKind === 'object') value = readObject(body);
      else value = inputValue(body.querySelector('.kv-val'));
      Object.defineProperty(result, section, {value, enumerable: true, configurable: true, writable: true});
    }
    return result;
  }
  window.JobApplyResumeEditor = {render, collect};
})();
