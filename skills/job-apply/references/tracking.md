# 进度记录规范

JSON 数组为主记录，CSV 与 HTML 为导出视图。每次确认投递、出现验证阻碍或收到新反馈后更新；“实时”指任务运行期间逐项更新，不表示后台永久监控。

每条记录支持 id、company、position、date、status、next、note、url、location、source、evidence、updated_at。date 为实际投递日期（YYYY-MM-DD），未知填空串；updated_at 为记录更新时刻，不能混淆两者。

示例（仅虚构数据）：

~~~json
{
  "company": "示例新公司",
  "position": "产品经理",
  "date": "",
  "status": "待确认",
  "location": "城市甲",
  "next": "查询站内应聘记录确认是否提交成功",
  "source": "招聘网站",
  "evidence": "提交后连接超时，尚未看到成功回执",
  "url": "https://example.com/jobs/product"
}
~~~

状态：待筛选、待投递、待登录、待确认、已投递、筛选中、测评中、面试、Offer、拒绝/已结束、跳过。

证据规则：

- 用户提供已投公司：可以记“已投递”，source 写用户提供，岗位和日期未知保留空白；不要伪造站内核验。
- 仅打开表单、上传附件或保存草稿：不能记已投递。
- 自动回执：只能证明接收了申请，不能推断面试。
- 状态变化需新证据，接口 200 不等于业务成功。请求超时先核实，避免重复申请。
- 同一公司不同岗位历史可分别保留，筛选时按用户配置的 company 或 company-role 去重。

tracker.py 的 upsert 按规范化公司名与岗位匹配；每次覆盖都要求 evidence，不代替判断证据真假。history 记录岗位未知且启用 company-role 时，screen 返回 review_duplicate，不把未知岗位当成可投。

真实数据只写入用户工作目录。公开仓库只保留虚构示例；不要记录密码、验证码、会话 cookie、身份证号或申请编号。实际申请表仅填写岗位要求且经用户授权的个人资料。
