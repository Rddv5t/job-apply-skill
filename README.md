# Job Apply Skills · 通用求职投递助手

让 AI 根据简历和求职偏好筛选岗位，在真实浏览器中先查重再申请，并保存有证据的求职进度。

适用于校招、社招、实习；行业、岗位、城市、国家和去重范围均由使用者配置。仓库只包含通用能力与虚构示例，不包含作者或使用者的简历、联系方式、登录信息及真实投递记录。

## 包含什么

| 内容 | 作用 |
|---|---|
| job-apply | 偏好整理、公司别名去重、岗位资格核对、表单填写、提交核验、进度管理 |
| job-browser-setup | 配置浏览器工具，验证连接，交接登录、验证码和扫码 |
| tracker.py | 无第三方 Python 依赖，合并 JSON 记录、筛选候选、导出 CSV 与可搜索 HTML |
| install.py | 将两个 skill 安装到 Codex，按需安装 huashu-chrome 浏览器工具 |
| 本地简历助手接入 | 按指定提交下载 autumn tracker，移除示例资料与缺失字段默认推断，支持备份互通 |

## 首次使用顺序

1. **先配置资料工具**：优先运行下面的 --with-tracker 安装本地秋招助手兼容版；已有或偏好 [OfferLink](https://offerlink.tech/) 也可继续使用。
2. **录入自己的信息和简历**：本地扩展进入“我的简历资料库”，按字段录入或导入 JSON；OfferLink 进入“我的简历”。核对日期与附件是否一致。本地扩展不承诺 PDF/DOCX 解析，附件从招聘页面上传。
3. **再告诉助手三组意向排序**：意向工作岗位、意向工作城市、意向行业分别按 **1 → 2 → 3** 排列，1 为最高优先级。
4. **补充限制与已投记录**：说明是否只考虑列出的城市、海外排除地区和已投公司，随后开始查重与筛选。

使用者可以这样回答：

~~~text
岗位：1. 岗位甲；2. 岗位乙；3. 岗位丙
城市：1. 城市甲；2. 城市乙；3. 城市丙
行业：1. 行业甲；2. 行业乙；3. 行业丙
城市是否仅限上述范围：是 / 否
海外是否接受、排除地区：……
已投公司：……
~~~

可以少于三个意向，无需凑满。城市优先级与“只去哪些城市”分别记录；skill 不会默认套用作者的偏好。具体流程见 [首次使用引导](skills/job-apply/references/onboarding.md)。

资料插件与浏览器控制工具是两项不同准备。扩展启用、个人资料录入及必要登录需要使用者在浏览器完成；本包安装器不会静默安装扩展。提交与结果核验由投递流程处理。

本地兼容方案已在虚构表单和 service worker 中验证基础填写、缺失字段留空、重复岗位拦截；复杂 ATS、附件上传与 OCR 准确率尚未完成端到端验收，不能声称全面等效替代。具体接入、上游问题和测试边界见 [本地扩展说明](skills/job-apply/references/autumn-tracker.md)。

核心进度管理已随包提供，不依赖另外下载 offer skill。浏览器优先使用已连接且支持用户指定浏览器的工具；可选使用 MIT 开源项目 [huashu-chrome](https://github.com/alchaincyf/huashu-chrome)。浏览器工具是单独的软件依赖，不是被复制进本仓库的 skill。其他环境的电脑控制、PDF 或简历编辑技能按需使用，不打包专有插件。

## 下载与安装

下载 GitHub 仓库 ZIP 并解压，或克隆仓库。在仓库根目录运行：

~~~sh
python install.py
~~~

连本地简历助手与浏览器控制依赖一起准备：

~~~sh
python install.py --with-tracker --with-browser
~~~

--with-tracker 从 [原作者仓库](https://github.com/ljkss/autumn-job-assistant-tracker)下载固定提交并校验源文件，再在个人目录应用兼容处理；输出目录需使用者在浏览器中“加载未打包/已解压的扩展程序”。本仓库只发布自己的接入脚本，不重新分发上游源码。扩展资料与投递记录仍由使用者本地保管。

安装默认尊重 CODEX_HOME；未设置时使用 ~/.codex/skills。支持 Windows、macOS、Linux，需要 Python 3.10+。安装完成后在 Codex 新聊天中使用；必要时重新载入客户端。

连浏览器工具一起配置（额外需要 Node.js/npm）：

~~~sh
python install.py --with-browser
~~~

脚本先显示 huashu-chrome 安装预览，再询问是否运行其安装器。第三方安装器可能为已检测到的 AI 客户端添加 MCP 配置。扩展的安装与启用由使用者在浏览器内完成。已有工具连接时无需重复安装。实际可控制的浏览器以 tools 的 tabs 返回结果为准，不承诺已连接 Edge 或跨浏览器共享登录。

~~~sh
python install.py --dry-run
python install.py --target /custom/skills
python install.py --overwrite
~~~

默认不覆盖已存在的不同版本；--overwrite 会先在目标目录旁生成时间戳备份。

## 使用

在聊天里调用：

~~~text
使用 $job-apply。先检查我的本地秋招助手（或已有 OfferLink）和已保存简历。
资料核对完成后，问我岗位、城市、行业各自的 1/2/3 优先级。
根据我的简历和岗位表筛选并投递。
已投过的公司不再投，先检查站内应聘记录。
登录与验证码交给我。每次投递成功后更新本地进度表。
~~~

也可以只要求“先筛选不要投递”“整理历史投递”“暂停并交接”。未授权投递时不会把筛选请求当成提交授权。自动化遇到登录、验证码、扫码或不能确认的结果时交还给人，不重复点击提交。

## 进度工具

把示例配置复制到自己的工作目录再填写；不要把真实数据放进这个公开仓库。

~~~sh
python skills/job-apply/scripts/tracker.py screen --config skills/job-apply/references/config.example.json --candidates skills/job-apply/references/candidates.example.json
python skills/job-apply/scripts/tracker.py upsert --data /private/search/records.json --record /private/search/new-record.json
python skills/job-apply/scripts/tracker.py export --data /private/search/records.json --out /private/search/report
~~~

export 生成 application-tracker.html 和 application-records.csv。HTML 可搜索并按状态筛选；JSON 是主记录，每次更新后重新导出即可。网页不向外部服务发送数据，也不会在聊天结束后自动检查邮件或招聘进度。

状态与数据结构见 [进度记录规范](skills/job-apply/references/tracking.md)。工具不会替代岗位阅读、简历真实性核对或站内查重。

## 已覆盖的操作问题

- 同公司多个品牌、中文名、英文名或子公司：仅依据用户确认或可靠证据维护别名，不按名字相似随意合并。
- 汇总表说某城市、某学历，具体岗位不同：以具体职位要求为准。
- 个人简历和填表插件日期不一致：先确认，再同步表单和附件。
- 接口返回压缩的飞书表格：查看页面实际请求与响应结构，不依赖固定端点。
- 提交后超时或没有成功提示：记录“待确认”，先查应聘记录，不重投。
- 导入资料含获奖、校园或自定义模块：完整显示、编辑与保存，不因上游编辑器只支持固定模块而丢失信息。
- 用户最近编辑的资料优先保留，简历与作品集按原件上传；投递授权不包含修改文件。
- 作品集按使用者选择的 PDF 与网站链接提交，缺失必填信息只询问当前所需内容。
- 用户暂停：停止外部投递，保存进度和需要接手的浏览器页面。

## 验证范围

安装脚本、记录合并、公司别名去重、地点筛选、CSV/HTML 导出可通过本地演示验证。招聘站点会改变表单、登录方式和限制；本包没有声称能绕过这些限制，也未对每家网站做端到端验证。

## 开源许可

本仓库原创内容采用 MIT License。第三方浏览器工具由其原仓库分发并按原许可使用；本仓库不携带它的扩展代码、账户数据或私有插件。
