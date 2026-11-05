# 首选资料工具与升级基础：autumn-job-assistant-tracker

## huashu 可操作的记录控制页

兼容版新增 `job-apply-record-control.js`，在普通本机网页提供 huashu 可操作的记录控件，无需跨扩展访问 dashboard。仅在 `http://127.0.0.1:18765/records` 激活；不增加扩展权限，不对外网开放接口，也不接受任意网页 postMessage 指令。

1. 修改扩展目录后，由用户在扩展管理页重新加载秋招助手，再刷新控制页。旧内容脚本不会自动升级。
2. 用 Python 启动本 skill 的 `scripts/record_control.py`，保留该进程；仅绑定 127.0.0.1，不添加开机启动。
3. huashu 新建上述本地控制页并保留 tabId，snapshot 确认出现“秋招助手 · 投递记录控制”。
4. 用 autumn_bridge.py export 生成仅记录 JSON，历史条目也要有来源证据，未知实际日期留空。使用 upload，将本地文件交给 `#job-apply-record-file`，等候校验完成。
5. 对 `#job-apply-record-sync` 使用真实点击（huashu click 的 real:true），控件拒绝网页脚本模拟提交。读取 `#job-apply-record-result` 和 `#job-apply-record-summary` 核验结果。有“同步成功”并核对条数才算完成；阶段冲突需报告。

只合并记录，不删除文件未包含的既有记录，不访问简历存储键。写入前保留记录备份；筛选/测评/面试/Offer等后续阶段与导入阶段不同时保留并报告冲突。重复同步不增加重复项。看板监听记录变更刷新列表，不重载简历编辑区。

验证：`node tests/record_control.test.cjs`（需 Playwright），覆盖数据校验、记录合并、重复同步、阶段冲突、写入前备份和简历不变。实际用户浏览器须重新加载后再验证，隔离测试不代表已同步。

上游：[ljkss/autumn-job-assistant-tracker](https://github.com/ljkss/autumn-job-assistant-tracker)。
本次核对提交：a24b328aef7d62bf81ee4d4581b701a45ebe848e。
README 写 v2.1，manifest 与 dashboard 的版本字段为 2.0.0，按提交定位实现。

## 适合替代什么

可以替代基础简历资料库、字段点击插入、部分规则式自动填表、岗位收录、投递看板与本地 JSON 备份。无须登录第三方求职账户即可使用这些本地功能。浏览器控制、公司去重与偏好排序继续由本 skill 负责。

不能据此承诺所有 ATS 填表与 OfferLink 等效。上游源码采用字段标签规则与原生 setter/input/change；没有在本次验证中证明 PDF/DOCX 简历解析、附件自动上传、复杂多段经历及所有自定义下拉控件可靠。多段经历应逐字段核对，文件用招聘页面的上传入口处理。OCR 引擎随下载保留，本次未验收 OCR 准确率。

## 安装与本地兼容处理

仓库根目录运行：

~~~sh
python install.py --with-tracker
~~~

或直接运行本 skill 的 scripts/prepare_autumn_tracker.py --dest /private/tools/autumn-tracker。
脚本从原作者仓库下载指定提交并校验 Git blob 哈希，应用兼容处理，再输出待加载目录。它不会替使用者开启开发者模式、扩展权限或加载扩展。

由使用者打开 chrome://extensions/（Edge 使用 edge://extensions/），自行启用开发者模式、点击“加载已解压的扩展程序”并选择输出目录。保持该目录存在，不将临时目录当长期扩展路径。

本仓库不附带上游扩展源码。截至 2026-11-05 核对时，上游文件与 README 中未发现 LICENSE 或明确许可声明。保留作者 ljkss、仓库链接及固定提交；本项目 MIT 仅适用于自己的原创接入代码。直接下载、本地适配或注明出处均不等于获得修改、再分发授权。若要公开发布包含上游代码的改版扩展，先确认原作者授权或适用许可证，并按其要求保留声明。

后续升级继续以该资料工具为基础，保留已保存的资料、获奖、校园及自定义模块；不重复初始化或用旧备份覆盖。上游更新时先检查许可与提交差异，在独立目录验证兼容脚本，再备份并由用户重新加载扩展；不将固定提交自动改成未经验证的 main。

兼容处理（仅指定提交）：

- 新安装时资料库和投递表为空，不把演示人物或示例申请作为真实资料。
- 自动填表只使用实际保存的字段，不补民族、政治面貌、接受调剂、到岗时间、应聘理由、缺失的生日日期等。
- 相同原生字段标签出现多次时跳过批量填写，防止多段学校/经历填成第一条。
- 收录时按非空相同 URL 或规范化公司+岗位阻止重复；这不替代 skill 中公司别名级查重。
- 修正空 records 数组导入无法清空演示记录的问题。
- 资料库动态显示获奖、校园、工作和其他导入模块，保存时保留这些模块；不再仅处理上游固定的六个模块。新增经历不预填日期、学历或角色。

遇到本地已有演示数据时不要擅自删除；先备份、说明并由使用者处理。复用旧扩展 ID 时的已有数据不会因为安装脚本运行而自动清除。

## 与进度主记录互通

先在扩展“数据安全/备份”导出完整 JSON；随后运行：

~~~sh
python scripts/autumn_bridge.py import --backup /private/backup.json --data /private/search/records.json
python scripts/autumn_bridge.py export --data /private/search/records.json --out /private/new-backup.json
~~~

导入到主记录时合并，不覆盖已有整表。导回扩展的文件只含记录，不包含简历，且在扩展导入会替换其记录列表，操作前备份并按工具规则确认。上游状态粒度较少，扩展中部分未确认状态显示为“待投递”；原状态保留在 jobApplyStatus 字段，往返时恢复，不提升为已投递。未知日期始终留空。

## 已做验证与边界

使用虚构资料在隔离 Chrome 页面验证了：原版会写入示例简历、重复收录两条相同岗位、将未提供的政治面貌/调剂意向及生日日期填成默认值；兼容版保留基础姓名填充，对上述缺失字段留空并拦截重复收录。

这些是隔离表单与 service worker 测试，不等于使用者实际浏览器已加载扩展或真实招聘站点已验收。安装状态需以其扩展列表、看板和测试页面为准。

资料库适配器另经隔离 Chrome 测试：导入两项获奖、校园经历和自定义嵌套字段，检查页面显示、保存、重载及新增空白条目；已有字段均保留。可选执行 tests/resume_editor.test.cjs，需要 Playwright。JOB_APPLY_EXTENSION_DIR 指向准备后的扩展目录时会同时验证实际 dashboard 的加载与保存接线。
