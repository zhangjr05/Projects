# 豆瓣电影爬虫

一个用于爬取豆瓣电影 Top 250 信息的 Python 脚本，可获取电影基本信息和短评。

## 功能特点

- 爬取豆瓣 Top 250 电影列表
- 获取电影详细信息（名称、评分、导演、类型、时长等）
- 收集每部电影的短评（默认60条）
- 将所有数据保存为结构化的 JSON 文件 并保存到本地 mysql 数据库

## 环境要求

- Python 3.6+
- 依赖库：
  - requests
  - BeautifulSoup4
  - re
  - json
  - time
  - random
  - os
  - pymysql
- 安装 mysql

## 使用方法

1. **克隆或下载此项目到本地**

2. **安装所需依赖库**

    ```bash
    pip install requests beautifulsoup4 pymysql
    ```

3. **根据需要修改 `main.py` 中的配置**
   - `MOVIE_RANGE` - 要爬取的电影(区间)
   - `COMMENT_COUNT` - 每部电影要爬取的短评数
   - `PASSWORD` - 你的 mysql 密码
   - `HEADERS` - 请求头信息，随时更新 Cookie

4. 运行

    ```bash
    python main.py
    ```

## 数据格式

脚本爬取的 JSON 数据包含以下字段：

- `no`: 电影排名
- `name`: 电影名称
- `rating`: 评分
- `rating_count`: 评分人数
- `year`: 上映年份
- `country`: 上映国家
- `language`: 语言
- `runtime`: 时长
- `IMDb`: IMDb
- `intro`: 简介
- `directors`: 导演
- `scriptwriters`: 编剧
- `stars`: 主演
- `genres`: 类型
- `screening_dates`: 上映时间
- `other_name`: 别名
- `short_comments`: 短评列表（每条包含作者、时间、内容、评分和点赞数）

## 注意事项

- 爬虫设置了随机延时以降低被封禁的风险
- 请遵守豆瓣的使用条款，不要过于频繁地爬取数据
- 可能需要更新 Cookie 信息以确保脚本正常运行
- 建议定时更换代理位置以防被封

## 免责声明

本项目仅供学习和研究网络爬虫技术使用，请勿用于商业目的或其他可能违反豆瓣服务条款的用途。使用本脚本产生的任何后果由使用者自行承担。

## Tips

有问题可与作者交流~~
