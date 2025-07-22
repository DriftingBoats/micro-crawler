# 微博头条文章爬虫

一个专门用于爬取微博头条文章的Python爬虫工具，支持连续爬取专栏的所有章节，并提供Cookie认证功能。

## 功能特性

- 🚀 **专栏章节爬取**：自动识别并连续爬取专栏的所有章节
- 🔐 **Cookie支持**：支持多种Cookie格式，可访问需要登录的内容
- 📝 **多格式输出**：同时生成JSON和Markdown格式的结果文件
- 🛠️ **调试模式**：提供详细的调试信息，便于问题排查
- 🌐 **编码智能检测**：自动检测并处理GBK、GB2312等编码格式
- ⚙️ **命令行界面**：支持丰富的命令行参数配置
- 📊 **进度显示**：实时显示爬取进度和状态
- ✨ **盘古之白**：自动在中文字符和英文字母/数字之间添加空格，提升阅读体验

## 支持的URL格式

- `https://weibo.com/ttarticle/x/m/show#/id=xxx`
- `https://weibo.com/ttarticle/p/show?id=xxx`
- 其他微博头条文章链接

## 安装依赖

### 方法一：使用pip安装

```bash
pip install -r requirements.txt
```

### 方法二：手动安装

```bash
pip install requests>=2.31.0 beautifulsoup4>=4.12.0 lxml>=4.9.3
```

## 使用方法

### 基本用法

```bash
# 直接指定URL
python weibo_ttarticle_crawler.py "https://weibo.com/ttarticle/x/m/show#/id=xxx"

# 交互式输入URL
python weibo_ttarticle_crawler.py
```

### 高级用法

```bash
# 指定最大爬取章节数
python weibo_ttarticle_crawler.py "URL" --max-chapters 10

# 使用指定的Cookie文件
python weibo_ttarticle_crawler.py "URL" --cookies cookies.json

# 启用调试模式
python weibo_ttarticle_crawler.py "URL" --debug

# 组合使用多个参数
python weibo_ttarticle_crawler.py "URL" -m 20 -c cookies.txt -d
```

### 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `url` | - | 要爬取的微博头条文章URL | 无（必需） |
| `--max-chapters` | `-m` | 最大爬取章节数 | 50 |
| `--cookies` | `-c` | Cookie文件路径 | 自动检测 |
| `--debug` | `-d` | 启用调试模式 | 关闭 |

## Cookie配置

### 自动检测

程序会自动查找以下文件：
- `cookies.json`
- `cookies.txt`

### Cookie获取方法

1. **登录微博**：在浏览器中访问 https://weibo.com 并登录
2. **打开开发者工具**：按F12或右键选择"检查元素"
3. **切换到Network标签页**
4. **刷新页面**：找到weibo.com的请求
5. **复制Cookie**：在请求头中找到Cookie值

### Cookie文件格式

#### JSON格式（推荐）

创建 `cookies.json` 文件：

```json
{
  "SUB": "your_sub_value_here",
  "SUBP": "your_subp_value_here",
  "SINAGLOBAL": "your_sinaglobal_value_here",
  "XSRF-TOKEN": "your_xsrf_token_here"
}
```

#### 字符串格式

创建 `cookies.txt` 文件：

```
SUB=your_sub_value; SUBP=your_subp_value; SINAGLOBAL=your_sinaglobal_value
```

## 输出文件

### JSON格式

文件名：`ttarticle_chapters_YYYYMMDD_HHMMSS.json`

```json
{
  "all_chapters": [
    {
      "chapter_number": 1,
      "title": "章节标题",
      "content": "章节内容",
      "author": "作者",
      "publish_time": "发布时间",
      "next_chapter_url": "下一章链接"
    }
  ],
  "other_articles": [],
  "crawl_time": "2024-01-22T16:46:41.123456",
  "total_chapters": 1,
  "total_other_articles": 0
}
```

### Markdown格式

文件名：`ttarticle_chapters_YYYYMMDD_HHMMSS.md`

```markdown
## 第一章 标题

章节内容...

## 第二章 标题

章节内容...
```

## 故障排除

### 常见问题

1. **无法访问内容**
   - 检查Cookie是否有效
   - 确认账号有访问权限
   - 尝试更新Cookie

2. **乱码问题**
   - 程序已自动处理GBK编码
   - 如仍有问题，请开启调试模式查看详情

3. **爬取失败**
   - 检查网络连接
   - 降低爬取频率（程序已内置延时）
   - 使用调试模式查看详细错误信息

4. **Cookie保存失败**
   - 提示"multiple cookies with name"通常不影响功能
   - 只有在无法访问内容时才需要更新Cookie

### 调试模式

启用调试模式会生成以下文件：
- `article_debug_X_ARTICLEID.html`：API响应的HTML内容
- `article_debug_X_ARTICLEID.json`：API响应的JSON数据
- `article_error_X_ARTICLEID.txt`：错误信息

## 技术特性

- **多API支持**：尝试多个微博API接口确保成功率
- **智能重试**：自动处理网络错误和临时限制
- **编码检测**：自动检测并转换GBK、GB2312等编码
- **格式化输出**：统一段落间距，优化阅读体验
- **Cookie管理**：自动保存和加载Cookie状态
- **盘古之白格式化**：自动在中文字符和英文字母/数字之间添加空格，遵循中文排版规范，提升文档可读性

## 注意事项

- 🚨 **仅供学习研究使用**，请遵守微博使用条款
- 🚨 **控制爬取频率**，避免对服务器造成压力
- 🚨 **保护个人隐私**，不要分享Cookie文件
- 🚨 **合规使用**，不要用于商业用途或大规模数据采集

## 系统要求

- Python 3.7+
- Windows/Linux/macOS
- 网络连接

## 更新日志

### v2.1.0
- ✨ 新增盘古之白功能：自动在中文字符和英文字母/数字之间添加空格
- 🔧 优化文本格式化处理，提升阅读体验
- 📝 更新文档说明

### v2.0.0
- 添加连续章节爬取功能
- 支持多种Cookie格式
- 优化编码处理
- 添加调试模式
- 改进输出格式

### v1.0.0
- 基础爬取功能
- JSON和文本输出

## 许可证

本项目仅供学习和研究使用。使用时请遵守相关法律法规和网站使用条款。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**免责声明**：本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不承担任何法律责任。