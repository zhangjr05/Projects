import os
import re
import time
import json
import random
import pymysql
import requests
from bs4 import BeautifulSoup

# 设定你的 mysql 密码
PASSWORD = 'your password'

# 设定要爬取的电影(第i部到第j部)
MOVIE_RANGE = (1, 10)

# 设置每部电影要爬的短评数
COMMENT_COUNT = 60

# 豆瓣 Top 250 的 URL
BASE_URL = "https://movie.douban.com/top250"

# 请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Cookie": 'bid=OQuhhchhpsU; _pk_id.100001.4cf6=a3c9f3b94181bdc1.1743497797.; __yadk_uid=w9UzsKIGoQpvsxJKMAm9Do3wyIefUqPL; ll="118159"; dbcl2="285887997:V+pLcM3/O94"; ck=xbwl; push_noty_num=0; push_doumail_num=0; frodotk_db="62249aeb1b10f2c6266dd0c15132d852"; __utmc=30149280; __utmz=30149280.1743600457.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmc=223695111; __utmz=223695111.1743600457.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=D0215FA17C45C48CA96125BE6A0C92712|05c8fe408310efe223bb316bd09c3f6c; __utma=30149280.1901610314.1743600457.1743600457.1743602737.2; __utma=223695111.552024510.1743600457.1743600457.1743602737.2; __utmb=223695111.0.10.1743602737; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1743602737%2C%22https%3A%2F%2Faccounts.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1; ap_v=0,6.0; __utmt_douban=1; __utmt=1; __utmv=30149280.28588; __utmb=30149280.6.10.1743602737',
    "Referer": "https://movie.douban.com/",
}


def get_json_path():
    '''获取json文件的路径'''
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "douban_movies.json")
json_path = get_json_path()


def get_movie_links():
    """
    获取豆瓣 Top 250 的电影详情页链接
    """
    movie_links = []
    for start in range(0, 250, 25):  # 每页 25 部电影，共 10 页
        url = f"{BASE_URL}?start={start}"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 提取电影详情页链接
        for tag in soup.select(".hd a"):
            movie_links.append(tag["href"])
        
        time.sleep(random.uniform(1, 2))  # 随机延时，降低被封风险
    return movie_links

def extract_movie_id(url):
    """
    从电影URL中提取电影ID
    """
    pattern = r"subject/(\d+)/"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_movie_comments(movie_id, comment_count=COMMENT_COUNT):
    """
    获取指定数量的电影短评
    """
    comments = []
    start = 0
    limit = 20  # 豆瓣每页显示20条评论
    
    while len(comments) < comment_count:
        # 构建评论页URL
        comment_url = f"https://movie.douban.com/subject/{movie_id}/comments?start={start}&limit={limit}&status=P&sort=new_score"
        
        response = requests.get(comment_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        comment_items = soup.find_all("div", class_="comment-item")
        
        if not comment_items:
            break  # 没有更多评论了
            
        for comment in comment_items:
            # 提取评论信息
            try:
                comment_info = {
                    "author": comment.find("span", class_="comment-info").a.text.strip(),
                    "time": comment.find("span", class_="comment-time").text.strip(),
                    "content": comment.find("span", class_="short").text.strip(),
                    "rating": "未评分"
                }
                
                # 提取评分
                rating_span = comment.find("span", class_=lambda x: x and x.startswith("allstar"))
                if rating_span:
                    rating_class = rating_span.get("class")[0]
                    rating_value = rating_class.replace("allstar", "")
                    comment_info["rating"] = f"{int(rating_value) // 10}星"
                
                # 提取点赞数
                votes_span = comment.find("span", class_="votes")
                comment_info["useful"] = votes_span.text.strip() if votes_span else "0"
                
                comments.append(comment_info)
            except Exception as e:
                print(f"解析评论时出错: {e}")
        
        # 更新起始位置，获取下一页评论
        start += limit
        
        # 已经获取足够数量的评论或者没有下一页了
        if len(comments) >= comment_count or not soup.find("a", class_="next"):
            break
            
        # 随机延时，降低被封风险
        time.sleep(random.uniform(1, 2))
    
    return comments[:comment_count]  # 返回指定数量的评论

def get_movie_details(movie_url):
    """获取单部电影的详细信息和短评"""
    try:
        response = requests.get(movie_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 初始化电影信息字典
        movie_info = {"no": "未知", "name": "未知", "rating": "未知", "rating_count": "0", "year": "未知", "country": "未知", "language": "未知", "runtime": "未知", "IMDb": "未知", "intro": "未知"}
        
        # 提取排名
        no = soup.find("span", class_="top250-no")
        if no:
            no = no.text.strip()
            movie_info["no"] = re.match(r"No.(\d*)", no).group(1)

        # 提取影片名
        name_element = soup.find("span", property="v:itemreviewed")
        if name_element:
            movie_info["name"] = name_element.text.strip()
        
        # 提取评分
        rating_element = soup.find("strong", class_="ll rating_num")
        if rating_element:
            movie_info["rating"] = rating_element.text.strip()
 
        # 提取评分人数
        rating_count_element = soup.find("span", property="v:votes")
        if rating_count_element:
            movie_info["rating_count"] = rating_count_element.text.strip()
        
        # 提取年份 
        year_element = soup.find("span", class_="year")
        if year_element:
            movie_info["year"] = year_element.text.strip("()")

        # 提取导演
        directors = soup.find_all("a", rel="v:directedBy")
        if directors:
            movie_info["directors"] = [director.text.strip() for director in directors]
        else:            
            movie_info["directors"] = ["未知"]
        
        # 提取编剧
        scriptwriters = soup.find('span', string=re.compile('编剧'))
        if scriptwriters and scriptwriters.parent:
            scriptwriters = scriptwriters.parent.find_all('a')
            if scriptwriters:
                movie_info["scriptwriters"] = [writer.text.strip() for writer in scriptwriters]
            else:
                movie_info["scriptwriters"] = ["未知"]
        else:
            movie_info["scriptwriters"] = ["未知"]
        
        # 提取主演
        stars = soup.find_all("a", rel="v:starring")
        if stars:
            movie_info['stars'] = [star.text.strip() for star in stars]
        else:
            movie_info['stars'] = ['未知']
        
        # 提取电影类型
        genres = soup.find_all("span", property="v:genre")
        if genres:
            movie_info['genres'] = [genre.text.strip() for genre in genres]
        else:
            movie_info['genres'] = ['未知']
        
        # 提取制片国家/地区
        country_span = soup.find('span', string=re.compile('制片国家/地区:'))
        if country_span and country_span.next_sibling:
            movie_info["country"] = country_span.next_sibling.strip()
        else:
            movie_info["country"] = "未知"

        # 提取语言
        language = soup.find('span', string=re.compile('语言'))
        if language and language.next_sibling:
            movie_info["language"] = language.next_sibling.strip()
        else:
            movie_info["language"] = "未知"

        # 获取上映日期
        screening_dates = soup.find_all("span", property="v:initialReleaseDate")
        if genres:
            movie_info['screening_dates'] = [screening_date.text.strip() for screening_date in screening_dates]
        else:
            movie_info['screening_dates'] = ['未知']

        # 获取片长
        runtime = soup.find("span", property="v:runtime")
        if runtime:
            movie_info["runtime"] = runtime.text.strip("()")
        
        # 提取又名
        other_name = soup.find('span', string=re.compile('又名:'))
        if other_name and other_name.next_sibling:
            movie_info["other_name"] = other_name.next_sibling.strip().split(' / ')
        else:
            movie_info["other_name"] = ["未知"]

        # 提取IMDb
        IMDb = soup.find('span', string=re.compile('IMDb:'))
        if IMDb and IMDb.next_sibling:
            movie_info["IMDb"] = IMDb.next_sibling.strip()

        # 提取电影简介
        intro = soup.find("span", property="v:summary")
        if intro:
            movie_info["intro"] = intro.text.strip()

        # 提取电影ID并获取短评
        movie_id = extract_movie_id(movie_url)
        if movie_id:
            try:
                movie_info["short_comments"] = get_movie_comments(movie_id, 60)
            except Exception as e:
                print(f"获取短评失败: {e}")
                movie_info["short_comments"] = []
        else:
            movie_info["short_comments"] = []
        
        return movie_info
    
    except Exception as e:
        print(f"获取电影详情时发生错误: {e}")
        return {"name": "获取失败", "error": str(e), "short_comments": []}

def save_to_json(data, filename):
    """
    保存数据到 JSON 文件
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_to_sql():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password=PASSWORD
    )
    try:
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS douban_movies")

            cursor.execute("USE douban_movies")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies(
                id INT AUTO_INCREMENT PRIMARY KEY,
                no INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                rating DECIMAL(3,1) NOT NULL,
                rating_count INT NOT NULL,
                year INT NOT NULL,
                country VARCHAR(255),
                language VARCHAR(255),
                runtime VARCHAR(100),
                IMDb VARCHAR(20),
                intro TEXT,
                directors TEXT,
                scriptwriters TEXT,
                stars TEXT,
                genres TEXT,
                screening_dates TEXT,
                other_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments(
                id INT AUTO_INCREMENT PRIMARY KEY,
                movie_id INT NOT NULL,
                author VARCHAR(100),
                time DATETIME,
                content TEXT,
                rating VARCHAR(10),
                useful INT,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # 读取JSON数据
            with open(get_json_path(), 'r', encoding='utf-8') as f:
                movies_data = json.load(f)

            # 插入数据
            for movie in movies_data:
                no = int(movie['no'])
                rating = float(movie['rating'])
                rating_count = int(movie['rating_count'])
                year = int(movie['year'])
                directors = ','.join(movie['directors'])
                scriptwriters = ','.join(movie['scriptwriters'])
                stars = ','.join(movie['stars'])
                genres = ','.join(movie['genres'])
                screening_dates = ','.join(movie['screening_dates'])
                other_name = ','.join(movie['other_name'])

                cursor.execute(
                    "INSERT INTO movies (no, name, rating, rating_count, year, country, language, runtime, IMDb, intro, directors, scriptwriters, stars, genres, screening_dates, other_name)"
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (no, movie['name'], rating, rating_count, year, movie['country'], movie['language'], movie['runtime'], movie['IMDb'], movie['intro'], directors, scriptwriters, stars, genres, screening_dates, other_name)
                )

                for comment in movie['short_comments']:
                    useful = int(comment['useful'])
                    cursor.execute(
                        "INSERT INTO comments (movie_id, author, time, content, rating, useful)" 
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (no, comment['author'], comment['time'], comment['content'], comment['rating'], useful)
                    )
            connection.commit()

    except Exception as e:
        print(f'出错了: {e}')
        connection.rollback()
    finally:
        connection.close()

def main():
    all_movies = []
    try:
        # 获取所有电影链接
        print("正在获取电影链接...")
        movie_links = get_movie_links()
        print(f"共获取到 {len(movie_links)} 部电影链接")
        
        # 爬取每部电影的详细信息
        for idx, movie_url in enumerate(movie_links[MOVIE_RANGE[0] - 1 : MOVIE_RANGE[1]]):  # 只爬取前 MOVIE_NUMS 部电影
            print(f"正在爬取第 {idx + 1} 部电影")
            movie_details = get_movie_details(movie_url)
            all_movies.append(movie_details)
            time.sleep(random.uniform(1, 2))  # 随机延时，降低被封风险
        
        # 保存到 JSON 文件
        save_to_json(all_movies, json_path)
        print("爬取顺利完成  数据已保存到 douban_movies.json 文件中")
        save_to_sql()
        print('数据成功存储到 mysql 数据库中')
    
    except Exception as e:
        print(f"程序执行过程中出错: {e}")
        # 保存已经爬取的数据
        if all_movies:
            save_to_json(all_movies, json_path)
            print("已保存部分爬取的数据到 douban_movies.json 文件中")

if __name__ == "__main__":
    main()