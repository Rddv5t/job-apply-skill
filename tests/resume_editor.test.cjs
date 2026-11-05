/* Optional browser regression: set JOB_APPLY_EXTENSION_DIR to a prepared extension. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.JOB_APPLY_PLAYWRIGHT || 'playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.JOB_APPLY_CHROME ? { executablePath: process.env.JOB_APPLY_CHROME } : {})
  });
  try {
    const original = {
      '基本信息': { '姓名': '示例用户' },
      '教育经历': [{ '_rowName': '本科', '学校': '示例学校' }],
      '获奖经历': [
        { '_rowName': '示例奖项甲', '奖项名称': '示例奖项甲', '描述': '团队贡献' },
        { '_rowName': '示例奖项乙', '奖项名称': '示例奖项乙', '描述': '个人贡献' }
      ],
      '校园经历': [{ '职务': '示例校园职务', '职责': '组织活动' }],
      '自定义模块': { '复杂字段': { nested: [1, 2] }, '空值': null },
      '未知标量模块': 'preserve',
    };
    const page = await browser.newPage();
    await page.setContent('<div class="resume-editor-grid"></div>');
    await page.addScriptTag({
      path: path.join(__dirname, '../skills/job-apply/assets/resume-editor.js')
    });
    await page.evaluate(profile => window.JobApplyResumeEditor.render(document, profile), original);
    assert.equal(await page.locator('[data-profile-section="获奖经历"] .exp-item-card').count(), 2);
    assert.equal(await page.locator('[data-profile-section="校园经历"] .exp-item-card').count(), 1);
    const collected = await page.evaluate(profile => window.JobApplyResumeEditor.collect(document, profile), original);
    for (const key of Object.keys(original)) assert.deepEqual(collected[key], original[key]);
    await page.locator('[data-profile-section="获奖经历"] > .editor-card-head button').click();
    const withNewAward = await page.evaluate(profile => window.JobApplyResumeEditor.collect(document, profile), original);
    assert.equal(withNewAward['获奖经历'].length, 3);
    assert.equal(withNewAward['获奖经历'][2]['获奖时间'], '');
    await page.close();

    if (process.env.JOB_APPLY_EXTENSION_DIR) {
      const integrated = await browser.newPage();
      await integrated.addInitScript(profile => {
        const store = {
          'autumnRecruitmentTracker.resume.v1': profile,
          'autumnRecruitmentTracker.records.v1': []
        };
        window.__profileStore = store;
        window.chrome = {storage: {local: {
          get: async keys => Object.fromEntries(keys.map(key => [key, store[key]])),
          set: async values => Object.assign(store, values)
        }}};
      }, original);
      const dashboard = pathToFileURL(path.join(process.env.JOB_APPLY_EXTENSION_DIR, 'dashboard.html'));
      dashboard.hash = 'resume';
      await integrated.goto(dashboard.href);
      await integrated.locator('[data-profile-section="获奖经历"]').waitFor();
      await integrated.locator('#saveAllResumeBtn').click();
      const saved = await integrated.evaluate(() => window.__profileStore['autumnRecruitmentTracker.resume.v1']);
      for (const key of Object.keys(original)) assert.deepEqual(saved[key], original[key]);
      await integrated.reload();
      await integrated.locator('[data-profile-section="获奖经历"]').waitFor();
      assert.equal(await integrated.locator('[data-profile-section="获奖经历"] .exp-item-card').count(), 2);
      await integrated.close();
    }
    console.log('PASS: awards, campus and custom modules render and survive save; new fields start blank.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
