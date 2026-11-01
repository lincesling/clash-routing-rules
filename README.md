# Clash 分流规则

这是一个可直接交给 Subconverter / OpenClash 使用的 Clash 分流模板。

主文件：

```text
clash-routing.ini
```

它负责规则顺序、策略组、节点地区筛选和测速参数；机场节点仍来自你自己的订阅。

## 已经整理的内容

- 删除无效的 `GEOIP,应用名` 写法，应用域名统一交给 `GEOSITE`。
- 修复被全角标点、重复段落和空格破坏的 URL。
- 修正 `url-test` 参数为 `间隔,超时,容差 = 300,5,50`。
- 将 CN、GFW、非标端口和 Aethersailor 代理补丁移到精确应用规则之后。
- 将 Steam 放到宽泛的 `category-games` 之前，避免 Steam 分组永远不命中。
- 默认数据源使用 `category-games-cn`，同时兼容未启用 Meta 属性的 geosite 数据。
- 用显式规则处理 `google.cn` 等中国大陆 Google 域名。
- 修复节点地区正则中的双反斜杠问题。
- 保留公告、套餐、到期、客服等机场伪节点过滤。

## 使用方式

这个仓库文件本身不是节点订阅，不能单独提供任何代理节点。完整 Clash 订阅需要和你的机场订阅一起转换。

Subconverter 请求格式：

```text
http://127.0.0.1:25500/sub?target=clash&url=<URL编码后的机场订阅>&config=<URL编码后的本模板地址>
```

把生成后的完整链接导入 Clash / Mihomo / Clash Verge Rev 即可。

本模板已经编码好的 `config` 参数：

```text
config=https%3A%2F%2Fraw.githubusercontent.com%2Flincesling%2Fclash-routing-rules%2Fmain%2Fclash-routing.ini
```

只替换 `url=<URL编码后的机场订阅>` 即可。机场订阅含访问凭据，建议使用自己的 Subconverter，不建议提交给来路不明的公共转换服务。

本模板的 Raw 地址：

```text
https://raw.githubusercontent.com/lincesling/clash-routing-rules/main/clash-routing.ini
```

仓库地址：<https://github.com/lincesling/clash-routing-rules>

## 策略组说明

- `🚀 手动选择`：总代理出口。
- `🌐 Default`：应用分组的默认选择入口。
- `🐟 漏网之鱼`：最终兜底。
- `🧭 全部节点`：显示所有可用节点。
- `🧊 冷门节点`：排除 HK、TW、JP、SG、US 后的节点池。
- `♻️ 自动选择`、五地区组：`url-test` 自动延迟测试组。

## 本地校验

```bash
python scripts/validate_rules.py
```

仓库已配置 GitHub Actions，每次修改规则会自动执行同一项校验。

## 数据源

- Subconverter: <https://github.com/tindy2013/subconverter>
- Aethersailor 补充规则: <https://github.com/Aethersailor/Custom_OpenClash_Rules>
- V2Fly 域名分类: <https://github.com/v2fly/domain-list-community>
- Loyalsoldier 规则数据: <https://github.com/Loyalsoldier/v2ray-rules-dat>
