# -*- coding: utf-8 -*-
# 作者:             inspurer(月小水长)
# 创建时间:          2020/11/1 19:43
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# qq邮箱            2391527690@qq.com
# 微信公众号         月小水长(ID: inspurer)
# 文件备注信息       todo


import csv
import os
import random
import re
import sys
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep
import pandas as pd

import requests

requests.packages.urllib3.disable_warnings()
from lxml import etree
import json

User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
Cookie='_T_WM=8cf41e6b84ecb186573cf7692be0594b; SCF=AkR6w_OILlm5cICJ3O0zJLVeILJ5f4DeTub9f3BrVvYSlGVDLcXib5q5PAA7DZNlidvT64Ww5bwR1pg3TfZmZaI.; SUB=_2A25JaOWVDeThGeBP61QX9i3NyT6IHXVqkovdrDV6PUJbktANLWf2kW1NRX6Dfjfw02qhpzEgsLXiWcfaV-wgj5IR; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Wh-F.1FbuSLbg9mI68f4c1u5JpX5K-hUgL.FoqpehqcSoepeoz2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMceK5cSoq0eKzE; SSOLoginState=1684837829; ALF=1687429829'
class WeiboUserScrapy():
    IMG_LINK_SEP = ' '
    IMG_SAVE_ROOT = 'img'

    def __init__(self, user_id, filter=0, download_img=False):
        global headers
        self.headers = {
            'Cookie': Cookie,
            'User_Agent': User_Agent
        }

        if filter != 0 and filter != 1:
            sys.exit('filter值应为0或1,请重新输入')

        self.user_id = str(user_id)  # 用户id,即需要我们输入的数字,如昵称为"Dear-迪丽热巴"的id为1669879400
        self.filter = filter  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        self.download_img = download_img  # 微博抓取結束后是否下载微博图片
        self.nickname = ''  # 用户昵称,如“Dear-迪丽热巴”
        self.weibo_num = 0  # 用户全部微博数
        self.got_num = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibo = []  # 存储爬取到的所有微博信息
        if not os.path.exists('user'):
            os.mkdir('user')
        if not os.path.exists(self.IMG_SAVE_ROOT):
            os.mkdir(self.IMG_SAVE_ROOT)
        if self.download_img:
            self.img_save_folder = os.path.join(self.IMG_SAVE_ROOT, self.user_id)
            if not os.path.exists(self.img_save_folder):
                os.mkdir(self.img_save_folder)
        self.run()

    def deal_html(self, url):
        """处理html"""
        try:
            html = requests.get(url, headers=self.headers, verify=False).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def deal_garbled(self, info):
        """处理乱码"""
        try:
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_nickname(self):
        """获取用户昵称"""
        try:
            url = 'https://weibo.cn/{}/info'.format(self.user_id)
            selector = self.deal_html(url)
            nickname = selector.xpath('//title/text()')[0]
            self.nickname = nickname[:-3]
            if self.nickname == '登录 - 新' or self.nickname == '新浪':
                sys.exit('cookie错误或已过期')
            print('用户昵称: ' + self.nickname)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_user_info(self, selector):
        """获取用户昵称、微博数、关注数、粉丝数"""
        try:
            self.get_nickname()  # 获取用户昵称
            user_info = selector.xpath("//div[@class='tip2']/*/text()")

            self.weibo_num = (user_info[0][3:-1])
            print('微博数: ' + str(self.weibo_num))

            self.following = (user_info[1][3:-1])
            print('关注数: ' + str(self.following))

            self.followers = (user_info[2][3:-1])
            print('粉丝数: ' + str(self.followers))
            print('*' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_page_num(self, selector):
        """获取微博总页数"""
        try:
            if selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(
                    selector.xpath("//input[@name='mp']")[0].attrib['value'])
            return page_num
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_weibo(self, weibo_link):
        """获取长原创微博"""
        try:
            selector = self.deal_html(weibo_link)
            info = selector.xpath("//div[@class='c']")[1]
            wb_content = self.deal_garbled(info)
            wb_time = info.xpath("//span[@class='ct']/text()")[0]
            weibo_content = wb_content[wb_content.find(':') +
                                       1:wb_content.rfind(wb_time)]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_original_weibo(self, info, weibo_id):
        """获取原创微博"""
        try:
            weibo_content = self.deal_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind('赞')]
            a_text = info.xpath('div//a/text()')
            if '全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                sleep(2)
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            weibo_content = wb_content[:wb_content.rfind('原文转发')]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_retweet(self, info, weibo_id):
        """获取转发微博"""
        try:
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if not original_user:
                wb_content = '转发微博已被删除'
                return wb_content
            else:
                original_user = original_user[0]
            wb_content = self.deal_garbled(info)
            wb_content = wb_content[wb_content.find(':') +
                                    1:wb_content.rfind('赞')]
            wb_content = wb_content[:wb_content.rfind('赞')]
            a_text = info.xpath('div//a/text()')
            if '全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                weibo_content = self.get_long_retweet(weibo_link)
                if weibo_content:
                    wb_content = weibo_content
            retweet_reason = self.deal_garbled(info.xpath('div')[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex('赞')]
            wb_content = (retweet_reason + '\n' + '原始用户: ' + original_user +
                          '\n' + '转发内容: ' + wb_content)
            return wb_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def is_original(self, info):
        """判断微博是否为原创微博"""
        is_original = info.xpath("div/span[@class='cmt']")
        if len(is_original) > 3:
            return False
        else:
            return True

    def get_weibo_content(self, info, is_original):
        """获取微博内容"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            if is_original:
                weibo_content = self.get_original_weibo(info, weibo_id)
            else:
                weibo_content = self.get_retweet(info, weibo_id)
            print(weibo_content)
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_place(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath('div')[0]
            a_list = div_first.xpath('a')
            publish_place = '无'
            for a in a_list:
                if ('place.weibo.com' in a.xpath('@href')[0]
                        and a.xpath('text()')[0] == '显示地图'):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        publish_place = weibo_a[-1]
                        if ('视频' == div_first.xpath(
                                "span[@class='ctt']/a/text()")[-1][-2:]):
                            if len(weibo_a) >= 2:
                                publish_place = weibo_a[-2]
                            else:
                                publish_place = u'无'
                        publish_place = self.deal_garbled(publish_place)
                        break
            print('微博发布位置: ' + publish_place)
            return publish_place
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            publish_time = str_time.split('来自')[0]
            if '刚刚' in publish_time:
                publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            elif '分钟' in publish_time:
                minute = publish_time[:publish_time.find('分钟')]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() -
                                minute).strftime('%Y-%m-%d %H:%M')
            elif '今天' in publish_time:
                today = datetime.now().strftime('%Y-%m-%d')
                time = publish_time[3:]
                publish_time = today + ' ' + time
            elif '月' in publish_time:
                year = datetime.now().strftime('%Y')
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = year + '-' + month + '-' + day + ' ' + time
            else:
                publish_time = publish_time[:16]
            print('微博发布时间: ' + publish_time)
            return publish_time
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split('来自')) > 1:
                publish_tool = str_time.split('来自')[1]
            else:
                publish_tool = '无'
            print('微博发布工具: ' + publish_tool)
            return publish_tool
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_weibo_footer(self, info):
        """获取微博点赞数、转发数、评论数"""
        try:
            footer = {}
            pattern = r'\d+'
            str_footer = info.xpath('div')[-1]
            str_footer = self.deal_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind('赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            print('点赞数: ' + str(up_num))
            footer['up_num'] = up_num

            retweet_num = int(weibo_footer[1])
            print('转发数: ' + str(retweet_num))
            footer['retweet_num'] = retweet_num

            comment_num = int(weibo_footer[2])
            print('评论数: ' + str(comment_num))
            footer['comment_num'] = comment_num
            return footer
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def extract_picture_urls(self, info, weibo_id):
        print('开始提取图片 URL')
        """提取微博原始图片url"""
        try:
            selector = self.deal_html(f"https://weibo.cn/mblog/picAll/{weibo_id}?rl=2")
            if not selector:
                return ''
            sleep(1)
            picture_list = selector.xpath('//img/@src')
            picture_list = [
                p.replace('/thumb180/', '/large/').replace('/wap180/', '/large/')
                for p in picture_list
            ]
            print(picture_list)
            picture_urls = self.IMG_LINK_SEP.join(picture_list)
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_picture_urls(self, info, is_original):
        """获取微博原始图片url"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            picture_urls = {}
            if is_original:
                original_pictures = self.extract_picture_urls(info, weibo_id)
                picture_urls['original_pictures'] = original_pictures
                if not self.filter:
                    picture_urls['retweet_pictures'] = '无'
            else:
                retweet_url = info.xpath("div/a[@class='cc']/@href")[0]
                retweet_id = retweet_url.split('/')[-1].split('?')[0]
                retweet_pictures = self.extract_picture_urls(info, retweet_id)
                picture_urls['retweet_pictures'] = retweet_pictures
                a_list = info.xpath('div[last()]/a/@href')
                original_picture = '无'
                for a in a_list:
                    if a.endswith(('.gif', '.jpeg', '.jpg', '.png')):
                        original_picture = a
                        break
                picture_urls['original_pictures'] = original_picture
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = self.is_original(info)
            if (not self.filter) or is_original:
                weibo['id'] = info.xpath('@id')[0][2:]
                weibo['link'] = 'https://weibo.cn/comment/{}?uid={}&rl=0#cmtfrm'.format(weibo['id'], self.user_id)
                weibo['content'] = self.get_weibo_content(info,
                                                          is_original)  # 微博内容
                picture_urls = self.get_picture_urls(info, is_original)
                weibo['original_pictures'] = picture_urls[
                    'original_pictures']  # 原创图片url
                if not self.filter:
                    weibo['retweet_pictures'] = picture_urls[
                        'retweet_pictures']  # 转发图片url
                    weibo['original'] = is_original  # 是否原创微博
                weibo['publish_place'] = self.get_publish_place(info)  # 微博发布位置
                weibo['publish_time'] = self.get_publish_time(info)  # 微博发布时间
                weibo['publish_tool'] = self.get_publish_tool(info)  # 微博发布工具
                footer = self.get_weibo_footer(info)
                weibo['up_num'] = footer['up_num']  # 微博点赞数
                weibo['retweet_num'] = footer['retweet_num']  # 转发数
                weibo['comment_num'] = footer['comment_num']  # 评论数
            else:
                weibo = None
            return weibo
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        try:
            url = f'https://weibo.cn/{self.user_id}/profile?page={page}'
            selector = self.deal_html(url)
            info = selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                for i in range(0, len(info) - 1):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        self.weibo.append(weibo)
                        self.got_num += 1
                        print('-' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    @staticmethod
    def drop_duplicate(file_path):
        df = pd.read_csv(file_path)
        # print(df.shape[0])
        df.drop_duplicates(keep='first', subset=['wid'], inplace=True)
        # 去重重复 header
        df.drop(df[df['publish_time'].isin(['publish_time'])].index, inplace=True)
        # print(df.shape[0])
        df.sort_values(by=['publish_time'], ascending=False, inplace=True)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

    def write_csv(self, wrote_num):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                'wid',
                'weibo_link',
                'content',
                'img_urls',
                'location',
                'publish_time',
                'publish_tool',
                'like_num',
                'forward_num',
                'comment_num',
            ]
            if not self.filter:
                result_headers.insert(4, 'origin_img_urls')
                result_headers.insert(5, 'is_origin')
            result_data = [w.values() for w in self.weibo][wrote_num:]
            self.file_path = './user/{}_{}.csv'.format(self.user_id, self.nickname)
            # with open('./user/{}_{}_{}博_{}粉_{}关注.csv'.format_excc(self.user_id,self.nickname,self.weibo_num, self.followers,self.following),'a',encoding='utf-8-sig',newline='') as f:
            with open(self.file_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if wrote_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            self.drop_duplicate(self.file_path)
            print(u'%d条微博写入csv文件完毕:' % self.got_num)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_file(self, wrote_num):
        """写文件"""
        if self.got_num > wrote_num:
            self.write_csv(wrote_num)

    def get_weibo_info(self):
        """获取微博信息"""
        try:
            url = f'https://weibo.cn/{self.user_id}/profile'
            selector = self.deal_html(url)
            self.get_user_info(selector)  # 获取用户昵称、微博数、关注数、粉丝数
            page_num = self.get_page_num(selector)  # 获取微博总页数
            wrote_num = 0
            page1 = 0
            user_page_config = 'user_page.json'
            if not os.path.exists('user_page.json'):
                page = 1
                with open(user_page_config, 'w', encoding='utf-8-sig') as f:
                    f.write(json.dumps({f'{self.user_id}': page}, indent=2))
            else:
                with open(user_page_config, 'r', encoding='utf-8-sig') as f:
                    raw_json = json.loads(f.read())
                    if self.user_id in raw_json.keys():
                        page = raw_json[self.user_id]
                    else:
                        page = 0

            random_pages = random.randint(1, 5)
            for page in range(page, page_num + 1):
                self.get_one_page(page)  # 获取第page页的全部微博

                with open(user_page_config, 'r', encoding='utf-8-sig') as f:
                    old_data = json.loads(f.read())
                    old_data[f'{self.user_id}'] = page

                with open(user_page_config, 'w', encoding='utf-8-sig') as f:
                    f.write(json.dumps(old_data, indent=2))

                if page % 3 == 0:  # 每爬3页写入一次文件
                    self.write_file(wrote_num)
                    wrote_num = self.got_num

                # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                if page - page1 == random_pages and page < page_num:
                    sleep(random.randint(6, 10))
                    page1 = page
                    random_pages = random.randint(1, 5)
            self.write_file(wrote_num)  # 将剩余不足3页的微博写入文件
            if not self.filter:
                print('共爬取' + str(self.got_num) + '条微博')
            else:
                print('共爬取' + str(self.got_num) + '条原创微博')
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def do_down_img(self, img_url, savepath):
        if os.path.exists(savepath):
            print(f'{img_url} 已经下载过')
            return
        try:
            print(f"正在下载图片 {img_url} ...")
            with open(savepath, 'wb') as fp:
                response = requests.get(url=img_url, headers=self.headers)
                fp.write(response.content)
            print('图片下载成功')
            sleep(1)
        except:
            print('图片下载失败')

    def get_weibo_img(self):
        '''下载相册图片'''
        if self.download_img:
            df = pd.read_csv(self.file_path)
            for index, row in df.iterrows():
                print(f'index: {index + 1} / {df.shape[0]}')
                # 下载相册图片使用 img_urls
                # 下载转发过的微博里面的图片使用 origin_img_urls

                image_cols = ['img_urls']
                if not self.filter:
                    image_cols.append('origin_img_urls')

                wid = row['wid']

                for ic in image_cols:
                    image_urls = row[ic]
                    if image_urls == None or isinstance(image_urls, float) or image_urls == '' or image_urls == '无':
                        pass
                    else:
                        image_urls = image_urls.split(self.IMG_LINK_SEP)
                        for index, image_url in enumerate(image_urls):
                            self.do_down_img(image_url, os.path.join(self.img_save_folder, f'{wid}_{ic[:-5]}_{index + 1}.jpg'))

    def run(self):
        """运行爬虫 """
        try:
            print('开始抓取微博')
            self.get_weibo_info()
            print('微博抓取完毕，开始下载相册图片')
            self.get_weibo_img()
            print('*' * 100)

        except Exception as e:
            print('Error: ', e)
            print(traceback.format_exc())


if __name__ == '__main__':
    # 注意关闭 vpn，注意配置代码第 29 行处的 cookie
    # 2023.2.12 更新
    # 1、解决无法抓取 cookie 对应账号微博的问题
    # 2、解决微博抓取不全的问题，解决微博全文无法获取的问题（有待多次验证）
    # 3、可选下载所有图片（包括微博相册和转发微博里面的图片），参数为 download_img，默认为 False 不下载
    id_list = [5143117209, 2033248174, 1907767253, 1257831543, 1801055875, 1232114604, 1703296145, 5643994130, 2732754935, 2661504823, 3828809034, 1679517897, 1801920002, 1811363633, 2493507623, 1195379710, 1640365687, 1197354837, 1345943410, 2287349412, 1752164320, 5126446888, 1313454973, 1740301135, 2350442141, 1244856617, 1218494871, 2409370432, 6447211492, 1910171127, 5607826030, 1292815744, 1198073405, 2064160160, 5619779382, 1871672550, 1749937787, 3185250997, 1225563944, 2029906001, 1402602034, 1862974331, 7275646478, 2794430491, 6019404696, 1656214784, 1808764472, 6179279336, 1712354525, 2021822051, 1906339011, 1976794091, 5626136031, 1219952281, 1222425514, 1276314124, 1928540007, 7064708862, 2620811727, 1910672761, 1035674473, 5886998602, 3944068535, 6823546584, 1262819273, 1258824907, 1623965900, 1802264644, 3916424386, 5891319276, 2157329842, 3005331561, 5490326028, 2113045567, 1927706047, 5616945199, 2882733894, 5887697249, 6047467945, 1912449555, 1246756713, 1821135665, 5874514144, 2761630725, 1930258915, 2655245350, 1734442735, 5680343342, 1722803755, 3600625653, 1835539930, 1967952367, 2044833997, 2619723465, 2285334795, 1927305954, 1728945512, 1110411735, 1408932587, 1252032243, 1734466633, 1298062167, 2644575251, 1721425872, 1440344522, 5680339910, 3579616231, 1580993472, 2344543981, 1743938470, 2449552120, 1762210562, 3370070480, 6741964788, 1656312435, 1873914867, 5023069053, 6463527162, 1792673805, 1689023367, 2623007997, 3371436430, 1767819164, 1501634660, 1698077481, 3319236353, 1877701971, 1785884091, 5786332015, 2130771712, 1255250097, 1731864915, 1750155477, 1497176560, 2688201053, 3500459811, 1721860370, 1867002514, 2014845112, 1829335871, 1822299354, 1216826653, 1664279327, 1732442457, 1846225514, 1806062307, 3708072513, 2565158051, 5693482483, 1736275134, 5398979743, 1249629725, 2146965345, 1375953203, 6529876887, 1319015503, 1006421732, 1824553760, 2629731043, 2113270200, 3176010690, 1794572275, 1826628633, 2705589884, 5977036090, 1745766100, 3100185195, 1240959311, 1240959311, 1586148707, 1738171957, 1225419417, 1268252377, 1641519890, 1716761743, 1779875541, 2003394681, 1926243773, 2700162334, 1256223644, 1483820045, 3820754851, 2424084591, 1749774442, 1648886722, 1817472001, 1623412013, 3675865547, 1307243944, 2119367023, 6115182009, 2700877354, 7155113315, 1736695537, 1193256103, 1580971924, 1270354642, 1566936885, 2431095307, 1171345731, 1704658972, 2085966565, 1700486331, 1797069487, 1642586513, 2845018135, 3309483405, 1751606144, 1807776872, 1735957450, 3178384564, 1825329153, 1894947983, 2707527833, 6522115298, 3213107764, 6288254740, 2153928381, 1097080752, 1876156855, 1672587573, 1066317210, 1630856882, 3962982466, 1617774075, 1659064660, 1264674527, 2257401393, 5172843865, 3108949955, 5887863238, 1801988971, 5659866424, 5127009132, 6057973808, 2282421827, 1997726860, 1825573943, 6203188939, 2956384255, 2281544503, 1863792930, 1526131963, 3968741640, 1739266037, 1791715730, 2583858490, 1757052517, 1714193955, 1835110811, 1261141474, 1199275700, 1654807054, 2610429597, 2049002927, 1827243543, 1733078595, 2191588464, 1323061061, 1735695412, 1751125675, 2868803181, 1224449043, 1132891981, 7166486922, 1225627080, 2433827884, 1231688837, 1797054534, 7527950457, 2117726305, 1054007001, 3285031871, 2696749592, 1951031735, 1322373644, 1922233745, 1730338264, 1721396755, 6190030326, 1045134617, 1233614375, 1814284757, 2684259633, 2643307453, 2643307453, 1787196155, 1013657184, 1746118392, 5967503625, 7524392184, 3175707612, 1229906331, 1500894097, 3030365523, 1269402871, 1496838293, 1745811937, 1223537940, 1321880115, 2356534223, 1895567845, 1868725482, 1692042771, 2057070033, 2342329387, 1864388983, 3616258995, 1826643727, 1271359943, 2600926867, 6795935450, 5656129896, 1660235667, 1735125594, 2268869983, 1702129627, 2409068545, 1766673785, 1465832951, 2451544942, 1273380037, 1213536224, 2502471581, 1242418703, 1289012440, 1840441844, 3116872295, 1680313495, 2155202415, 2795857600, 2251552653, 5300636312, 2112642651, 5543153302, 3908122917, 5318584155, 1357579865, 1840141932, 2176141495, 7339969127, 1245429172, 5607257930, 1796258175, 1264890570, 2324900557, 3609302441, 5112240060, 1724196104, 1576850535, 1686751151, 1373539132, 2128209774, 3181706612, 1845675654, 1770026453, 1769171570, 3932588380, 5688774559, 2823738074, 6055458953, 1971076403, 5920356880, 1827685703, 1737877151, 3528394330, 1313455195, 5211643249, 6988788731, 2745509764, 2104645281, 5627362571, 3478459251, 6296303400, 1877253217, 3739204194, 2807129234, 1842298803, 5912379360, 2235844972, 1217577193, 2139155362, 5503504780, 6263891074, 1874288121, 1363064563, 1279709861, 1740573077, 5119853579, 1799605655, 5775941209, 1235481371, 1217541774, 1228948940, 2677589285, 5901287687, 1747684497, 1792547357, 1411482802, 5682216571, 5879751395, 2538950143, 5449297975, 2176389945, 1586249967, 1771088177, 1709572805, 2976620041, 1769985142, 1505989231, 6988800170, 1772914881, 7475996012, 1760938994, 2806630012, 1775564374, 1730123695, 1594600804, 1228131382, 1805606247, 2687868021, 1768887231, 5922952768, 2265582003, 6989467163, 2554325211, 1798592270, 1874998095, 1228692737, 1768341151, 1888024547, 5464355430, 5055034462, 1261297105, 1567250074, 1229860611, 3313256852, 1861641734, 1882307872, 1288604907, 1567261593, 5356416594, 1735833683, 6171388940, 2250755382, 1838922731, 1217261134, 5985666104, 2521166497, 1212394350, 1679824627, 1195017937, 5072151301, 3984792451, 2440235910, 1244829331, 6123372493, 7370292839, 1650305567, 1195019732, 5273009671, 1738734804, 1369706300, 1501877483, 1815759383, 2672500515, 1746263014, 1268453601, 2680736212, 1248793710, 2307753290, 1893347753, 1505903624, 1722150384, 3558391704, 1643200985, 2169289455, 2606436331, 1278178992, 2759526793, 1792997800, 5418912902, 1213529407, 5948448170, 1270577247, 1774846944, 5717017841, 1218355240, 5048169615, 1672330664, 1161133861, 1714732373, 1686659730, 2125924401, 1874320010, 5070172775, 1732418574, 1096102210, 3023889587, 1613258127, 1808951997, 2388776035, 1511975374, 5623374073, 6525850639, 1750222444, 1465371653, 1287604042, 2010654675, 1671545692, 2000749772, 6331885976, 1290364693, 1671959152, 1898516834, 1266788915, 1885054850, 1929816272, 3973455743, 3748534967, 1833973550, 3987559881, 5214076932, 1901751947, 1256806373, 6495371429, 1706948687, 2199840307, 1628482500, 1218639357, 2954186642, 1739475907, 2790987297, 6015166419, 3479629641, 1251615823, 2270636385, 5885940120, 3547332173, 1847856024, 1767868420, 1984841003, 2121746677, 1721099481, 1265295777, 1419278235, 2495158142, 3779962062, 1712782607, 2323836621, 1404999597, 5019577390, 1892663771, 1734445321, 1793180284, 2168029022, 3221102132, 1951110477, 1402310184, 1559988215, 1281950453, 1765335300, 3655689037, 1802675582, 1198408797, 1902396531, 1219459467, 1633079705, 1391061615, 6106249012, 2136002182, 1289631817, 3785739782, 1241931415, 2004546117, 1301064830, 6041673899, 1139098205, 3710674180, 1781372535, 3127526303, 3898567542, 1746901070, 5541361691, 3316146805, 1700420845, 1271475524, 3031831014, 2529348553, 1846427083, 3279873201, 2183765897, 2187299437, 1463707815, 1247063043, 6356142753, 1890773304, 1798381277, 5066166401, 2097482553, 2358157617, 1310255983, 1194892683, 1845790602, 2180249535, 1928872330, 1596354251, 3484986413, 1952286741, 3558201323, 2054996223, 2088912225, 1909979083, 2507788061, 3705941004, 2284381983, 2099555177, 1262964014, 5382742539, 1594941220, 5753994009, 2260957637, 6124627606, 1901162013, 2323760064, 2135486115, 1457699772, 228046102, 1725217600, 2099804201, 1662450871, 1660352010, 5043210086, 2169519682, 2692396272, 1774604001, 1210348320, 1398886745, 1891197302, 1002143827, 1254127560, 3620180771, 1076907402, 2451459323, 5941967267, 1665736437, 1912851947, 6791298205, 5672619890, 1233308293, 1588460680, 1773190267, 1686997830, 1701624681, 1249298075, 2856548130, 1224672814, 1826205592, 2845350992, 1763969373, 1721427037, 5593360163, 1807802183, 1921089310, 1750333295, 1317052044, 1798111971, 1212569831, 1246379911, 1229641152, 1582330690, 6142442691, 1199429884, 7014823596, 1711704715, 2389624897, 1214663600, 1212612565, 1745464970, 2491905683, 1911237367, 1239368103, 6442501619, 2266537042, 1784448804, 2205765065, 1686810661, 2374854813, 2501511785, 1320682073, 1881976852, 1692056982, 1940966310, 1774124194, 1256042280, 5863441494, 1256917082, 1277053657, 6258357937, 1752618033, 1854951145, 2734343924, 1752778612, 5210781129, 3119949624, 1355837881, 2102380517, 1500585892, 1781199803, 1663561194, 1984967881, 1560712503, 1594925933, 1253020831, 1910735460, 1648887267, 1557283450, 1647334697, 1528637284, 2979392192, 1670970787, 3534888350, 2011939425, 5880065475, 1342732931, 5628105945, 2736797132, 1348026261, 1689224772, 1797816724, 3054571717, 6088257243, 3585483752, 1240200895, 1802740171, 5705693126, 1739791150, 1706715944, 1793569311, 1277738857, 1609773927, 1915458005, 1622967225, 3803968739, 5610438555, 2357205141, 5885812685, 1231821870, 1212999073, 1283686064, 1934756582, 1307296987, 1300367447, 1308901094, 1626443785, 1838717532, 1823954192, 1601447455, 2111506967, 1995801167, 1819102687, 1653472004, 1761713265, 1988354725, 1265410293, 1764654382, 1231687250, 1220746691, 1228196907, 1192331292, 1218925030, 2166297137, 5230456780, 1787544153, 1284235270, 1341155903, 1950640211, 1117395942, 5675478244, 2264393257, 1823455165, 1640631034, 1046611253, 6013611098, 1391954182, 1405998362, 1302358487, 1528462485, 5652423635, 1244759855, 6263764064, 1214835457, 1657693052, 6271559855, 1807660103, 1948110002, 1065105440, 1418293330, 1677937662, 1497714725, 1729859377, 2037027642, 3471850792, 2480172345, 1730930214, 1462356705, 3026210250, 2150835921, 1172571555, 1419517335, 1624837895, 1871944365, 1689273620, 5387897948, 6473069383, 1296348605, 1219766982, 1232859091, 7552181904, 1667629881, 1402621192, 1196900641, 1809680753, 2254791010, 1874356165, 1886290635, 2181404294, 1238296465, 5672291931, 1322714793, 1469187111, 2734269954, 1744080731, 1884277373, 1676534905, 1578282541, 1225923717, 1212447630, 1814738543, 5435474188, 1225419941, 5121228416, 7351423700, 1726134784, 2732448712, 1236837097, 1220566780, 5443650019, 1887895795, 1708309817, 2179021091, 2955896132, 3916509316, 1854303295, 2617317504, 1750638262, 1740494923, 1801421710, 5880066726, 1836312141, 1418555123, 1613806934, 1864328092, 2141279315, 1242519605, 1236636620, 1713696033, 2387935353, 2267520074, 2083438721, 1380193101, 1271354361, 1727687652, 1286151312, 2139168374, 1757723563, 1093345840, 1243765252, 3050792913, 5221439722, 1227035881, 1735431001, 2739972155, 1211598953, 3927931816, 1215180647, 1680338307, 1791703837, 2707744090, 2164393223, 1304579737, 2205793227, 1586994221, 1845824364, 5849028307, 1413727783, 5690264778, 2667431265, 1254192443, 1783011685, 1763910584, 1560926874, 1560853005, 2081667845, 5546660784, 3034045004, 1744195595, 1748764503, 1729714591, 2904949345, 1641530562, 1743513605, 1646493427, 1289988734, 2449152482, 1907616172, 2107955050, 1771252683, 1228864031, 1991083414, 1324243857, 1792857820, 1732032912, 1609940921, 3174185127, 2307953755, 1678682530, 1893993941, 2808295293, 1791519375, 5901077408, 1654390540, 1223540840, 2461607990, 2319096075, 1570722975, 1574790192, 1848949921, 5976663270, 3414361710, 5643723331, 1709121233, 1405426355, 2031473245, 2281717305, 1830500202, 3062769307, 1272621567, 1880086437, 3197433977, 1609301832, 1288814951, 1658397224, 1707463070, 1449788625, 2549177871, 1262945510, 1750119550, 1758223955, 1222729470, 1882611787, 3675601605, 1742757850, 1894805985, 3669076064, 1665102492, 3172918062, 6393166009, 1791747650, 1266404711, 1904446207, 5777703045, 1243121537, 1229419552, 1674176955, 1852196695, 1721523337, 1744849604, 1732673582, 5256877731, 1675028977, 3481921712, 1294814247, 2388394831, 2553418722, 2274595341, 1238726334, 1279943242, 1705147594, 1317754153, 2623641965, 1159746725, 1697045860, 1624095323, 3496414495, 2368711221, 1650770275, 5632153942, 5393756108, 3699172790]
    for i in range(len(id_list)):
        WeiboUserScrapy(user_id=id_list[i], filter=0, download_img=False)
