---
name: job-browser-setup
description: 为求职投递检查并配置真实浏览器连接，优先复用现有工具，按需安装 huashu-chrome，并把扩展启用、登录和验证码交接给使用者。
---

# 求职浏览器配置

本 skill 与 job-apply 一起分发，只负责连接准备和恢复，不代表用户授权提交申请。

## 先复用

发现已启用的浏览器工具，读取当前工具说明，列出可连接浏览器/标签页，确认与用户选择一致。不要因工具名字包含 Chrome 就声称已连 Edge，也不要假定不同浏览器共享登录。连接正常后交回 job-apply；无需重复安装。

## 缺少工具时

优先使用本包安装脚本的 --with-browser 选项，或根据 [huashu-chrome 官方说明](https://github.com/alchaincyf/huashu-chrome)配置。当前分发器使用 huashu-chrome 1.3.0；安装其他版本先核对其安装命令和兼容性。

~~~sh
npx -y huashu-chrome@1.3.0 install --dry-run
npx -y huashu-chrome@1.3.0 install
npx -y huashu-chrome@1.3.0 doctor
~~~

先展示预览，说明第三方安装器会为检测到的客户端写入 MCP 配置；用户请求整套安装可执行该范围，未授权安装则先说明所需依赖。保留现有配置和登录状态，不复制其他环境的 cookie 或密钥。

扩展由使用者在浏览器里安装和启用；需要调试/安全权限时交由人决定，不用电脑控制去绕过系统或浏览器拦截。安装后必要时请用户重新载入客户端，让 MCP 工具可见。

## 验证与交接

调用实际 tabs/list 或对应工具的连接探测；出现 NO_EXTENSION 时请用户点击扩展重连，按工具规定停止重试。没有连接不能靠反复刷新申请页解决。

huashu-chrome 使用 learnings 查询站点经验，tabs 新页设 label、保留 tabId；登录、扫码、验证码和 CAPTCHA 使用 ask。遵守工具自身的能力边界与确认规则，不把本 skill 作为降低限制的理由。

交付连接状态、实际浏览器、目标标签页及仍需用户处理的事项。不要将登录成功等同于投递成功，不默认开启后台长期任务。
