const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium} = require(process.env.JOB_APPLY_PLAYWRIGHT || 'playwright');
(async () => {
  const browser = await chromium.launch({headless:true,
    ...(process.env.JOB_APPLY_CHROME ? {executablePath:process.env.JOB_APPLY_CHROME} : {})});
  try {
    const page = await browser.newPage();
    await page.route('http://127.0.0.1:18765/records', r => r.fulfill({body:'<html><body></body></html>',contentType:'text/html'}));
    await page.addInitScript(() => {
      window.store = {
        'autumnRecruitmentTracker.resume.v1': {awards:['keep'],custom:{nested:'unchanged'}},
        'autumnRecruitmentTracker.records.v1': [
          {id:'keep',company:'Existing',position:'PM',stage:'一面',note:'new interview'},
          {id:'update',company:'Applied',position:'PM',stage:'待投递'},
          {id:'unrelated',company:'Not in file',position:'PM',stage:'已投递'},
          {id:'history-0',company:'History',position:'',stage:'已投递'}
        ]
      };
      window.writes = [];
      window.chrome = {storage:{local:{
        get:async keys => structuredClone(Object.fromEntries(keys.map(k=>[k,window.store[k]]))),
        set:async values => {
          const sorted = JSON.parse(JSON.stringify(values, (k,v)=>v && typeof v==='object' && !Array.isArray(v) ? Object.fromEntries(Object.keys(v).sort().map(key=>[key,v[key]])) : v));
          window.writes.push(Object.keys(values));Object.assign(window.store,sorted);
        }
      }},runtime:{sendMessage:()=>{}}};
    });
    await page.goto('http://127.0.0.1:18765/records');
    await page.addScriptTag({path:path.join(__dirname,'../skills/job-apply/assets/record-control.js')});
    const upload = data => page.locator('#job-apply-record-file').setInputFiles({
      name:'records.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))
    });
    await upload({records:[],resume:{name:'must reject'}});
    await page.waitForFunction(()=>document.querySelector('#job-apply-record-preview').textContent.includes('未导入'));
    assert.equal(await page.locator('#job-apply-record-sync').isDisabled(),true);
    const row = (company,stage) => ({company,position:'PM',stage,evidence:'verified record',applicationDate:''});
    await upload({schemaVersion:2,records:[row('Existing','已投递'),row('Applied','已投递'),row('New','待投递'),{...row('History','已投递'),id:'history-0',position:'待补充'}]});
    await page.waitForFunction(()=>!document.querySelector('#job-apply-record-sync').disabled);
    // Page JavaScript must not trigger a write through a synthetic event.
    await page.evaluate(()=>document.querySelector('#job-apply-record-sync').click());
    assert.equal(await page.evaluate(()=>window.writes.length),0);
    await page.locator('#job-apply-record-sync').click();
    await page.waitForFunction(()=>document.querySelector('#job-apply-record-control').dataset.syncStatus==='conflicts');
    const state=await page.evaluate(()=>({store:window.store,writes:window.writes}));
    const rows=state.store['autumnRecruitmentTracker.records.v1'];
    assert.equal(rows.length,5);
    assert.equal(rows.filter(r=>r.company==='History').length,1);
    assert.equal(rows.find(r=>r.company==='History').id,'history-0');
    assert.equal(rows.find(r=>r.company==='Existing').stage,'一面');
    assert.equal(rows.find(r=>r.company==='Applied').stage,'已投递');
    assert.equal(rows.find(r=>r.company==='Not in file').id,'unrelated');
    assert.equal(rows.find(r=>r.company==='New').applicationDate,'');
    assert.deepEqual(state.store['autumnRecruitmentTracker.resume.v1'],{awards:['keep'],custom:{nested:'unchanged'}});
    assert.ok(state.writes.every(keys=>keys.every(k=>!k.includes('resume'))));
    assert.equal(state.store['jobApply.recordSync.backups.v1'][0].records.length,4);
    await page.locator('#job-apply-record-sync').click();
    await page.waitForFunction(()=>document.querySelector('#job-apply-record-result').textContent.includes('新增0，更新0'));
    assert.equal(await page.evaluate(()=>window.store['autumnRecruitmentTracker.records.v1'].length),5);
    await page.locator('#job-apply-record-rollback').click();
    await page.waitForFunction(()=>document.querySelector('#job-apply-record-control').dataset.syncStatus==='rolled-back');
    assert.equal(await page.evaluate(()=>window.store['autumnRecruitmentTracker.records.v1'].length),4);
    assert.deepEqual(await page.evaluate(()=>window.store['autumnRecruitmentTracker.resume.v1']),{awards:['keep'],custom:{nested:'unchanged'}});
    console.log('PASS: trusted uploads/clicks, record merge, idempotence, conflict preservation, rollback backup, resume unchanged.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
