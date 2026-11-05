# 本地替代方案：autumn-job-assistant-tracker

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

本仓库不附带上游扩展源码。核对时上游没有 LICENSE 文件，因此以使用者直接下载的独立依赖接入，不将其源码复制到本仓库的 MIT 许可范围。

兼容处理（仅指定提交）：

- 新安装时资料库和投递表为空，不把演示人物或示例申请作为真实资料。
- 自动填表只使用实际保存的字段，不补民族、政治面貌、接受调剂、到岗时间、应聘理由、缺失的生日日期等。
- 相同原生字段标签出现多次时跳过批量填写，防止多段学校/经历填成第一条。
- 收录时按非空相同 URL 或规范化公司+岗位阻止重复；这不替代 skill 中公司别名级查重。
- 修正空 records 数组导入无法清空演示记录的问题。

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
