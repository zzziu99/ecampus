# E校园 — 北交大校园智能问答助手

基于 Claude Code + Cursor AI 辅助开发的北交大校园百事通系统。集成 12 个分类 686+ 条校园问答知识库 + DeepSeek AI 问答引擎，提供一站式校园信息查询服务。

## 功能特性

- **智能问答**：知识库检索 + DeepSeek AI 生成混合回答，支持联网搜索
- **分类浏览**：图书馆、食堂、宿舍、选课、考试、奖学金等 12 个分类
- **校园资讯**：自动抓取 news.bjtu.edu.cn 头条新闻
- **食堂推荐**：覆盖海淀/威海/唐山三校区 18 个食堂
- **匿名树洞**：匿名发帖交流
- **校历查询**：学期安排一目了然
- **PWA 支持**：可添加到手机桌面，离线访问
- **深色模式**：跟随系统或手动切换

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask + SQLite |
| 前端 | 原生 JavaScript + PWA |
| AI | DeepSeek API + DuckDuckGo 搜索 |
| 开发工具 | Claude Code + Cursor AI |

## 快速启动

```bash
git clone https://github.com/zzziu99/ecampus.git
cd ecampus
pip install -r requirements.txt
python app.py
```

浏览器打开 `http://localhost:5000`

## 数据来源

- 北京交通大学官网公开信息
- news.bjtu.edu.cn 公开新闻
- 各学院培养方案公开文件

## 许可证

MIT
