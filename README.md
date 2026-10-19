# Quantumult X 分流规则库

按服务分类、可追溯、可检查的 Quantumult X 域名规则。用于补充和细化个人分流配置，不包含节点订阅、账户信息、证书、会员修改脚本或整套代理配置。

本项目区分业务归属与连接策略：规则文件描述域名属于哪些服务，主配置决定直连、代理、拒绝或使用哪个策略组。维护目标是减少宽泛匹配与规则交叉，不以规则数量衡量准确性。

## 当前范围

初始数据快照包含 **1,548 个上游分类**，已构建 **155 个常用业务模块、9,179 条域名条件**。数量随上游更新变化，以 [来源锁定记录](sources/lock.json) 与 [分类目录](catalog/services.csv) 为准。

| 分类 | 代表性模块 |
| --- | --- |
| AI 与模型 | OpenAI、Anthropic、Gemini、DeepSeek、Copilot、Cursor、Perplexity、Hugging Face |
| 办公与协作 | Microsoft、OneDrive、Notion、Slack、Zoom、Adobe、Figma |
| 谷歌服务 | Google、Google Play、Google FCM、Google Scholar |
| 苹果服务 | Apple、iCloud、Apple Intelligence、Apple Music、Apple TV+ |
| 学术与教育 | 知网、万方、DOI、IEEE、Elsevier、Springer、Zotero |
| 开发与软件 | GitHub、GitLab、Docker、Python、npm、JetBrains、Vercel |
| 社交与通讯 | Telegram、WhatsApp、Discord、LinkedIn、Reddit、微信、小红书 |
| 视频与音乐 | YouTube、Netflix、Disney、Spotify、TikTok、哔哩哔哩 |
| 游戏与下载 | Steam、Epic Games、PlayStation、Xbox、Nintendo、Synology |
| 国内常用服务 | 百度、腾讯、阿里巴巴、京东、美团、高德、银行与支付服务 |

这不是所有服务均已覆盖的承诺。完整上游分类在目录中可检索，只有“已构建”为 `True` 的分类才有本仓库的订阅文件。未选分类可在 `sources/selection.json` 中添加后重新构建。

## 使用

规则位于 `rules/services/<服务名>.list`，服务名使用小写英文，与上游分类名一致。

仓库发布后，Raw 链接格式为：

```text
https://raw.githubusercontent.com/OWNER/quantumultx-rules/main/rules/services/openai.list
```

`OWNER` 必须替换为实际仓库所有者。该地址是格式示例，未填写所有者前不能订阅。

在现有主配置的 `[filter_remote]` 中添加所需模块。例如：

```ini
[filter_remote]
https://raw.githubusercontent.com/OWNER/quantumultx-rules/main/rules/services/openai.list, tag=OpenAI, force-policy=狮城节点, update-interval=86400, opt-parser=false, enabled=true
https://raw.githubusercontent.com/OWNER/quantumultx-rules/main/rules/services/onedrive.list, tag=OneDrive, force-policy=direct, update-interval=86400, opt-parser=false, enabled=true
https://raw.githubusercontent.com/OWNER/quantumultx-rules/main/rules/services/cnki.list, tag=知网, force-policy=direct, update-interval=86400, opt-parser=false, enabled=true
```

“狮城节点”必须是你的配置中已存在的策略名称。示例仅说明写法，不表示对应服务必须使用该地区或必须直连。不要重复创建 `[filter_remote]` 段；将条目放入已有段落即可。

文件内部统一写 `proxy`，由 `force-policy` 覆盖。如果不设置该参数，文件内部策略将决定去向。规则已是 Quantumult X 格式，无需资源解析器。域名分流本身不需要 MITM。

建议逐个替换对应旧模块，检查实际命中后再继续。不要将所有模块同时启用，也不要把 Google、Microsoft 等集团集合与所有子服务随意叠加。具体业务有独立去向时，需结合客户端的规则优先级与实际日志检查集团规则是否覆盖子业务。

## 精度边界

- `full:` 转为 `host`，`domain:` 转为 `host-suffix`，保持明确域名与子域名匹配的区别。
- 递归解析上游 `include:`，按官方语法执行属性过滤与 affiliation，不把属性过滤误当属性添加。
- 去除同一文件内的重复条件。
- 带 `@ads` 的条件不放入业务规则，列入审查报告；本项目当前不提供广告拦截订阅。
- `keyword:`、`regexp:` 不直接混入业务文件，保留审查记录。因此生成结果不是上游的无损全量转换。
- 对共享云平台、公共认证、统计和支付平台的一组根域名采用显式审查名单；专用子域名仍可保留。这只是有限名单，不代表已识别全部共享基础设施。
- [模块交叉报告](reports/overlaps.csv) 包含同名条件和后缀包含关系。交叉不一定错误，也不代表已确定运行时谁优先。
- 同一域名可能同时供网页、客户端、登录和同步使用。仅靠域名规则无法可靠区分 OneDrive 网页与同步客户端，也不能按某个页面路径细分 HTTPS 流量。
- 规则不保证服务可访问、地区解锁或节点可用。纯 IP 请求、被隔离的正则条件、HTTPDNS 等情况不在当前域名文件的完整覆盖承诺之内。

如出现误分流，优先记录目标域名、实际命中的规则、预期策略和测试结果，再修正最小范围。不要通过新增 `wiki`、`xhs` 等宽泛关键词掩盖遗漏。

## 来源、署名与许可

许可核查日期：2026-10-19。许可信息以各来源实际文件及后续变更为准；“未确认”不表示作者已经拒绝授权。署名不能代替许可。

### 实际使用的数据

| 作者或项目 | 使用方式 | 许可及处理 |
| --- | --- | --- |
| [V2Fly / V2Ray 社区贡献者](https://github.com/v2fly/domain-list-community) | 保存上游域名数据；解析分类引用、筛选并转换为 Quantumult X 格式 | 已核对 [MIT 许可](https://github.com/v2fly/domain-list-community/blob/master/LICENSE)，保留原始版权声明和完整许可文本 |

上游完整原文在 `sources/v2fly/data/`，上游许可在 `sources/v2fly/LICENSE`。`sources/lock.json` 记录确切提交和原始压缩包哈希；生成文件头标明来源提交和本地修改。本项目自编维护工具同样采用根目录 [MIT 许可](LICENSE)，不改变其他来源的权利归属。

### 规则结构、目录与资料参考

以下来源用于了解分类、配置形式或提供原始入口。初始公开版本**没有复制或合并其规则正文、脚本及完整主配置**，也不声称获得作者专门授权。涉及未确认授权或额外声明的资源，不做自动镜像。

| 作者或项目 | 本次核查情况 | 本项目处理 |
| --- | --- | --- |
| [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script) | 根目录有 GPL-2.0 文件，README 另有转载及使用声明；规则还列有各自来源 | 仅保留分类入口与参考链接，未复制其规则进入公开版本 |
| [ConnersHua / RuleGo](https://github.com/ConnersHua/RuleGo) | 未从本次检查的根目录 LICENSE 与 README 确认明确再分发许可 | 保留规则文件来源索引，不复制正文 |
| [大飞 / w37fhy](https://github.com/w37fhy/QuantumultX) | 已查到 GPL-3.0 许可文件；配置中引用的第三方资源需另行判断 | 仅参考配置结构，不将 GPL 内容并入 MIT 数据 |
| [彭于晏 / 89996462](https://github.com/89996462/Quantumult-X) | README 与配置含转载、用途方面的限制性声明 | 仅保留来源链接 |
| [Shawn / KOP-XIAO](https://github.com/KOP-XIAO/QuantumultX) | 本次未确认明确再分发许可 | 参考模块说明与配置结构，不复制正文 |
| [Orz-3](https://github.com/Orz-3/QuantumultX) | 本次未确认明确再分发许可 | 参考分类结构，不复制正文 |
| [烧烤哥 / Tartarus2014](https://github.com/Tartarus2014/QuantumultX-Script) | 本次未确认明确再分发许可 | 仅保留来源链接 |
| [奇心 / zwf234](https://github.com/zwf234/rules) | 本次未确认网站配置的明确再分发许可 | 仅保留原始入口与引用记录 |
| [耳东橙 / erdongchanyo](https://github.com/erdongchanyo/Rules) | 本次未确认明确再分发许可 | 仅保留来源链接 |
| [懒人配置 / Sonmbs](https://github.com/Sonmbs/quantumult_X) | 本次未确认明确再分发许可 | 仅保留来源链接 |
| [Space / WSL33099](https://github.com/WSL33099/QuantumultX) | 原配置链接不可用，未确认许可 | 不复制内容 |
| [张军 / 28413761](https://github.com/28413761/QX) | 原配置链接不可用，未确认许可 | 不复制内容 |
| [墨鱼 / ddgksf2013](https://github.com/ddgksf2013/Filter) | 本次未确认明确再分发许可 | 仅作现有规则来源参考，不复制正文 |

说明：部分作者通过公共规则文件维护资源，不等于公开授予了所有使用方式的许可。本次只检查了可访问的声明文件与指定配置，没有联系作者请求授权，也未穷尽每个子目录的授权文件。未来若实际引入其他数据，应先核查具体文件许可，保留相应版权声明，并更新此表。

[Quantumult X 官方示例](https://github.com/crossutility/Quantumult-X)用于语法核对；[Loyalsoldier](https://github.com/Loyalsoldier/v2ray-rules-dat) 与 [MetaCubeX](https://github.com/MetaCubeX/meta-rules-dat)作为规则生态参考，初始版本没有复制其编译产物。[Steeefanie/personal-site](https://github.com/Steeefanie/personal-site)仅作中文 README 编排风格参考，未复制代码或正文。

## 目录

```text
README.md                   使用、来源、许可及维护说明
LICENSE                     MIT 许可及上游版权声明
rules/services/             可直接引用的业务域名规则
sources/selection.json      选定服务及分类
sources/lock.json           上游提交与数据哈希
sources/v2fly/              可追溯的 MIT 上游快照及许可
catalog/                    分类、博主引用与补充来源索引
reports/                    宽泛条件与模块交叉审查数据
tools/                      构建、校验、域名查询和提交检查工具
.github/workflows/          规则校验流程
```

## 维护

环境要求：Python 3.10 或以上，仅使用标准库。

```bash
# 校验现有文件，并核对其是否与上游快照的转换结果一致
python3 tools/build.py --check

# 测试引用过滤、循环引用、共享域名等边界
python3 -m unittest discover -s tools -p 'test_*.py'

# 查询一个域名在哪些已构建服务中匹配
python3 tools/query.py chatgpt.com

# 拉取上游并重新生成；不会自动提交或推送
python3 tools/build.py --refresh
```

上游许可不再为已核查的 MIT、分类引用缺失、循环引用或选定模块无法生成时，构建会报错。上游网络请求失败时，不发布空文件。刷新后必须检查来源变化、规则增减及交叉报告，再执行验证与提交。

GitHub Actions 会在推送、PR 或手动运行时校验规则。初始版本不启用定时同步，也不自动提交上游变化。以后增加自动更新，应明确更新频率、失败处理和变更审阅方式。

### 提交与 PR 规范

采用 Conventional Commits，格式为 `type(scope): 中文变更说明`。标题说明与正文均使用中文；类型、范围、服务名、协议字段和必要技术术语可保留英文。标题控制在 72 个字符以内。

| 类型 | 用途 | 示例 |
| --- | --- | --- |
| `feat` | 新增规则模块或能力 | `feat(ai): 新增模型服务分类` |
| `fix` | 修正遗漏、误匹配或错误转换 | `fix(onedrive): 收紧共享域名匹配范围` |
| `refactor` | 调整组织方式且不改变预期行为 | `refactor(rules): 拆分服务分类定义` |
| `chore` | 上游同步及维护记录 | `chore(upstream): 同步社区域名数据` |
| `docs` | 文档调整 | `docs(readme): 补充来源许可说明` |
| `test` | 测试与边界验证 | `test(parser): 覆盖属性筛选场景` |
| `ci` | 校验流程调整 | `ci(validation): 添加中文提交检查` |

固定常用范围：`rules`、`upstream`、`parser`、`catalog`、`validation`、`readme`、`ai`、`onedrive`、`google`、`apple`、`media`、`gaming`、`scholar`。新增具体服务范围时沿用小写英文及连字符。

正文写明修改原因、主要变更、影响范围、来源及许可、验证结果；没有完成设备验证时如实说明。PR 标题遵循同一格式，合并时保留有意义的中文说明。破坏性变更使用 `!` 并在正文加入 `BREAKING CHANGE: 中文迁移说明`。

本地可使用 `.gitmessage` 作为提交模板，并在提交前运行：

```bash
python3 tools/check_commit.py 提交消息文件
```

### 反馈误分流

反馈请包含服务名称、目标域名、当前命中的规则或模块、预期策略和复现结果。不要提交完整节点配置、私人订阅链接、访问令牌、证书、Cookie 或带个人信息的完整请求日志。

## 初始版本记录

2026-10-19：建立许可明确的数据基础、服务模块、上游快照、来源索引及静态校验流程。当前仅完成格式、转换一致性和自动化测试；尚未在真实 Quantumult X 设备完成逐项业务验证。
