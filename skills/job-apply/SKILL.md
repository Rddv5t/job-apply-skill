---
name: job-apply
description: 根据简历和用户偏好筛选校招、社招或实习岗位，在已授权范围内查重、填写与投递，并维护有证据的求职进度；适用于岗位表批量投递、避免重复申请和整理招聘反馈。
---

# 通用求职投递助手

将用户的求职偏好、真实经历和历史投递转化为可执行候选队列与可复盘记录。先确定用户本次要筛选、准备草稿、实际投递还是更新进度；保留其已经提供的授权与限制，不把筛选请求扩大成提交。

## 首次使用：先资料，后意向

首次准备实际投递时，先阅读并执行 [首次使用流程](references/onboarding.md)：引导使用者从 OfferLink 官网安装插件 → 使用者录入、保存并核对自己的个人信息与简历 → 再询问意向岗位、意向城市、意向行业，分别按 1、2、3 从高到低排列。已有安装、资料或明确排序时复用并核对，不重复初始化；仅整理历史进度时不强制安装插件。

OfferLink 是资料和填表工具，job-browser-setup 是浏览器控制配置，二者均需说明用途。扩展启用和登录交由使用者。不能把本包安装成功当成 OfferLink 已安装或个人资料已录入。

## 建立配置

从已有对话、简历和指定资料提取岗位优先级、业务方向、允许及偏好地点、海外排除地区、学历届次、已投公司与去重范围；只问影响本次决策且缺失的信息。默认不设置固定行业、城市、薪资或毕业年份。配置结构见 [示例](references/config.example.json)。

分别将三组有序答案保存到 role_priority、preferred_locations、industry_priority，1 为最高优先级；城市排序不等于城市白名单，只有明确限定地点时才设置 allowed_locations。少于三个意向时不强求补齐。

同一字段来源冲突时请用户确认，不能选择看起来更有利的版本。若用户更新偏好，立即重排后续候选并保留已完成事实。

## 执行

1. 建立已投公司及经确认的别名映射。按用户的 company 或 company-role 范围去重；不确定的历史保留待确认。
2. 从用户指定的岗位表或渠道提取候选，按岗位和业务优先级排序，在同等匹配度下优先用户偏好地点。先排硬性资格，再评估经历匹配。
3. 进入具体职位页核对学历、专业、届次、地点、截止时间、经验和投递次数限制；公司汇总信息不能替代具体岗位要求。
4. 浏览器投递或站内查重前阅读 [浏览器工作流](references/browser-workflow.md)。连接未就绪时使用同包 job-browser-setup；不存在可用工具时说明实际缺口，不声称已操作。
5. 查历史、核对简历与附件、填写必填项。日期和经历修正要同步表单及附件。遇到登录、扫码或验证码交给用户；可以继续与其无关的筛选。
6. 在授权范围和工具要求内提交。读取回执并核查业务结果，再写入记录；超时不盲目重投，先查站内记录。
7. 每处理一项更新 JSON 主记录，导出 CSV 和可搜索 HTML；汇报新投成功、待用户处理、待确认和跳过原因。

用户说暂停时，立即停止外部投递并保存交接状态。不能把任务运行期间更新承诺为聊天结束后的后台监控；自动监控须由用户另行要求并配置。

## 进度工具

使用 [进度规范](references/tracking.md)。脚本只需 Python 3.10+，无第三方库。

~~~sh
python scripts/tracker.py screen --config /private/search/config.json --candidates /private/search/candidates.json --history /private/search/records.json
python scripts/tracker.py upsert --data /private/search/records.json --record /private/search/new-record.json
python scripts/tracker.py export --data /private/search/records.json --out /private/search/report
~~~

脚本路径以本 skill 目录为基准。screen 是确定性初筛，资格与具体地点仍需人工/agent 读取 JD；未知海外地点或历史岗位返回 review，不自动放行。HTML 是 JSON 的可搜索导出视图，修改主记录后重新生成。

真实简历、联系方式、历史名单和会话凭据留在用户的私有工作目录，不写回公开 skill 仓库或示例。状态要注明来源：用户确认与站内核验均可记录，但不能相互冒充；未知实际日期保留空白。
