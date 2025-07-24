#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微博头条文章爬虫
专门处理 https://weibo.com/ttarticle/x/m/show#/id=xxx 格式的微博专栏文章
"""

import requests
import json
import time
import re
from urllib.parse import  urlparse, parse_qs
import os
from datetime import datetime
from bs4 import BeautifulSoup
import argparse
from zhconv import convert

class WeiboTTArticleCrawler:
    def __init__(self, cookies_file=None, cookies_dict=None):
        self.debug_mode = False  # 调试模式开关
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://weibo.com/',
            'Origin': 'https://weibo.com'
        }
        
        # 设置Cookie
        if cookies_dict:
            # 如果提供了cookie字典，直接使用
            self.session.cookies.update(cookies_dict)
            print(f"已加载 {len(cookies_dict)} 个cookie")
        elif cookies_file and os.path.exists(cookies_file):
            # 如果提供了cookie文件，从文件加载
            self.load_cookies_from_file(cookies_file)
        else:
            # 使用默认的基础Cookie
            self.session.cookies.update({
                'SINAGLOBAL': '1234567890.123.1234567890123',
                'UOR': 'www.baidu.com,widget.weibo.com,www.baidu.com',
                'SUBP': 'mock_subp_value',
                'SUB': 'mock_sub_value',
                '_s_tentry': 'weibo.com',
                'Apache': 'mock_apache_value',
                'ULV': '1234567890123:1:1:1:1234567890.123.1234567890123:1234567890123'
            })
            print("使用默认基础Cookie（可能无法访问需要登录的内容）")
        
        self.session.headers.update(self.headers)
    
    def load_cookies_from_file(self, cookies_file):
        """从文件加载Cookie"""
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if content.startswith('{'):
                # JSON格式
                cookies_dict = json.loads(content)
                self.session.cookies.update(cookies_dict)
                print(f"从JSON文件加载了 {len(cookies_dict)} 个cookie")
            else:
                # 浏览器导出的cookie字符串格式
                cookies_dict = self.parse_cookie_string(content)
                self.session.cookies.update(cookies_dict)
                print(f"从cookie字符串加载了 {len(cookies_dict)} 个cookie")
                
        except Exception as e:
            print(f"加载cookie文件失败: {e}")
            print("将使用默认基础Cookie")
    
    def parse_cookie_string(self, cookie_string):
        """解析浏览器导出的cookie字符串"""
        cookies_dict = {}
        try:
            # 处理多种格式的cookie字符串
            if ';' in cookie_string:
                # 格式: name1=value1; name2=value2
                pairs = cookie_string.split(';')
                for pair in pairs:
                    if '=' in pair:
                        name, value = pair.strip().split('=', 1)
                        cookies_dict[name.strip()] = value.strip()
            elif '\n' in cookie_string:
                # 每行一个cookie的格式
                lines = cookie_string.strip().split('\n')
                for line in lines:
                    if '=' in line:
                        name, value = line.strip().split('=', 1)
                        cookies_dict[name.strip()] = value.strip()
        except Exception as e:
            print(f"解析cookie字符串失败: {e}")
        
        return cookies_dict
    
    def save_cookies_to_file(self, filename):
        """保存当前session的cookie到文件"""
        try:
            cookies_dict = dict(self.session.cookies)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cookies_dict, f, ensure_ascii=False, indent=2)
            print(f"Cookie已保存到: {filename}")
        except Exception as e:
            print(f"保存cookie失败: {e}")
    
    def set_cookies_from_browser_export(self, cookie_string):
        """从浏览器导出的cookie字符串设置cookie"""
        cookies_dict = self.parse_cookie_string(cookie_string)
        self.session.cookies.update(cookies_dict)
        print(f"已更新 {len(cookies_dict)} 个cookie")
        return len(cookies_dict) > 0
        
    def extract_article_id_from_url(self, url):
        """从URL中提取文章ID"""
        try:
            print(f"正在分析URL: {url}")
            
            # 处理hash fragment中的参数
            if '#/' in url:
                fragment_part = url.split('#/')[-1]
                print(f"Fragment部分: {fragment_part}")
                
                # 解析fragment中的参数
                if 'id=' in fragment_part:
                    id_match = re.search(r'id=([^&]+)', fragment_part)
                    if id_match:
                        article_id = id_match.group(1)
                        print(f"提取到文章ID: {article_id}")
                        return article_id
            
            # 尝试从查询参数中提取
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'id' in query_params:
                article_id = query_params['id'][0]
                print(f"从查询参数中提取到文章ID: {article_id}")
                return article_id
                
            print("未能从URL中提取到文章ID")
            return None
        except Exception as e:
            print(f"提取文章ID失败: {e}")
            return None
    
    def get_article_content(self, article_id):
        """获取文章内容"""
        try:
            print(f"正在获取文章内容: {article_id}")
            
            # 尝试多种API接口，优先使用移动端接口
            api_urls = [
                f"https://weibo.com/ttarticle/x/m/aj/detail?id={article_id}",
                f"https://m.weibo.cn/statuses/extend?id={article_id}",
                f"https://weibo.com/ajax/statuses/longtext?id={article_id}",
                f"https://card.weibo.com/article/m/show/id/{article_id}",
                f"https://weibo.com/ttarticle/p/show?id={article_id}",
                f"https://weibo.com/ajax/statuses/show?id={article_id}"
            ]
            
            for i, api_url in enumerate(api_urls, 1):
                try:
                    print(f"尝试API {i}: {api_url}")
                    
                    # 为不同的API使用不同的请求头
                    headers = self.headers.copy()
                    if 'm.weibo.cn' in api_url:
                        headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
                        headers['Referer'] = 'https://m.weibo.cn/'
                    elif 'ajax' in api_url or 'aj/detail' in api_url:
                        headers['X-Requested-With'] = 'XMLHttpRequest'
                        headers['Referer'] = f'https://weibo.com/ttarticle/p/show?id={article_id}'
                        headers['Accept'] = 'application/json, text/plain, */*'
                    
                    response = self.session.get(api_url, headers=headers, timeout=15)
                    print(f"响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        # 检查是否需要登录
                        if '请登录' in response.text or 'login' in response.text.lower() or '微博不存在或暂无查看权限' in response.text:
                            print(f"API {i} 需要登录或无权限，跳过")
                            continue
                            
                        # 只在调试模式下保存调试信息
                        if self.debug_mode:
                            debug_filename = f"article_debug_{i}_{article_id}.html"
                            with open(debug_filename, 'w', encoding='utf-8') as f:
                                f.write(f"<!-- API URL: {api_url} -->\n")
                                f.write(f"<!-- Status Code: {response.status_code} -->\n")
                                f.write(f"<!-- Response Headers: {dict(response.headers)} -->\n")
                                f.write(f"<!-- Response Content Length: {len(response.text)} -->\n")
                                f.write(f"<!-- Response Content Type: {response.headers.get('Content-Type', 'unknown')} -->\n")
                                f.write(response.text)
                            print(f"调试信息已保存到: {debug_filename}")
                        print(f"响应内容长度: {len(response.text)}")
                        print(f"响应内容前200字符: {response.text[:200]}")
                        
                        # 如果是JSON响应，在调试模式下保存调试文件
                        if 'application/json' in response.headers.get('Content-Type', '') or response.text.strip().startswith('{'):
                            try:
                                import json
                                json_data = json.loads(response.text)
                                
                                if self.debug_mode:
                                    json_debug_filename = f"article_debug_{i}_{article_id}.json"
                                    with open(json_debug_filename, 'w', encoding='utf-8') as f:
                                        json.dump({
                                            'api_url': api_url,
                                            'status_code': response.status_code,
                                            'headers': dict(response.headers),
                                            'response_data': json_data
                                        }, f, ensure_ascii=False, indent=2)
                                    print(f"JSON调试信息已保存到: {json_debug_filename}")
                                
                                # 打印JSON结构信息
                                if isinstance(json_data, dict):
                                    print(f"JSON根级键: {list(json_data.keys())}")
                                    if 'data' in json_data:
                                        data_keys = list(json_data['data'].keys()) if isinstance(json_data['data'], dict) else 'not dict'
                                        print(f"data字段键: {data_keys}")
                                        # 查找可能的下一章信息
                                        if isinstance(json_data['data'], dict):
                                            next_keys = [k for k in json_data['data'].keys() if 'next' in k.lower() or 'series' in k.lower() or 'chapter' in k.lower()]
                                            if next_keys:
                                                print(f"可能包含下一章信息的键: {next_keys}")
                                                for key in next_keys:
                                                    print(f"  {key}: {json_data['data'][key]}")
                            except json.JSONDecodeError:
                                print("响应不是有效的JSON格式")
                        
                        # 解析内容
                        article_data = self.parse_article_content(response.text, api_url)
                        if article_data and (article_data.get('content') or article_data.get('title')):
                            return article_data
                            
                except Exception as e:
                    print(f"API {i} 请求失败: {e}")
                    # 出错时保存调试信息
                    if hasattr(self, 'debug_mode') and self.debug_mode:
                        try:
                            error_debug_filename = f"article_error_{i}_{article_id}.txt"
                            with open(error_debug_filename, 'w', encoding='utf-8') as f:
                                f.write(f"API URL: {api_url}\n")
                                f.write(f"Error: {str(e)}\n")
                                f.write(f"Exception Type: {type(e).__name__}\n")
                            print(f"错误调试信息已保存到: {error_debug_filename}")
                        except:
                            pass
                    continue
                
                # 在每次请求之间添加延时
                time.sleep(1)
            
            return None
        except Exception as e:
            print(f"获取文章内容失败: {e}")
            return None
    
    def add_pangu_spacing(self, text):
        """添加盘古之白：在中文字符和英文字母/数字之间添加空格"""
        if not text:
            return text
        
        # 在中文字符和英文字母/数字之间添加空格
        # 中文字符后跟英文字母/数字
        text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9])', r'\1 \2', text)
        # 英文字母/数字后跟中文字符
        text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fff])', r'\1 \2', text)
        
        # 在中文字符和英文标点之间添加空格（可选）
        text = re.sub(r'([\u4e00-\u9fff])([!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~])', r'\1 \2', text)
        text = re.sub(r'([!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~])([\u4e00-\u9fff])', r'\1 \2', text)
        
        # 清理多余的空格，但保留换行符
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text
    
    def clean_invisible_characters(self, text):
        """清理文本中的不可见字符和特殊空白符"""
        if not text:
            return text
        
        # 定义需要清理的不可见字符
        invisible_chars = {
            '\u00A0': ' ',  # 不间断空格 (Non-breaking Space) -> 普通空格
            '\u200B': '',   # 零宽空格 (Zero-width space) -> 删除
            '\u200C': '',   # 零宽非连字符 (Zero-width non-joiner) -> 删除
            '\u200D': '',   # 零宽连字符 (Zero-width joiner) -> 删除
            '\u2060': '',   # 词连接符 (Word joiner) -> 删除
            '\uFEFF': '',   # 零宽非断空格 (Zero-width no-break space) -> 删除
            '\u180E': '',   # 蒙古文元音分隔符 (Mongolian vowel separator) -> 删除
            '\u2000': ' ',  # En quad -> 普通空格
            '\u2001': ' ',  # Em quad -> 普通空格
            '\u2002': ' ',  # En space -> 普通空格
            '\u2003': ' ',  # Em space -> 普通空格
            '\u2004': ' ',  # Three-per-em space -> 普通空格
            '\u2005': ' ',  # Four-per-em space -> 普通空格
            '\u2006': ' ',  # Six-per-em space -> 普通空格
            '\u2007': ' ',  # Figure space -> 普通空格
            '\u2008': ' ',  # Punctuation space -> 普通空格
            '\u2009': ' ',  # Thin space -> 普通空格
            '\u200A': ' ',  # Hair space -> 普通空格
            '\u202F': ' ',  # Narrow no-break space -> 普通空格
            '\u205F': ' ',  # Medium mathematical space -> 普通空格
            '\u3000': ' ',  # 全角空格 -> 普通空格
        }
        
        # 替换不可见字符
        for invisible_char, replacement in invisible_chars.items():
            text = text.replace(invisible_char, replacement)
        
        return text
    
    def convert_to_simplified_fullwidth(self, text):
        """将繁体中文转换为简体中文，并将半角标点转换为全角标点"""
        if not text:
            return text
        
        # 0. 首先清理不可见字符
        text = self.clean_invisible_characters(text)
        
        # 1. 繁体转简体（如果zhconv可用）
        if convert is not None:
            try:
                text = convert(text, 'zh-cn')
            except Exception as e:
                print(f"繁体转简体失败: {e}")
        
        # 2. 半角到全角标点符号映射（不包括引号）
        half_to_full_map_base = {
            '!': '！', '(': '（', ')': '）', ',': '，', ':': '：', ';': '；', '?': '？', '[': '【', ']': '】'
        }
        
        # 3. 智能处理双引号和单引号
        in_double_quote = False
        in_single_quote = False
        processed_content_with_quotes = []
        
        for char in text:
            if char == '"':
                if not in_double_quote:
                    processed_content_with_quotes.append('"')
                    in_double_quote = True
                else:
                    processed_content_with_quotes.append('"')
                    in_double_quote = False
            elif char == "'":
                if not in_single_quote:
                    processed_content_with_quotes.append(''')
                    in_single_quote = True
                else:
                    processed_content_with_quotes.append(''')
                    in_single_quote = False
            else:
                processed_content_with_quotes.append(char)
        
        # 转换回字符串
        content_after_quotes = "".join(processed_content_with_quotes)
        
        # 4. 转换其他半角符号为全角（不包括已处理的引号）
        final_fullwidth_content = []
        for char in content_after_quotes:
            final_fullwidth_content.append(half_to_full_map_base.get(char, char))
        
        return "".join(final_fullwidth_content)
    
    def extract_formatted_text(self, element):
        """提取保留换行格式的文本内容"""
        if not element:
            return ''
        
        # 处理段落标签，保留换行
        for p in element.find_all('p'):
            p.append('\n\n')
        
        # 处理换行标签
        for br in element.find_all('br'):
            br.replace_with('\n')
        
        # 处理div标签，在末尾添加换行
        for div in element.find_all('div'):
            div.append('\n')
        
        # 获取文本并清理多余的空行
        text = element.get_text()
        # 将多个连续的换行符替换为最多两个
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 应用盘古之白格式化
        text = self.add_pangu_spacing(text)
        
        return text.strip()
    
    def find_next_chapter_url(self, soup):
        """查找下一章的URL"""
        # 查找下一篇文章的链接
        next_selectors = [
            'a[href*="ttarticle"][title*="下一篇"]',
            'a[href*="ttarticle"]:contains("下一篇")',
            'a[href*="ttarticle"]:contains("下一章")',
            '.special-button a[href*="ttarticle"]',
            'a[href*="show?id="]:contains("下")',
        ]
        
        for selector in next_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link and next_link.get('href'):
                    href = next_link.get('href')
                    # 确保是完整的URL
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return f"https://weibo.com{href}"
                    else:
                        return f"https://weibo.com/ttarticle/p/{href}"
            except:
                continue
        
        # 如果没有找到，尝试通过文本查找
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text(strip=True)
            if any(keyword in link_text for keyword in ['下一篇', '下一章', '下一页']):
                href = link.get('href')
                if 'ttarticle' in href or 'show?id=' in href:
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return f"https://weibo.com{href}"
        
        return None
    
    def parse_article_content(self, html_content, source_url):
        """解析文章内容"""
        try:
            article_data = {
                'source_url': source_url,
                'title': '',
                'content': '',
                'author': '',
                'publish_time': '',
                'next_chapter_url': None,
                'raw_html': html_content[:1000] + '...' if len(html_content) > 1000 else html_content
            }
            
            # 尝试解析JSON响应
            try:
                json_data = json.loads(html_content)
                print(f"成功解析JSON，数据键: {list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}")
                
                if isinstance(json_data, dict):
                    # 处理微博头条文章API响应
                    if json_data.get('code') == '100000' and 'data' in json_data:
                        data = json_data['data']
                        
                        # 提取标题（需要解码Unicode）
                        title = data.get('title', '')
                        if title:
                            try:
                                # 解码Unicode编码的标题
                                if r'\u' in title:
                                    title = title.encode('utf-8').decode('unicode_escape')
                            except Exception as e:
                                print(f"标题解码失败: {e}")
                        article_data['title'] = title
                        
                        # 提取作者信息
                        if 'uid' in data:
                            article_data['author_uid'] = str(data['uid'])
                        
                        # 尝试从多个字段提取作者名称
                        author_name = ''
                        if 'author' in data:
                            author_name = data['author']
                        elif 'author_name' in data:
                            author_name = data['author_name']
                        elif 'user_name' in data:
                            author_name = data['user_name']
                        elif 'screen_name' in data:
                            author_name = data['screen_name']
                        elif 'nickname' in data:
                            author_name = data['nickname']
                        
                        if author_name:
                            # 处理Unicode编码的作者名称
                            try:
                                if r'\u' in str(author_name):
                                    author_name = str(author_name).encode('utf-8').decode('unicode_escape')
                            except Exception as e:
                                print(f"作者名称解码失败: {e}")
                            article_data['author'] = str(author_name)
                            print(f"提取到作者: {author_name}")
                        else:
                            print(f"未找到作者信息，数据键: {list(data.keys())}")
                        
                        # 提取发布时间
                        article_data['publish_time'] = data.get('create_at', data.get('complete_create_at', ''))
                        
                        # 尝试获取文章详细内容
                        if 'content' in data:
                            content = data['content']
                            if content:
                                # 处理Unicode编码的内容
                                try:
                                    if r'\u' in content:
                                        content = content.encode('utf-8').decode('unicode_escape')
                                except Exception as e:
                                    print(f"内容解码失败: {e}")
                                content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                                content = re.sub(r'<[^>]+>', '', content)
                                article_data['content'] = content
                        
                        # 如果没有content字段，尝试获取完整内容
                        if not article_data.get('content'):
                            # 尝试从summary获取部分内容
                            summary = data.get('summary', '')
                            if summary:
                                article_data['content'] = summary
                            
                            # 尝试通过文章URL获取完整内容
                            article_url = data.get('url', '')
                            if article_url:
                                print(f"尝试获取完整文章内容: {article_url}")
                                try:
                                    full_response = self.session.get(article_url, headers=self.headers, timeout=10)
                                    if full_response.status_code == 200:
                                        full_content = self.parse_article_content(full_response.text, article_url)
                                        if full_content and full_content.get('content'):
                                            article_data['content'] = full_content['content']
                                            # 也更新下一章链接
                                            if full_content.get('next_chapter_url'):
                                                article_data['next_chapter_url'] = full_content['next_chapter_url']
                                except Exception as e:
                                    print(f"获取完整内容失败: {e}")
                        
                        # 查找下一章链接 - 从JSON数据中查找
                        if 'sibling' in data and data['sibling'] and 'next' in data['sibling'] and data['sibling']['next']:
                            next_info = data['sibling']['next']
                            # 优先使用url字段，这是正确的页面链接格式
                            if 'url' in next_info:
                                article_data['next_chapter_url'] = next_info['url']
                                print(f"从sibling字段找到下一章链接: {next_info['url']}")
                            # 如果没有url字段，尝试使用id构建链接
                            elif 'id' in next_info:
                                next_id = next_info['id']
                                article_data['next_chapter_url'] = f"https://weibo.com/ttarticle/p/show?id={next_id}"
                                print(f"使用ID构建下一章链接: {article_data['next_chapter_url']}")
                            
                            if 'title' in next_info:
                                next_title = next_info['title']
                                # 处理Unicode编码的标题
                                if r'\u' in next_title:
                                    try:
                                        next_title = next_title.encode().decode('unicode_escape')
                                    except Exception as e:
                                        print(f"下一章标题解码失败: {e}")
                                print(f"下一章标题: {next_title}")
                        elif 'next_article_id' in data:
                            next_id = data['next_article_id']
                            article_data['next_chapter_url'] = f"https://weibo.com/ttarticle/p/show?id={next_id}"
                        elif 'series_info' in data and data['series_info']:
                            series_info = data['series_info']
                            if 'next_id' in series_info:
                                next_id = series_info['next_id']
                                article_data['next_chapter_url'] = f"https://weibo.com/ttarticle/p/show?id={next_id}"
                        
                        return article_data
                    
                    # 处理其他JSON结构
                    elif 'data' in json_data:
                        data = json_data['data']
                        article_data['title'] = data.get('title', '')
                        # 保留换行格式
                        content = data.get('longTextContent', data.get('text', ''))
                        if content:
                            content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                            content = re.sub(r'<[^>]+>', '', content)  # 清理其他HTML标签
                            article_data['content'] = content
                        if 'user' in data:
                            article_data['author'] = data['user'].get('screen_name', '')
                        article_data['publish_time'] = data.get('created_at', '')
                    
                    elif 'ok' in json_data and json_data['ok'] == 1:
                        # 微博API成功响应
                        if 'data' in json_data:
                            data = json_data['data']
                            content = data.get('longTextContent', data.get('text', ''))
                            if content:
                                content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                                content = re.sub(r'<[^>]+>', '', content)
                                article_data['content'] = content
                            
                            # 提取作者信息
                            if 'user' in data:
                                user_info = data['user']
                                if isinstance(user_info, dict):
                                    author_name = user_info.get('screen_name', user_info.get('name', ''))
                                    if author_name:
                                        article_data['author'] = author_name
                                        print(f"从user字段提取到作者: {author_name}")
                                    if 'id' in user_info:
                                        article_data['author_uid'] = str(user_info['id'])
                            elif 'author' in data:
                                article_data['author'] = data['author']
                            elif 'screen_name' in data:
                                article_data['author'] = data['screen_name']
                            
                            # 提取发布时间
                            if 'created_at' in data:
                                article_data['publish_time'] = data['created_at']
                    
                    # 如果找到了内容，返回
                    if article_data.get('content') or article_data.get('title'):
                        return article_data
            
            except json.JSONDecodeError:
                # 不是JSON，尝试解析HTML
                pass
            
            # 解析HTML内容
            # 检查HTML是否指定了编码
            encoding = 'utf-8'  # 默认编码
            if 'charset=' in html_content.lower():
                charset_match = re.search(r'charset=["\']?([^"\'>\s]+)', html_content, re.IGNORECASE)
                if charset_match:
                    detected_encoding = charset_match.group(1).lower()
                    if detected_encoding in ['gbk', 'gb2312', 'gb18030']:
                        encoding = detected_encoding
                        print(f"检测到HTML编码: {encoding}")
                        # 如果是GBK编码，需要重新解码
                        try:
                            if isinstance(html_content, str):
                                # 先编码为bytes再用正确编码解码
                                html_content = html_content.encode('latin1').decode(encoding)
                                print("已重新解码HTML内容")
                        except Exception as e:
                            print(f"重新解码失败: {e}，使用原始内容")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找标题
            title_selectors = [
                'title',
                'h1.title',
                '.WB_detail .title',
                '.article-title',
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    title_text = title_elem.get_text(strip=True)
                    # 清理标题中的网站名称
                    if '微博' in title_text:
                        title_text = title_text.split('微博')[0].strip()
                    article_data['title'] = title_text
                    print(f"从HTML提取标题: {title_text}")
                    break
            
            # 查找作者信息
            author_selectors = [
                '.WB_detail .author',
                '.author-name',
                '.username',
                '.user-name',
                '.screen-name',
                '.nickname',
                '.WB_detail .WB_cardwrap .WB_info .W_f14',
                '.WB_info .W_f14',
                '.author',
                '.user',
                '[class*="author"]',
                '[class*="user"]',
                '[data-author]',
                'a[href*="/u/"]',
                'a[href*="weibo.com/"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem and author_elem.get_text(strip=True):
                    author_text = author_elem.get_text(strip=True)
                    # 清理作者名称中的多余信息
                    author_text = author_text.split('\n')[0].strip()  # 取第一行
                    author_text = re.sub(r'\s+', ' ', author_text)  # 合并多个空格
                    if len(author_text) > 0 and len(author_text) < 50:  # 合理的作者名称长度
                        article_data['author'] = author_text
                        print(f"通过选择器 {selector} 找到作者: {author_text}")
                        
                        # 尝试从链接中提取UID
                        author_link = author_elem.find('a') if author_elem.name != 'a' else author_elem
                        if author_link and author_link.get('href'):
                            href = author_link.get('href')
                            uid_match = re.search(r'/(?:u/)?([0-9]+)', href)
                            if uid_match:
                                article_data['author_uid'] = uid_match.group(1)
                                print(f"提取到作者UID: {uid_match.group(1)}")
                        break
            
            # 如果还没找到作者，尝试从data属性中提取
            if not article_data.get('author'):
                author_data_elem = soup.find(attrs={'data-author': True})
                if author_data_elem:
                    author_name = author_data_elem.get('data-author')
                    if author_name:
                        article_data['author'] = author_name
                        print(f"从data-author属性找到作者: {author_name}")
            
            # 查找发布时间
            time_selectors = [
                '.WB_detail .time',
                '.publish-time',
                '.created-time',
                '[class*="time"]'
            ]
            
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem and time_elem.get_text(strip=True):
                    article_data['publish_time'] = time_elem.get_text(strip=True)
                    break
            
            # 查找文章内容 - 使用更精确的选择器
            content_selectors = [
                '.WB_editor_iframe_new[node-type="contentBody"]',
                '.WB_detail .WB_text',
                '.article-content',
                '.content-body',
                '[class*="content"][class*="body"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = self.extract_formatted_text(content_elem)
                    if len(content_text) > 50:
                        article_data['content'] = content_text
                        print(f"通过选择器 {selector} 找到内容，长度: {len(content_text)}")
                        break
            
            # 查找下一章链接
            next_url = self.find_next_chapter_url(soup)
            if next_url:
                article_data['next_chapter_url'] = next_url
                print(f"找到下一章链接: {next_url}")
            
            # 如果没有从作者链接找到UID，尝试从页面其他地方提取
            if 'author_uid' not in article_data:
                uid_patterns = [
                    r'"uid"\s*:\s*"?([0-9]+)"?',
                    r'uid=([0-9]+)',
                    r'user_id["\']?\s*:\s*["\']?([0-9]+)',
                ]
                
                for pattern in uid_patterns:
                    match = re.search(pattern, html_content)
                    if match:
                        article_data['author_uid'] = match.group(1)
                        print(f"从页面内容提取到UID: {match.group(1)}")
                        break
            
            # 如果还没有作者信息，尝试从页面内容中提取作者名称
            if not article_data.get('author'):
                author_patterns = [
                    r'"author"\s*:\s*"([^"]+)"',
                    r'"screen_name"\s*:\s*"([^"]+)"',
                    r'"user_name"\s*:\s*"([^"]+)"',
                    r'"nickname"\s*:\s*"([^"]+)"',
                    r'"author_name"\s*:\s*"([^"]+)"',
                ]
                
                for pattern in author_patterns:
                    match = re.search(pattern, html_content)
                    if match:
                        author_name = match.group(1)
                        # 处理Unicode编码
                        try:
                            if r'\u' in author_name:
                                author_name = author_name.encode('utf-8').decode('unicode_escape')
                        except Exception as e:
                            print(f"作者名称解码失败: {e}")
                        article_data['author'] = author_name
                        print(f"从页面内容提取到作者: {author_name}")
                        break
            
            # 从script标签中查找JSON数据
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.get_text()
                if 'longTextContent' in script_content:
                    json_matches = re.findall(r'\{[^{}]*"longTextContent"[^{}]*\}', script_content)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'longTextContent' in data:
                                # 保留换行格式
                                content = data['longTextContent'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                                # 清理HTML标签但保留换行
                                content = re.sub(r'<[^>]+>', '', content)
                                article_data['content'] = content
                                break
                        except:
                            continue
            
            # 如果找到了有效内容，返回
            if article_data['content'] or article_data['title']:
                return article_data
            
            return None
        except Exception as e:
            print(f"解析文章内容失败: {e}")
            return None
    
    def get_author_articles(self, article_data):
        """获取作者的其他文章"""
        try:
            print("正在尝试获取作者的其他文章...")
            
            # 从article_data中提取作者信息
            author_name = article_data.get('author', '')
            author_uid = article_data.get('author_uid', '')
            
            if not author_name:
                print("未找到作者信息，无法获取其他文章")
                return []
            
            # 清理作者名称，提取实际用户名
            clean_author = author_name.split()[0] if author_name else ''
            print(f"正在获取作者 {clean_author} 的其他文章...")
            
            articles = []
            
            # 如果有作者UID，尝试直接获取用户的文章
            if author_uid:
                uid_urls = [
                    f"https://weibo.com/ajax/statuses/mymblog?uid={author_uid}&page=1&feature=0",
                    f"https://m.weibo.cn/api/container/getIndex?containerid=107603{author_uid}",
                    f"https://weibo.com/ttarticle/api/profile/articles?uid={author_uid}&page_size=20&page=1"
                ]
                
                for i, url in enumerate(uid_urls, 1):
                    try:
                        print(f"尝试UID API {i}: {url}")
                        response = self.session.get(url, headers=self.headers, timeout=10)
                        
                        if response.status_code == 200:
                            # 只在调试模式下保存调试文件
                            if self.debug_mode:
                                debug_filename = f"author_uid_articles_debug_{i}.txt"
                                with open(debug_filename, 'w', encoding='utf-8') as f:
                                    f.write(f"<!-- API URL: {url} -->\n")
                                    f.write(f"<!-- Status Code: {response.status_code} -->\n")
                                    f.write(f"<!-- Response Headers: {dict(response.headers)} -->\n")
                                    f.write(response.text)
                                print(f"UID API响应已保存到: {debug_filename}")
                            print(f"UID API响应长度: {len(response.text)}")
                            
                            try:
                                data = response.json()
                                parsed_articles = self.parse_articles_from_response(data, f"UID-{i}")
                                if parsed_articles:
                                    articles.extend(parsed_articles)
                                    print(f"通过UID API {i} 找到 {len(parsed_articles)} 篇文章")
                                    break
                            except json.JSONDecodeError:
                                print(f"UID API {i} 返回的不是有效的JSON格式")
                                continue
                        else:
                            print(f"UID API {i} 请求失败，状态码: {response.status_code}")
                            
                    except Exception as e:
                        print(f"UID API {i} 请求出错: {str(e)}")
                        continue
            
            # 如果通过UID没有找到文章，尝试搜索API
            if not articles:
                search_urls = [
                    f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{clean_author}",
                    f"https://weibo.com/ajax/search/searchall?q={clean_author}&xsort=time",
                    f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D60%26q%3D{clean_author}"
                ]
                
                for i, url in enumerate(search_urls, 1):
                    try:
                        print(f"尝试搜索API {i}: {url}")
                        response = self.session.get(url, headers=self.headers, timeout=10)
                        
                        if response.status_code == 200:
                            # 只在调试模式下保存调试文件
                            if self.debug_mode:
                                debug_filename = f"author_search_articles_debug_{i}.txt"
                                with open(debug_filename, 'w', encoding='utf-8') as f:
                                    f.write(f"<!-- API URL: {url} -->\n")
                                    f.write(f"<!-- Status Code: {response.status_code} -->\n")
                                    f.write(f"<!-- Response Headers: {dict(response.headers)} -->\n")
                                    f.write(response.text)
                                print(f"搜索API响应已保存到: {debug_filename}")
                            print(f"搜索API响应长度: {len(response.text)}")
                            
                            try:
                                data = response.json()
                                parsed_articles = self.parse_articles_from_response(data, f"Search-{i}")
                                if parsed_articles:
                                    articles.extend(parsed_articles)
                                    print(f"通过搜索API {i} 找到 {len(parsed_articles)} 篇文章")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"搜索API {i} JSON解析失败: {e}")
                                print(f"响应内容前200字符: {response.text[:200]}")
                                continue
                                
                        else:
                            print(f"搜索API {i} 请求失败，状态码: {response.status_code}")
                            
                    except Exception as e:
                        print(f"搜索API {i} 请求异常: {e}")
                        continue
            
            if not articles:
                print("未能获取到作者的其他文章")
                
            return articles
            
        except Exception as e:
            print(f"获取作者其他文章失败: {e}")
            return []
    
    def parse_articles_from_response(self, data, api_type):
        """从API响应中解析文章列表"""
        articles = []
        
        try:
            # 处理不同API的响应格式
            if data.get('ok') == 1 and 'data' in data:
                # 移动端API格式
                if 'cards' in data['data']:
                    for card in data['data']['cards']:
                        if 'mblog' in card:
                            mblog = card['mblog']
                            # 检查是否是文章类型
                            if 'page_info' in mblog and mblog['page_info'].get('type') == 'article':
                                article = {
                                    'title': mblog['page_info'].get('page_title', ''),
                                    'url': mblog['page_info'].get('page_url', ''),
                                    'created_at': mblog.get('created_at', ''),
                                    'summary': mblog.get('text', '').replace('<br />', '\n')
                                }
                                articles.append(article)
                            else:
                                # 普通微博
                                article = {
                                    'title': mblog.get('text', '').replace('<br />', '\n')[:100] + '...',
                                    'url': f"https://m.weibo.cn/status/{mblog.get('bid', '')}",
                                    'created_at': mblog.get('created_at', ''),
                                    'reposts_count': mblog.get('reposts_count', 0),
                                    'comments_count': mblog.get('comments_count', 0)
                                }
                                articles.append(article)
                elif 'list' in data['data']:
                    for item in data['data']['list']:
                        if 'page_info' in item and item['page_info'].get('type') == 'article':
                            article = {
                                'title': item['page_info'].get('page_title', ''),
                                'url': item['page_info'].get('page_url', ''),
                                'created_at': item.get('created_at', ''),
                                'summary': item.get('text_raw', item.get('text', ''))
                            }
                            articles.append(article)
            
            elif 'data' in data and isinstance(data['data'], dict):
                # 桌面端API格式
                if 'list' in data['data']:
                    for item in data['data']['list']:
                        if 'text' in item:
                            article = {
                                'title': item.get('text', '').replace('<br />', '\n')[:100] + '...',
                                'url': f"https://weibo.com/status/{item.get('id', '')}",
                                'created_at': item.get('created_at', ''),
                                'reposts_count': item.get('reposts_count', 0),
                                'comments_count': item.get('comments_count', 0)
                            }
                            articles.append(article)
                
                # 头条文章API格式
                elif 'articles' in data['data']:
                    for article_data in data['data']['articles']:
                        article = {
                            'title': article_data.get('title', ''),
                            'url': f"https://weibo.com/ttarticle/p/show?id={article_data.get('id', '')}",
                            'created_at': article_data.get('create_time', ''),
                            'read_count': article_data.get('read_count', 0),
                            'summary': article_data.get('summary', '')
                        }
                        articles.append(article)
                        
        except Exception as e:
            print(f"解析{api_type}响应时出错: {str(e)}")
        
        return articles
    
    def save_results_with_chapters(self, all_chapters, other_articles=[]):
        """保存包含章节的爬取结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存JSON格式
            json_filename = f"ttarticle_chapters_{timestamp}.json"
            result_data = {
                'all_chapters': all_chapters,
                'other_articles': other_articles,
                'crawl_time': datetime.now().isoformat(),
                'total_chapters': len(all_chapters),
                'total_other_articles': len(other_articles)
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {json_filename}")
            
            # 保存markdown格式
            md_filename = f"ttarticle_chapters_{timestamp}.md"
            
            # 先组装所有内容为完整文本
            full_content = []
            
            if all_chapters:
                # 组装所有章节内容
                for i, chapter in enumerate(all_chapters):
                    title = chapter.get('title', '未知')
                    full_content.append(f"## {title}\n\n")
                    
                    content = chapter.get('content', '无内容')
                    # content中多行换行改成只空一行，没空行也换成空一行
                    import re
                    # 将多个连续换行符替换为双个换行符（一个空行）
                    formatted_content = re.sub(r'\n\s*\n+', '\n\n', content)
                    # 将单个换行符也替换为双个换行符（确保段落间有空行）
                    formatted_content = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', formatted_content)
                    full_content.append(f"{formatted_content}\n\n")
            
            if other_articles:
                for i, article in enumerate(other_articles, 1):
                    title = article.get('title', '未知')
                    full_content.append(f"## {title}\n")
                    
                    article_url = article.get('url', '无链接')
                    full_content.append(f"{article_url}\n")
                    
                    content = article.get('content', '无内容')[:200] + '...'
                    import re
                    formatted_content = re.sub(r'\n\s*\n+', '\n', content)
                    full_content.append(f"{formatted_content}\n\n")
            
            # 将所有内容合并为一个字符串
            final_text = ''.join(full_content)
            
            # 统一进行盘古之白格式化处理
            final_formatted_text = self.add_pangu_spacing(final_text)
            
            # 应用繁体转简体和标点符号转换
            final_converted_text = self.convert_to_simplified_fullwidth(final_formatted_text)
            
            # 写入文件
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(final_converted_text)
            
            print(f"Markdown格式结果已保存到: {md_filename}")
            return json_filename, md_filename
        except Exception as e:
            print(f"保存结果失败: {e}")
            return None, None
    
    def save_results(self, article_data, other_articles=[]):
        """保存爬取结果（兼容旧版本）"""
        return self.save_results_with_chapters([article_data], other_articles)
    
    def crawl_all_chapters(self, start_url, max_chapters=50):
        """连续爬取专栏的所有章节"""
        all_chapters = []
        current_url = start_url
        chapter_count = 0
        
        while current_url and chapter_count < max_chapters:
            try:
                print(f"\n正在爬取第 {chapter_count + 1} 章: {current_url}")
                
                # 提取文章ID
                article_id = self.extract_article_id_from_url(current_url)
                if not article_id:
                    print("无法提取文章ID，停止爬取")
                    break
                
                # 获取文章内容
                article_data = self.get_article_content(article_id)
                if not article_data:
                    print("无法获取文章内容，停止爬取")
                    break
                
                # 检查是否获取到有效内容
                if not article_data.get('content') and not article_data.get('title'):
                    print(f"第 {chapter_count + 1} 章没有有效内容，可能需要登录或被限制访问")
                    break
                
                # 添加章节编号
                article_data['chapter_number'] = chapter_count + 1
                all_chapters.append(article_data)
                
                print(f"成功获取第 {chapter_count + 1} 章: {article_data.get('title', '无标题')}")
                
                # 查找下一章链接
                next_url = article_data.get('next_chapter_url')
                if next_url:
                    print(f"找到下一章链接: {next_url}")
                    current_url = next_url
                    chapter_count += 1
                    time.sleep(3)  # 添加更长的延迟避免被限制
                else:
                    print("未找到下一章链接，爬取完成")
                    break
                    
            except Exception as e:
                print(f"爬取第 {chapter_count + 1} 章时出错: {e}")
                break
        
        return all_chapters
    
    def crawl_article(self, url, max_chapters=50):
        """爬取指定URL的文章及其后续章节"""
        try:
            print(f"开始爬取微博头条文章: {url}")
            
            # 爬取所有章节
            all_chapters = self.crawl_all_chapters(url, max_chapters)
            
            if not all_chapters:
                print("未能获取任何章节")
                return None
            
            # 第一章作为主要文章
            main_article = all_chapters[0]
            other_chapters = all_chapters[1:] if len(all_chapters) > 1 else []
            
            # 尝试获取作者的其他文章
            other_articles = self.get_author_articles(main_article)
            
            # 保存结果
            json_file, txt_file = self.save_results_with_chapters(all_chapters, other_articles)
            
            print(f"\n爬取完成！")
            print(f"专栏章节: {len(all_chapters)}篇")
            print(f"作者其他文章: {len(other_articles)}篇")
            print(f"总计: {len(all_chapters) + len(other_articles)}篇文章")
            
            return {
                'all_chapters': all_chapters,
                'main_article': main_article,
                'other_chapters': other_chapters,
                'other_articles': other_articles,
                'files': {'json': json_file, 'txt': txt_file}
            }
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='微博头条文章爬虫 - Cookie支持版本')
    parser.add_argument('url', nargs='?', help='要爬取的微博头条文章URL')
    parser.add_argument('--cookies', '-c', help='Cookie文件路径 (支持.json或.txt格式)')
    parser.add_argument('--max-chapters', '-m', type=int, default=50, help='最大爬取章节数 (默认: 50)')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式，保存调试文件')
    
    args = parser.parse_args()
    
    # 如果没有提供URL，提示用户输入
    if not args.url:
        print("微博头条文章爬虫 - Cookie支持版本")
        print("=" * 50)
        url = input("请输入要爬取的微博头条文章URL: ").strip()
        if not url:
            print("错误：必须提供有效的URL")
            return
    else:
        url = args.url
    
    print("微博头条文章爬虫 - Cookie支持版本")
    print("=" * 50)
    print("Cookie使用说明:")
    print("1. 不使用Cookie（默认）: 可能无法访问需要登录的内容")
    print("2. 使用Cookie文件: 通过--cookies参数指定文件")
    print("3. 自动检测: 程序会自动查找cookies.json或cookies.txt文件")
    print("=" * 50)
    
    # 检查cookie文件
    cookies_file = args.cookies
    if not cookies_file:
        if os.path.exists('cookies.json'):
            cookies_file = 'cookies.json'
            print("发现cookies.json文件，将使用该文件中的cookie")
        elif os.path.exists('cookies.txt'):
            cookies_file = 'cookies.txt'
            print("发现cookies.txt文件，将使用该文件中的cookie")
        else:
            print("未发现cookie文件，使用默认基础cookie")
            print("\n如需使用真实cookie，请:")
            print("1. 在浏览器中登录微博")
            print("2. 按F12打开开发者工具")
            print("3. 在Network标签页中找到weibo.com的请求")
            print("4. 复制Cookie请求头的值")
            print("5. 创建cookies.txt文件并粘贴cookie字符串")
            print("   或创建cookies.json文件，格式如: {\"SUB\": \"value\", \"SUBP\": \"value\"}")
            print("   或使用--cookies参数指定cookie文件路径")
    
    # 创建爬虫实例
    crawler = WeiboTTArticleCrawler(cookies_file=cookies_file)
    
    # 设置调试模式
    crawler.debug_mode = args.debug
    
    print(f"\n开始爬取: {url}")
    print(f"最大章节数: {args.max_chapters}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    
    # 开始爬取
    result = crawler.crawl_article(url, args.max_chapters)
    
    if result:
        print("\n爬取成功！")
        # 保存当前使用的cookie以供下次使用
        crawler.save_cookies_to_file('last_used_cookies.json')
    else:
        print("\n爬取失败！")
        print("\n可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 更新cookie（如果内容需要登录）")
        print("3. 稍后重试（可能遇到访问限制）")
        print("4. 使用--debug参数查看详细调试信息")

if __name__ == "__main__":
    main()