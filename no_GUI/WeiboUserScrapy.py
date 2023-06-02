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
    id_list = [2248803312, 1749842582, 1886461330, 5720777134, 6385000417, 6404590560, 1858734882, 2480789220, 2424676762, 2424676762, 3547922527, 7721991615, 5671035663, 6279942152, 3846227105, 3846227105, 1740293690, 5385445938, 6329168354, 5759359520, 2255757894, 5098924273, 2373667922, 5759359520, 2122208721, 6551307917, 1836300832, 1921439757, 2619152523, 2940162781, 2100277994, 2866295450, 5886052092, 7561674226, 6617208779, 3354294234, 3354294234, 5111747178, 7504076590, 3903006386, 3580198440, 2984813504, 6366535147, 3239625572, 3038283547, 2625143865, 2920771634, 2523786820, 7098350086, 2693162972, 1902909102, 2063264115, 2779437300, 5176393389, 2167290631, 2316052830, 1726715942, 2991084874, 7754064105, 2160453571, 5508852234, 1802510251, 2695167601, 2949855784, 2617476123, 3186045217, 6259578979, 1740248463, 1740248463, 5504508908, 5048081129, 2596806027, 3920023961, 5013089132, 2316050362, 1962218223, 1962218223, 5516238751, 2177278634, 2706465567, 2692590351, 2735140947, 2736142045, 2734949901, 2719680093, 2513847640, 2725753227, 1820302591, 2582727560, 1979554842, 3168369601, 6046067395, 3088902731, 3093233825, 5270231449, 5871867144, 3169417005, 3096972613, 3096428075, 3096434835, 3099714125, 3168379641, 3168388121, 3099652987, 3169403271, 7238868190, 3093212805, 3092819677, 3097127485, 5872380300, 2142612505, 3097076061, 3096437071, 3092771495, 3169394071, 3168358765, 3099835603, 2633677501, 2279727162, 5704665021, 2674772681, 6791505712, 2626700707, 7168992615, 7168992615, 2260759160, 2432012837, 2120269110, 2442446765, 2501583234, 2094595190, 1941551890, 5893040760, 2028769691, 1993419200, 2501273632, 2058427580, 2129979887, 2337348984, 2490779410, 2434330044, 2519525490, 2171464713, 2424624854, 2337442240, 2062877131, 1961578544, 2006014535, 2057989860, 1969398684, 2104801092, 1997769777, 2143986585, 2090152850, 2058451700, 2494998364, 2501485212, 1910982554, 1941533290, 2006752177, 2071875027, 2445125713, 2106399643, 2512996862, 2438119315, 1112140085, 1918345254, 2058132254, 2157016134, 2513788054, 2048911530, 2488141982, 2443814997, 2090445064, 2406716967, 2058405514, 2406716967, 2058405514, 1951067734, 2211894681, 6251400535, 5514838135, 6474970370, 1996563913, 7599512611, 2680771045, 3787551575, 1748876317, 3039630947, 2832931840, 3366112660, 2832987000, 6456660852, 3062567981, 5149633050, 2706982983, 2287471815, 2627293053, 2024095732, 6724328968, 3944085288, 7525104252, 5524090433, 3076913831, 2101419462, 3019307884, 1712693011, 3455848890, 2478411954, 1831061480, 2348810497, 7693962431, 5545848667, 2049470394, 2044214604, 5898273188, 2119743245, 2458495360, 2883716272, 2039168975, 1740936973, 2602824281, 2373626584, 2600497597, 3724267730, 2991085144, 3735611965, 1498356461, 5748760291, 5450785727, 5402025116, 3650605980, 2718932725, 7452105521, 6278531694, 6042778285, 1968100743, 2008547321, 1895094874, 1895094874, 1831945750, 1958215084, 3174955895, 6054605446, 6473857472, 1681933755, 7473960595, 5597887245, 2697780390, 5598178001, 5598178001, 2491179797, 5507822609, 1700719943, 5406319352, 2987593843, 5563465019, 1898624432, 5385438633, 3227999200, 2424671700, 6032994077, 3187792357, 2920215241, 6695350120, 3236855182, 6145933363, 3097756843, 3494864282, 1828417507, 7610293677, 2751083220, 6294937978, 5440128174, 3925986898, 5042528988, 3925986898, 5042528988, 1805939267, 3230654817, 2156681127, 5909958974, 3338206470, 3975793461, 3338206470, 3338206470, 3975793461, 2156648262, 2588272390, 2588272390, 5044514382, 3353987184, 1977610261, 3133907774, 3249080364, 1966788662, 6011273089, 6033269888, 2368168285, 6383250066, 6241234406, 5865661536, 6228519331, 3810028816, 1295953764, 6313983580, 5612026620, 5139842005, 1855705313, 5105235162, 5105235895, 5107945152, 2358430070, 2793676102, 3035108253, 1370148927, 7743665290, 2810196805, 6750471325, 2540286952, 5479528201, 2746035951, 3051869087, 3652058623, 2260091753, 5543120381, 5873632352, 3701630925, 5873632352, 7072072013, 7071323737, 7070105905, 3195849040, 7072076528, 3748077964, 7724310919, 5524066140, 5338652436, 2526224063, 2526409307, 3316649112, 3204862664, 6503721959, 6503721959, 2178332414, 5085912484, 5242146037, 7426463470, 7443892204, 5725591199, 5102582100, 1902734354, 3106644705, 3213307763, 6626811252, 2375748187, 6176054442, 5340015050, 3514295164, 2083443735, 2871636531, 3968836954, 5787014482, 5502452651, 3263014912, 3263014912, 2724824755, 5535510900, 5443649174, 6196950786, 5332066849, 3625973385, 1965618504, 5773996855, 2645900413, 3172588137, 2043877873, 2647377391, 5995944455, 5602762632, 6693710205, 3871286386, 3871286386, 2187065830, 5060941822, 3051392383, 7218157292, 7728128636, 7480305727, 2243958134, 3446138894, 5175029207, 5872249338, 3735287105, 6574022222, 5234771571, 7650836295, 3977619400, 2887665632, 2638319033, 5366337035, 7502248665, 6583733202, 3099336844, 5297670665, 5437133955, 6109424727, 5093521540, 5261052235, 7628017051, 5398177448, 5477216447, 5598139263, 5598139263, 1700182960, 6237374781, 7069697030, 2873482840, 2873516850, 2873566312, 2873513684, 2873519932, 3007221914, 3075637064, 3978451961, 2359411614, 2815340892, 2785519644, 3560641763, 1944899442, 2571946400, 5148293002, 2958953642, 6519424552, 6519424552, 6508290081, 2547584625, 3559041133, 5377633505, 3549888763, 7735692953, 1893296100, 7003514784, 2701870800, 2534589742, 3877036805, 3159894300, 2043395184, 2953465192, 3814471490, 7242338458, 3330242402, 3237274114, 1964483392, 2473741707, 2855127445, 1656284825, 6330400883, 6516836011, 1866686741, 2850978010, 2789214350, 2659255630, 3152556723, 3152556723, 3152556723, 5234200510, 3805780013, 1801644712, 1801644712, 5752999435, 5886402575, 1884378530, 7725493275, 2881636920, 2611346274, 2991137362, 2416598530, 2351261720, 6060030657, 3908489335, 2305241917, 7175997328, 1696258210, 2045159801, 2628538344, 3631762434, 2732718514, 2415459053, 2287529875, 7464983422, 5473578871, 5875114620, 1899227920, 2742923054, 1054376171, 5377203399, 5377203399, 3094395285, 3092597751, 5042053036, 5048177639, 3090897415, 3496891420, 2429297725, 3276065674, 3557588551, 3756484204, 3098536717, 3098536717, 3320158032, 6030056783, 3483240793, 2263155297, 3513868135, 3982605468, 2440586584, 6500534597, 2415872900, 5043979422, 3600931101, 3846320209, 7493842053, 3008041013, 3007820122, 5520856124, 3704667795, 5353715867, 5754936534, 6382731819, 2964524482, 7744162589, 6107930778, 5994521633, 5245494358, 3194560672, 3781891191, 2724500230, 2785746864, 5785182631, 3537002960, 2712725313, 5797547250, 2764679037, 5659704186, 2624418173, 1787345353, 1969850161, 2867678432, 3276544147, 6443863428, 2686531913, 2812161673, 3172605981, 5901288950, 6462972038, 3028349195, 2774051255, 2005733163, 7464260610, 2255955614, 1980226780, 5237640212, 3929069433, 5215990721, 5228913575, 7484354401, 3206530111, 5386414073, 2745481802, 2145765272, 2177022414, 2145765272, 3950137337, 3960342629, 3509258635, 3509258635, 6884521176, 3173937945, 3173937945, 5605067178, 2875243582, 2875243582, 5241676861, 1841302205, 2841979752, 2841979752, 5789142534, 2453040322, 1922557700, 2912792135, 6065597864, 3209160284, 2471202827, 5249416987, 3127704057, 3358047862, 2533728972, 5413425148, 7714995547, 6619613331, 7513928600, 7550186104, 6791448383, 6529503053, 1948998370, 1808907340, 1972255434, 1988825680, 2334542042, 2649341543, 2756301272, 5574474658, 6477186861, 6474537436, 5777123857, 6638100639, 6533316946, 7499194714, 5838113772, 6456742894, 7030989023, 6071543925, 6449655061, 5542003896, 5246120418, 5230419112, 6360961694, 7190356082, 5034791078, 2133102750, 2724375390, 6975623233, 6493747081, 7289808672, 6351273912, 2960914680, 5625623900, 6449655061, 5355537045, 5798147299, 2977238982, 7357003373, 2644610010, 3220079677, 3095922557, 3681779495, 5051720848, 2872629460, 5617144350, 6813152897, 1951203034, 5237077170, 2266240334, 2266285644, 7520821036, 1987892803, 2257424110, 1937108264, 2270296574, 7250320085, 2364799612, 3719196614, 2949015202, 7093541997, 2039268873, 1871701201, 1975866714, 2464352824, 2964429030, 6553126360, 2640320617, 3019531974, 3003952264, 3224105380, 3088741577, 3055179715, 3112995262, 2935743030, 3015867694, 3889846969, 5628420801, 2477160751, 3749519582, 7588265320, 5548602124, 6172868752, 2997392030, 1848994004, 3216500232, 3560589452, 3463134832, 5423099745, 5726824239, 5199666231, 5312194780, 6354028256, 6352282790, 5042293053, 5310242477, 3204924172, 2533970854, 6323988084, 2837878282, 5904493201, 2637132240, 2637139780, 2637100340, 2341047862, 5686029799, 2282500484, 3074376013, 5548585053, 2481674191, 1975476223, 5982381941, 2337126760, 2616512737, 5564659994, 1775689381, 5371033056, 1893932527, 5303547843, 5396092412, 2168223477, 3105539515, 2644608081, 1855753133, 1879849525, 2168223477, 3229218877, 3105539515, 3166811941, 2991682363, 5076775439, 2168223477, 1855753133, 3461954194, 3012583627, 5099542938, 1879849525, 6021509166, 5093197136, 2118968851, 1731572185, 2710391602, 2105413721, 2186835930, 3474025724, 6529461538, 5647199649, 5516877270, 3202642715, 3201381293, 6028387165, 5936357327, 6308163894, 5941645243, 5627146330, 5917912277, 5898199735, 2147056295, 5140820466, 5113346413, 1858719704, 2726861293, 2773271514, 3326583184, 2793250680, 1683591314, 2047888524, 2620462133, 2772738474, 2792569934, 2360053022, 2239698842, 2810367602, 2394335502, 2161415732, 2109128022, 2652838403, 2267745720, 2776186404, 2721698763, 3219955003, 7410588437, 2330272751, 2794214002, 3697448203, 2858417630, 1958966143, 2176831617, 3878489375, 3229814392, 3197885312, 3195659992, 2012585224, 2012585224, 1886959171, 2409517254, 6037135799, 6636326202, 3171166794, 3405604982, 3902739840, 5443663266, 5244110813, 5295118701, 1864525597, 5862180386, 6979878834, 2297044140, 5543719294, 5951535388, 3090981147, 2127005985, 6526572485, 7765043674, 1799453550, 1799453550, 6535741546, 6353790398, 3952004833, 7452921612, 7453428998, 5690319557, 5703807905, 5703486135, 3468816340, 1834861571, 5652106206, 3955028066, 3963808943, 3053069735, 6500771635, 5276737200, 3238470262, 2831553854, 2831553854, 3736437613, 5243939197, 3736437613, 6029577503, 7084472622, 1748851237, 2723946581, 3117573567, 2724434223, 1730948925, 6012897509, 2170403147, 2705167377, 2721812743, 2687604541, 3091549777, 2120583807, 2099283231, 1792409897, 1830781922, 2723949251, 1781312947, 1821390723, 1808598632, 2858062754, 3193487124, 6124772703, 6092122616, 2936897545, 2994229024, 5563571979, 2345008530, 3055264973, 3055216123, 2337692310, 3813888028, 2231835763, 6220396420, 6272139221, 2773178453, 6079160718, 5013032414, 2695464560, 3118428785, 5321766968, 2619114381, 7330216837, 3155233180, 6329156395, 2818634490, 3773741173, 3201326405, 1374816812, 6319541338, 2717104287, 2718445685, 1884906040, 7577752043, 2076498403, 2966834914, 3192916601, 5583317068, 2881976720, 2881976720, 6362094624, 6362094624, 6320265131, 3167382377, 1667589542, 2776295227, 2543689871, 3757376961, 5582155843, 2779076013, 2003314607, 3213095013, 3788584025, 3202537120, 2771661553, 5874060808, 2373181664, 2797283377, 3547363211, 3127331843, 1937206912, 2159504860, 2159479280, 5241224545, 1308995864, 2360834595, 1744686975, 6213530245, 6213530245, 5243636597, 3150924504, 2202090885, 2426637290, 3215289351, 3159461984, 7761601267, 7744691340, 5643254761, 2032134775, 6827399309, 5928509338, 2492551160, 1966789530, 5094809555, 2759589651, 5527950473, 5527950473, 6490747415, 6464039622, 2674835053, 5094809555, 1966789530, 2759589651, 3733951203, 3733951203, 2005323100, 3710664104, 2150745444, 2150745444, 3710664104, 2150709652, 2150709652, 2150709652, 3673104414, 1972745783, 5142543771, 6042622653, 3816550487, 7744606584, 7588045831, 6437439651, 2368877305, 5984940904, 5647384940, 5450741405, 5634297730, 2559757383, 5681314930, 2558978451, 5328753925, 3503146671, 1871529383, 2262676875, 2368877305, 1990315145, 3013300517, 1980370714, 1928774057, 1970805267, 2044211597, 1964007953, 2898089101, 1894755975, 3984049650, 3984049650, 2218792142, 5374537949, 6534032890, 2165890400, 5492411046, 2559518964, 3964792643, 2721774801, 2535702660, 1770952934, 5366468542, 1787647082, 1907405732, 1907405732, 2108737925, 1863349080, 1787647082, 2268565570, 2115265130, 3629215995, 5697413575, 2425593922, 2733865101, 5537119048, 6172911535, 3537010653, 2361722994, 6516584476, 6020611135, 5600186429, 6319193516, 3482408975, 2436518877, 5227293529, 5227293529, 2318429607, 2006625312, 2688910253, 5555248842, 2316602185, 2056700605, 5401674448, 5403090790, 3182409067, 5396644068, 6596666497, 3045729803, 3045729803, 2294650674, 3953660980, 5199538373, 6395567369, 3173446862, 7367983350, 6629128646, 6629128646, 7742497085, 1935629543, 3226951904, 5904234929, 5999127579, 3226951904, 5059823949, 3211485050, 2695100133, 2695100133, 3211485050, 5121400442, 2805113090, 2269388161, 2170273843, 3198109395, 5034259572, 5402017825, 3723593512, 6057048516, 6405547604, 5883514942, 5881876810, 5883294699, 3939440296, 5546080546, 6289394069, 2164803877, 5261068586, 2012977294, 2457437745, 2922579345, 3221942514, 5461542465, 3092834264, 5970032013, 7756654759, 2296113401, 7752373696, 7403903722, 7144694717, 5575075668, 2612199740, 5497663501, 2394426762, 1801242144, 3188654817, 5879087857, 1928474335, 6136703527, 7562839061, 3817044983, 5062191277, 3163575803, 2842285455, 3228858470, 2802543470, 5536013217, 7365968014, 5407773207, 5870157209, 1810665900, 3730994193, 5788536384, 1810665900, 2764940333, 5648008035, 7274191564, 1926874422, 3707230021, 2362697234, 7728283606, 6001308254, 3732706573, 1913371173, 1907503605, 3205272897, 5672256661, 3903561315, 1907503605, 1913371173, 2946001415, 7532320014, 5477983950, 2507736481, 2748464192, 1969191302, 1918943030, 3218479391, 1918943030, 3218479391, 7650360974, 2712860111, 5322083540, 5702831357, 7715486153, 6320283639, 6088273833, 3899773280, 3908711692, 5942994973, 2462162882, 2462162882, 2462162882, 2140592565, 5387857342, 3801920873, 1720380684, 2376142771, 5097583245, 6604264798, 2264174437, 2611655743, 5698825696, 2740113090, 2257574290, 2377316364, 7341643353, 3284910287, 5897795392, 3872490138, 6456251048, 6424993551, 2729215972, 3045699327, 6208962672, 7378805768, 6056009606, 6056009606, 6197106125, 2316719722, 6997148949, 2694053370, 2296622160, 6032758079, 6032758079, 3536756363, 3517849625, 3535144055, 3134685235, 6626757242, 3213859651, 3849707690, 3517849190, 3515567782, 3852206077, 7450492859, 2450914097, 5533807947, 5532788649, 3567024013, 2705166323, 2649660260, 2718254241, 5879365509, 2611790161, 2426642761, 5242874589, 5242874589, 3455085154, 2611790161, 1933478733, 5208626819, 3705965573, 3536797635, 2829218271, 5150042408, 3196224053, 5662194006, 3294198275, 1031347034, 2874280410, 3239898672, 6432981069, 3802163781, 5685695767, 3890063313, 2628455643, 7514302432, 1944251614, 2908844535, 5945876692, 5945876692, 3030973553, 7021707711, 5572007945, 3965843951, 2649064781, 1716237255, 5629927089, 5629751867, 5234585065, 1894643357, 5543752230, 1894643357, 6533794992, 3206670722, 6008373360, 5823031019, 6401932247, 3684014671, 6401932247, 3193410980, 3193410980, 5994596493, 2628525583, 2404312990, 1786651283, 2325483081, 6313987008, 5796702572, 3195589027, 6049484168, 7356695067, 5999502168, 3714045943, 2842611651, 3129920763, 3129920763, 2842611651, 2459796794, 5504484891, 7460226279, 2812669894, 6463237809, 5244309533, 2669856812, 2576921892, 5270321090, 7727511637, 1711476901, 2738765082, 2738765082, 2738765082, 2511456804, 2092261577, 2521197582, 2164527510, 2164527510, 3710992770, 3246705755, 2865678574, 2164527510, 2117033840, 3253069123, 2211861841, 5067278354, 3888580666, 3849705691, 3849441701, 2682267983, 7495281729, 5976264662, 3027531103, 2603210451, 2603210451, 5112031965, 7708351288, 7347657732, 2077077213, 7276511842, 2322771372, 2322771372, 6028376000, 2805342660, 5502540149, 6451685605, 2128595081, 2166852562, 1241305362, 5552801741, 7755847916, 5419301712, 1767998204, 6478774654, 6020672972, 2626270281, 2106526033, 3195555332, 6274390013, 5322519578, 2496599134, 3082563985, 1950951945, 5410647043, 2049302780, 2082746633, 2084546831, 2083479591, 7516722651, 3167144771, 3967977755, 6023293761, 3232072474, 3236142570, 6189944092, 3440810150, 3440810150, 3440810150, 6358094874, 5358140116, 6507181868, 5598186839, 5229619922, 5579109011, 3281643410, 1605978183, 1605978183, 1605978183, 6342496925, 6317684276, 3849954632, 2451210102, 5209151653, 5210843522, 1923070471, 5047625147, 3868901285, 5802448024, 3902009475, 3816579483, 5117269214, 5155886915, 5047538353, 5126081317, 5098245904, 5098507226, 3799121242, 6685033875, 3568463187, 3546114655, 3354190044, 3354190044, 5997590330, 5563497977, 5550971548, 2989169494, 3714103167, 5053736747, 3030968192, 3030968192, 2497851807, 1747752902, 2503124601, 2385092207, 1589352930, 1852621607, 7524708372, 6418876747, 6269443086, 3218034730, 7707456704, 2671988671, 2671988671, 3899977167, 3899977167, 5675838843, 2217419037, 3931111870, 3214820497, 2250024172, 2250043272, 2746353120, 6881815679, 5758007072, 2300275460, 5189850307, 1653625013, 2950140542, 3925651606, 3900229149, 5343580050, 6206278246, 2793376612, 2812032974, 1775209621, 1891528037, 2679856713, 2704265427, 2709850391, 2977378361, 3071726327, 3174990307, 2497831257, 5434957140, 7036287892, 3037506847, 2985390852, 7478425228, 2868482810, 2775265517, 6524701788, 7595698227, 7533467370, 5656499406, 6593197104, 5075781359, 2833585232, 3675387241, 2780298522, 2151090983, 2003760097, 7532964605, 7387268976, 7711998667, 3168651920, 3164587924, 3164609860, 5095666082, 2648095303, 1777029525, 2648095303, 7742367289, 1779569885, 2756488994, 1730854050, 2257384072, 1779113525, 3609125671, 5879089356, 2815909745, 3980149389, 2923565622, 2775216180, 6488550101, 3224514163, 3500422677, 2165580520, 6790457541, 5757034022, 2213182053, 5166812939, 5168159917, 2596391734, 5491417323, 3354543622, 5332718494, 2094679125, 5236037566, 5674067781, 3880378981, 3938816380, 6915845829, 5582016790, 3082596635, 2279915600, 1765991467, 1770627385, 2709613632, 7009576770, 1770627385, 2054701413, 6161765365, 6237373463, 1083035245, 2024408227, 2932708071, 5111063620, 5833660416, 3857089739, 3547260294, 3960773899, 3638522572, 3315391734, 1275852543, 3199279444, 2694336674, 6178929576, 6017159079, 2241856910, 2241856910, 5545588720, 6899938800, 7164433241, 2017719585, 2618629615, 2887589984, 1895789323, 7349732395, 5876960490, 5872597403, 2708331722, 7394622998, 3052691557, 2574272244, 7169450470, 6515433443, 5083903056, 5432446779, 3648723015, 7740770754, 2247210344, 2695995503, 1911604832, 2803820263, 3445702160, 5133393304, 5115638530, 3960190082, 2663525323, 6293027503, 2107614051, 1700738970, 2167368254, 2536227570, 1917905714, 2736508644, 5714761276, 7426455547, 2633653923, 6992161538, 3898820362, 5829169631, 5413936627, 2245469412, 7748314442, 5812205141, 7688778084, 2091872671, 3212275122, 2013814570, 3206557353, 5263231334, 5395594134, 5348162160, 5489249290, 5699428085, 5727854367, 7461158960, 5722915140, 3483019420, 2647214743, 2647214743, 6216748687, 1911805591, 2551840267, 2750839437, 5564003731, 1929914557, 7399546992, 7680262282, 2809361554, 3197132642, 6809098821, 2129821087, 1843415060, 5928736478, 5876988095, 2190885562, 3097818393, 5880630303, 1887298990, 3579357827, 2676937663, 5228232558, 3206698545, 7096883432, 7216772540, 2405526134, 3315670722, 7373625845, 5976502972, 5245450290, 7040413051, 3871637029, 5517528758, 2731903043, 5290669612, 2809309832, 3213585680, 7481965179, 5324448418, 3101187935, 2597854265, 2883857570, 3045642711, 7734016917, 3340383940, 3781180823, 2418419712, 3783217431, 2972359112, 5889897264, 5777115174, 5572746126, 2254113450, 2259527842, 2646741803, 2710370792, 2710370792, 1791436490, 6283216143, 3227235610, 1972131370, 1972179902, 3621924864, 6503618697, 1972028112, 2673174083, 1972046074, 1972027330, 1972052844, 5886014978, 3194840234, 5452482413, 5382050737, 2422679874, 5453101091, 5084350456, 5891713216, 5319485043, 2865048950, 7524503295, 5742432077, 5999622644, 1814497153, 3515288585, 7372395088, 6394095049, 3284292577, 6501049793, 2133847855, 3972170214, 2232547062, 2296060583, 6126584720, 2648677474, 3464394534, 2416541192, 3180536972, 5654088309, 7505138726, 6979002710, 6034740643, 2219023102, 2181648411, 1737522625, 5065485571, 5052014547, 3122042031, 3798578975, 5055399447, 1686300095, 2832561432, 5883432556, 5883432556, 5883432556, 5589265028, 7280691595, 6004433149, 3177960103, 3177960103, 5206790030, 2315673154, 1621725077, 2283478724, 3223938804, 5873052145, 7736993541, 7722919819, 1734141152, 7410934809, 2329750784, 2329750784, 3255961833, 2441123300, 3735160915, 1768898725, 5661928051, 5266830766, 5308355693, 3028027161, 2734297392, 2734297392, 2781912153, 5530415980, 2760302201, 5118698747, 7394069397, 5118698747, 5591128730, 5455127123, 5467852442, 1760661757, 5418734048, 5699761395, 5505607906, 5474466362, 5455044470, 5485357770, 3825652990, 5475095829, 5486299064, 2990680594, 5487028039, 5466310340, 5445637029, 5418766186, 3958718774, 5488554643, 5651607265, 5478389762, 5332664305, 5393883394, 2847531955, 2847531955, 2847531955, 2847531955, 2847531955, 2373756044, 7502905490, 5938608356, 7332061173, 1776830283, 5486665471, 5865861038, 3667473314, 2683914181, 5441327790, 2286145972, 1773159472, 6857293657, 3673979643, 3218505965, 2941303747, 2946127137, 2010862577, 5542855564, 2067005103, 5738227348, 3922532522, 7018536555, 7595963154, 2316110774, 6310883271, 1823388293, 6495360847, 5404740726, 2711814793, 2127166007, 2709798593, 7720959983, 2651616020, 2865081670, 3357229252, 3770327644, 3852921560, 3567934973, 5482053051, 5242672519, 5867712178, 6043248622, 2628538863, 2214763564, 3462079094, 6294312701, 3957333707, 2464096494, 5186365382, 5102751528, 3877761295, 5048612464, 5428405600, 2214316322, 3568517225, 3462758980, 5270958707, 6997020831, 3412086190, 2184193343, 1836297985, 2185021562, 2189028430, 2182899397, 2184179413, 2185459583, 2194007497, 2189930867, 2185456537, 2189038102, 2185464053, 1680564187, 5695729065, 2185784680, 2184729175, 2185452843, 3229584057, 5407707188, 1885531527, 7575803567, 7729602011, 7727148208, 7675911015, 7608050302, 7576719611, 7502979197, 5615057465, 6520100166, 1808523312, 3552164111, 3224727895, 3741442237, 6519795374, 5627426644, 5952913608, 7496400875, 6520440134, 3585616873, 6147176033, 6134218880, 2556897124, 6420788107, 6525264451, 3106642541, 3107429685, 7456853499, 5986605708, 5656430595, 2713308341, 2640954147, 3050872521, 2177173995, 1875326175, 1875326175, 2669143347, 2669143347, 7312362801, 5048537502, 1883411740, 6302196133, 1755421273, 2960543972, 2573829880, 6509796913, 3140508293, 6509796913, 2359347854, 2466170102, 2209902967, 2695909160, 6685190904, 2284735697, 5530134220, 2386345451, 6090688912, 2866538512, 5195893770, 5195893770, 3989650834, 5397560192, 3989650834, 2261632212, 3198976357, 2261632212, 3198976357, 5479100147, 3558589443, 1922544954, 2340468804, 2609493002, 7650835228, 7308533025, 1974074411, 5287133285, 3551981787, 3462440620, 1687408032, 3699955683, 3737389712, 3787780807, 2321829914, 3516923342, 2997351592, 3633975101, 1886650090, 3513823134, 1843689357, 3710987650, 2817093004, 2611902402, 5339849826, 3173104651, 3107002897, 5518440374, 5698445302, 6463850644, 2902342060, 6463850644, 6380672544, 2808492293, 5887159498, 1286945794, 2243794974, 1361882355, 6348859808, 2840540342, 7605699829, 6112535190, 2733697970, 1895668724, 1895668724, 1895668724, 5743500858, 6460724064, 1612134157, 5042200072, 2118859714, 2290417792, 3030257737, 2627318262, 2638681880, 3217828507, 5902507919, 3702826941, 5656915965, 3941801363, 1866997213, 5754843626, 5539575737, 5754843626, 3651156284, 5342053129, 5116422055, 2799575964, 2460220130, 6970786907, 6473486612, 3178273737, 7021849034, 6109825523, 5684965011, 2919870803, 2678648720, 3987956514, 3991921719, 5329153941, 3983507158, 6132117569, 2462493490, 2870783997, 2933092714, 2870783997, 2462493490, 1990357580, 5754857590, 7434991875, 7434995400, 6177206136, 6177206136, 3225109191, 5504311757, 2652300753, 5489426132, 7332563292, 2719327843, 2636581383, 2685617923, 1769674345, 2922848244, 5562322383, 2826438783, 7391897552, 3279273470, 2990691472, 2718289463, 2718289463, 5053989216, 2909961634, 5054748248, 5216318459, 7280186590, 5612968464, 2200100952, 6432315232, 6164100622, 6793693753, 7385403114, 3850070574, 6315636554, 5462247005, 5455024199, 3113864033, 5279234332, 5104248913, 5878853069, 5279234332, 7004289862, 3909068338, 3860056812, 2299163722, 6049502648, 5341789770, 3229800040, 3291539284, 3764757644, 1809928591, 6567864294, 7052806968, 5989163364, 5601782196, 1804254291, 5117356069, 3300557152, 1397786427, 3228493834, 3039436615, 5588900600, 2930199661, 1933147961, 2839491052, 2995920322, 5120729604, 7521765997, 6285147440, 5999930133, 5348179381, 5915600516, 3708425654, 5067304239, 1327342077, 3855758612, 3869578450, 3843967057, 3824066307, 1643386091, 2128568457, 3251986254, 5359118314, 5708038873, 5339824571, 5369431951, 3990525027, 5052711033, 5070402095, 5085003902, 5085092741, 5086619457, 5093088520, 5103089223, 5101202009, 5102821143, 5103868867, 5105204095, 5112641949, 5121962184, 5122700062, 5147762022, 5150853927, 5163220108, 5279968723, 5571119992, 5354403550, 3845779712, 2128568457, 5569469512, 5073251766, 6543408452, 5474514615, 5474514615, 3662409453, 2784681520, 5329592963, 2352732500, 2004032743, 3080569315, 2973184723, 3174986527, 2689490431, 2990786722, 2990786722, 1824175690, 5596021382, 2713242457, 5510175160, 5134431812, 3900005443, 5664837098, 2887560572, 6135547729, 2534721557, 2628955191, 2793260392, 2942760990, 2942720282, 2950442692, 2477649770, 5926347679, 5198036422, 5649605479, 1962210667, 1962210667, 2898024102, 2872914954, 2857816000, 2942425390, 7711616012, 6860951374, 3541636917, 3195647243, 2701572834, 6131235004, 5615045716, 6773586050, 6377518491, 1913935964, 3901562528, 3944167508, 1737142740, 1737142740, 2122010701, 2836607053, 2836586607, 2836619233, 6583748604, 2271922871, 2724251611, 3557108354, 3557108354, 6913341471, 1802183327, 5271830175, 5242833264, 7534480467, 5623183614, 5396408660, 3243665170, 5602340549, 6020074778, 2883495367, 3201445874, 5290008861, 2105777571, 5879234316, 6032769481, 3768348990, 5821745146, 5943097996, 2793126361, 5601563378, 3768365030, 3423559262, 5042258015, 2649207135, 3535189480, 3358187962, 5656722485, 5652157624, 6186373446, 6186373446, 5209669530, 5077682335, 3683565394, 5033807860, 2735436073, 5580319749, 2949171120, 2137734815, 2137851427, 5496966930, 3163216615, 3167290561, 1828455535, 2807683212, 6098316490, 5696716667, 2431467694, 6387561141, 7711866859, 3748144747, 5576600110, 3925730949, 3358269220, 6321057850, 2369650614, 3933824839, 3173950141, 7420760222, 2334591610, 3206237570, 6796075148, 3229049955, 5999888788, 2854389607, 5538392410, 2676624371, 2510945392, 2868353580, 5906101612, 5315081416, 5406912308, 5893692860, 2712627093, 6493253790, 6779703184, 5889706694, 6085681256, 6621334819, 1759081553, 5870320378, 1781802394, 2402248953, 6452111196, 5884971020, 5705198279, 6047842847, 6729047323, 5216612271, 2664850105, 5549249741, 5549249741, 1686253095, 2610198153, 1866637004, 2708233602, 3148747853, 2405401765, 2826060450, 6019665064, 2378125511, 2462074014, 3498378764, 2092205552, 2768435721, 2374984990, 3446792462, 6534037939, 7293510306, 1769720457, 1769720457, 5263915505, 7097683621, 3027488693, 2343997162, 2592072422, 1746760032, 5299653424, 2167560063, 5341728484, 5228602039, 6583455085, 6583455085, 1923976897, 3141750261, 3137376551, 2931887655, 5574142122, 5199074792, 2639064711, 5377627002, 5409951196, 3222321920, 1760960387, 1865568653, 2472549457, 3673212312, 6420637413, 5341972492, 3916203035, 2464801572, 5206834011, 2295737597, 5670693762, 1852792121, 3225683044, 3225025341, 6032773728, 3800228695, 5864079358, 7540609148, 3802921755, 3941720207, 2153794503, 1718298877, 1801557490, 7750534551, 5182905653, 2648961233, 2361819260, 5794933693, 5794933693, 3330155060, 1812764917, 2708371074, 1590697142, 6422086556, 5611513732, 6172563854, 6624644513, 5634872494, 3080806683, 2822413472, 5541467293, 7385479681, 2148345724, 7310730889, 7650607828, 5864827245, 5056655273, 2110768894, 2316563523, 3240270802, 2316563523, 5984691836, 3982902790, 5645175342, 5699769464, 5056655273, 2110768894, 2429583781, 3669165643, 1959216762, 6623501645, 6623501645, 2642488433, 2561040051, 2404378992, 5634321327, 5589381522, 2297358582, 6107936013, 2881782262, 3152650255, 6724028460, 6480963612, 6054414988, 5486319790, 5294832879, 6584154237, 5986218684, 2564151581, 5093689959, 3925006166, 5938527513, 3823472917, 5444557260, 3880726352, 5170245330, 2859722850, 3172602751, 5414346950, 2511916890, 7564463204, 6371468634, 2176460860, 2296497950, 5262303789, 5511781978, 5948473291, 2988204911, 3228950642, 6499630442, 3197007800, 2176460860, 3495620420, 3558246197, 7279802534, 2372049180, 2107218441, 5651611495, 3634269454, 2775348841, 5579042322, 5254054863, 5520345786, 5133443821, 5458531189, 2978995540, 2817052292, 2922362874, 6001319783, 2037905517, 5948665964, 6692717965, 2280706442, 3213978314, 3266708657, 1690182184, 3222721200, 6182453297, 7496599973, 7679570861, 3944823062, 5203432738, 5601865686, 2653910994, 6681438177, 3706916941, 2465449110, 1616954460, 3587090871, 2092900103, 6250984436, 2951470177, 2092900103, 6250984436, 2951470177, 2061528832, 2061528832, 2964646690, 1784470365, 3944232347, 2718900981, 3739801035, 5480193428, 2036453222, 5238686098, 2188210361, 2098840485, 5733425147, 3511893201, 2304523221, 1806394591, 2304503845, 2282115205, 2282255395, 3107401651, 2282209821, 1885741814, 2034053862, 2608082372, 2948855360, 2302733902, 2302733902, 2034053862, 2948855360, 2608082372, 5886512065, 2878087934, 2144711551, 3844937504, 3702728727, 2186531975, 3069789567, 6072549777, 6611959645, 1659828622, 1886015067, 5710552407, 2155885967, 2792612694, 1874283441, 3222229260, 7545566060, 2172183042, 3761443024, 1796494104, 2120586803, 1935978447, 5704926064, 6573864229, 5187419980, 7439768408, 3668692724, 1771628002, 5434027126, 6313179608, 3877718933, 7475630844, 6529099723, 2973957963, 7690155234, 3947091185, 3947091185, 2689101453, 2748389300, 1393785612, 3193853742, 7341579702, 2358407562, 2848453313, 2941516452, 5535511463, 7010074485, 2349403282, 7717168962, 3899823385, 2131607030, 2241249682, 2239933453, 6469778674, 7429986863, 2816830272, 6195713220, 3205250964, 2093157997, 3662321811, 5499105919, 5419150955, 3172527540, 3914313051, 5078626551, 5524086747, 2340404212, 1992565512, 6813995575, 5896599075, 6475690602, 5356374712, 5303776255, 6362314256, 6452380353, 6877867089, 3213408771, 3993308004, 2153364852, 5289627188, 3193047843, 2872540072, 5649157768, 5824448353, 2711749273, 2316939714, 2809715537, 5708601747, 6605240991, 7744875432, 5201067733, 5368150678, 5200483380, 5242685634, 2636534524, 2636534524, 5651832787, 3212502427, 2699561984, 3557587102, 5146625657, 2299621870, 3158185134, 7139102034, 5530129473, 6457713386, 2451039652, 6438911372, 5568771261, 5568771261, 5609945690, 6432471770, 3570853192, 5237340328, 5307460089, 2719260183, 5036309008, 2534721814, 2652523681, 3194765572, 2032747457, 3189701515, 6541810172, 6734810654, 7512230592, 5663544565, 2057549315, 2057549315, 2270678261, 1761004027, 1697486122, 5047792086, 3375922902, 7501247774, 1740567781, 7620874687, 6560770115, 5118902526, 3384956670, 5135078486, 5580890147, 2559971200, 6176592931, 5191979078, 3164806923, 5548957489, 6176592931, 6550109431, 3735301034, 1823348853, 6607298631, 7480867067, 7499801117, 5068814460, 5227293163, 5514856685, 5571416536, 5192638320, 5665190364, 7657843797, 1798789365, 3912366317, 7419444085, 7424125496, 6170268138, 7452926107, 1668701490, 1742880694, 7191151825, 7521741276, 6580962954, 6705903697, 2015320893, 7357077610, 5146406794, 6880842078, 6001856728, 5806829334, 5616621338, 5945921267, 5540812946, 5543671799, 5589361107, 2850511284, 3946321036, 3170900777, 5286720226, 2495070870, 2677937391, 5536012246, 2694166204, 2006213732, 5896854354, 2523375380, 2523375380, 2523375380, 5179634360, 6190212420, 3850583739, 3909353988, 3313461523, 2781001971, 3225514563, 3817962751, 2707332497, 6612300250, 7443921106, 1752899641, 2129947237, 5203819871, 5606697429, 5730839406, 7469108888, 3053121424, 5730839406, 5571132049, 2837874485, 3214142434, 2243712552, 2431795744, 1748276683, 2296944113, 6864340629, 6618134425, 3801188793, 5047827999, 6471166525, 5675014800, 7506348704, 2284606510, 3205351981, 7500830426, 1749988497, 3215305500, 3633354957, 2348015734, 2610855911, 2790609550, 2827102914, 3203642394, 1956931152, 7507108279, 5208958319, 5362491180, 3172765174, 3461260914, 7329638811, 2740886145, 3459626784, 5669706624, 1988454287, 7330457792, 1814704313, 3146923157, 5332514488, 6074229840, 7534609393, 2673703733, 3194250657, 3266074624, 5876443306, 1822862863, 2402561721, 5095189308, 5848073472, 6687013402, 6730510171, 5632927122, 5611233615, 7704955928, 2866202030, 2866202030, 3822000979, 5562946394, 5682040132, 7410518563, 2979295981, 2979295981, 3122952711, 3223749821, 2105824034, 2759322337, 2779369532, 5647758660, 3175611202, 3558494537, 3938872203, 3801182616, 2082413983, 5702471696, 2604924574, 2142235403, 1967954793, 7753195248, 7686648695, 5261706033, 2392331834, 7275635455, 2975334972, 5261363027, 6468540945, 2695472184, 7400226056, 7534726112, 3336926980, 7721294673, 5530030826, 1890917142, 6334806106, 7669979182, 7498793024, 7191694522, 5212817824, 7459365008, 6367902609, 6408565113, 7215671553, 6200550772, 5513809292, 5632928249, 5875903134, 5399214751, 5621469066, 7624473199, 6524336007, 5156161569, 3053682701, 7731920785, 1805629163, 3737261813, 5669170887, 5500136063, 3203618710, 1920947444, 2098245463, 2481788941, 1944865034, 2935863095, 1944865034, 7467327140, 7453072998, 5764936385, 6629266291, 7351755727, 3058602742, 3615054352, 7072644412, 2792636132, 7399482943, 2076739092, 1737520324, 5769309261, 6904645943, 6274964973, 6274964973, 3399917164, 3202191481, 3255752247, 3494326885, 7285467648, 3614639585, 2175286600, 6607113648, 6516535277, 2894968930, 6708435299, 5881965939, 2793624734, 2155183824, 2996441160, 6122827176, 5123013368, 6215209543, 1747170114, 7503402381, 2360667832, 5770344947, 6217258971, 5324252604, 5408109239, 2714302591, 5891989770, 5625221387, 5623225817, 2305362310, 5235005805, 3876992302, 5374277222, 7320752930, 5347919963, 1940481002, 7722095224, 6210017583, 2249451585, 3304210482, 5367496832, 5449725511, 3304210482, 5367496832, 5449725511, 7616435266, 5493514279, 5078285746, 3919299771, 6140224941, 2011365673, 7647418362, 5374497358, 2626700471, 6083283905, 3183765125, 2080194393, 5059654054, 2481094277, 5669167789, 5671379329, 2515962115, 5812486066, 3844914711, 3549422260, 1818743744, 1892532610, 5614241251, 1934295297, 5264692898, 7357710821, 2012572483, 6981518419, 5211224727, 1875231583, 3892039918, 2003905565, 1875231583, 6604396323, 6580667144, 2707715883, 5146729055, 6021506797, 6021506797, 6253409613, 5912314889, 7552341935, 1974644911, 5043121481, 1999441145, 2773458421, 2384005224, 3134819130, 3511859871, 5571506138, 7455555644, 7488585681, 6034599262, 3716297944, 2111741691, 3542508800, 7500075772, 3214270770, 3649982944, 2632194263, 2840048627, 3641973700, 3641973700, 2632194263, 2840048627, 2189138004, 5834148061, 6517050559, 7577742165, 2027228514, 2324840931, 1465135185, 2006349412, 1890754312, 1653150224, 1991975152, 6375362184, 6072478686, 1773185505, 3146789722, 2016660567, 5883291480, 7299548922, 1770996052, 2720074542, 2478109874, 7293573223, 2142653411, 2807231527, 3097153485, 3066011811, 1961362610, 2092477712, 2691784512, 7488528469, 2511929820, 1957258370, 2511929820, 5696195347, 5696195347, 2801528271, 2646692005, 2471229533, 1979535124, 1979535124, 3512877500, 7031091560, 2513126082, 3536860362, 3824682490, 2662329323, 2830775584, 2951558060, 3708592564, 3816209200, 1906512695, 7319123967, 6336283633, 6280644662, 6433766651, 6085687022, 2505776215, 2837091371, 5732778599, 5234956121, 3649277330, 2388729080, 2690303253, 5767346759, 7714656389, 3993309948, 2544352433, 2774029785, 5049169658, 5591675634, 2711946611, 1376441730, 2365890762, 2728926630, 2641989934, 2521517894, 2493202064, 3205215304, 1681825262, 1681826554, 1681826735, 2389230343, 2257425990, 2730257414, 1723216305, 2986723420, 2564457834, 2986723420, 1981792621, 3849614076, 5390219202, 2176853320, 3004623212, 3617010394, 2737700332, 2382429753, 5896354700, 5931605019, 5375587369, 6884950239, 5375587369, 5375587369, 1838350895, 1665169124, 3051054183, 2168669013, 6620230922, 5584236400, 2964616874, 3048354633, 5559750954, 3199237524, 2498394572, 3194374034, 3117911573, 1905056282, 5177030293, 2100200200, 5902167553, 2104807790, 7516333210, 7249721456, 7368466644, 1862980964, 5338637897, 2429597977, 2217084165, 2232541571, 2970663125, 3486457344, 6196086492, 5964312962, 2014035852, 2014035852, 2200232764, 2194539053, 7457605437, 5684971054, 1974110250, 2473081741, 2017157695, 5755037758, 7567598285, 2475216144, 2188538905, 5578494981, 3211612107, 5435082117, 2872810465, 3764710125, 5601549641, 3019964531, 5827923014, 2219385922, 2240091610, 2273134350, 2259242152, 2312870900, 2258687444, 2239578817, 2241965750, 6326931570, 2134598834, 2139924793, 3784550053, 5448935385, 7274207156, 5748396700, 5618222535, 2082327723, 5633468981, 2492862170, 2416422844, 2416426242, 3214277373, 3665669071, 2747915087, 1405797250, 1700551531, 1828544205, 3826388732, 2830527402, 6612828476, 3334556020, 2936753584, 2805518570, 3107036523, 3091438021, 5461245193, 2102577270, 3699012670, 3693446122, 5296925486, 2754798672, 7567543709, 2310982320, 1176146555, 2620489157, 3203636060, 3203636060, 5381618825, 2207378367, 5688141155, 3009720251, 3052660485, 3178053877, 2718115622, 2154529147, 6353817345, 5999087811, 7432313133, 1838311773, 5907240523, 3223967192, 2004568612, 3909930353, 1674808834, 7407023449, 2143600545, 6154678937, 2274480212, 2878091982, 5496389198, 7514410734, 3210625993, 3210625993, 3210625993, 2097367431, 6500493733, 5433923618, 5410083752, 2596561391, 1666048491, 3512832804, 2683787783, 6389619024, 7699060394, 2549540684, 2159317127, 7596073713, 6604687227, 1830898040, 5624149127, 1688337755, 5633603200, 2639721550, 5624185740, 6404655739, 5643492188, 5657729803, 3940180203, 5098256934, 3106522591, 2215331585, 5043962707, 5490710954, 1807936260, 5303775580, 3849051261, 2048072790, 3163736370, 3799558123, 2754671911, 3934307595, 3169345597, 3169345597, 2158897721, 5235192542, 7723533306, 7478941166, 7281978639, 1873715220, 3925878035, 2126435101, 5591674636, 3203746002, 5611977510, 5331168460, 5572302573, 2958721425, 2211590043, 2211590043, 2958721425, 3135171184, 3155105517, 3310745664, 5545563182, 3149058614, 1971266091, 1971266091, 1971266091, 5664713124, 5644369442, 2201273033, 1934424957, 2212281921, 2739495497, 5582035335, 5281838720, 5274309965, 2862372204, 3580110857, 2862372204, 5780189351, 2473744067, 2502205183, 2502242777, 2079697977, 2170216702, 2502197277, 2505403945, 1914064893, 1156966871, 3812459090, 1914064893, 2594940940, 5606940364, 5379177178, 1856510800, 1856510800, 5927884251, 2995860780, 2547845303, 3048215167, 3047965691, 3047923911, 3047948331, 3047998753, 2661075943, 3047985987, 7614601005, 2954021492, 2954021492, 2094763280, 7616321415, 1970028913, 5267043728, 3167960267, 2005272870, 5531302666, 3892695528, 2909374992, 7646450796, 2311652410, 7002119857, 7484730728, 2109956587, 2362924693, 5977771867, 2091338033, 3768817155, 3218209683, 3228736347, 3206061783, 3206775255, 3205452691, 3165207345, 5674219449, 5252521580, 2178633250, 2363294930, 3194543572, 3194550740, 2703149837, 5397862427, 7440413364, 2453665353, 2523935150, 2709633052, 6276935320, 2977153772, 5390795339, 5210583586, 1822109487, 3203153444, 3833858066, 6981554558, 6541398017, 6996437875, 5847736212, 5605575359, 2098110412, 1650062344, 2282045150, 2097799372, 2786005352, 2295456327, 2567620304, 2567620304, 2295456327, 7041951960, 6855394980, 5546693542, 3216272991, 3206856685, 5873934021, 7336440567, 6727199906, 6086675877, 3104216955, 2639351165, 5820359927, 5546950189, 7347380445, 7230543753, 5553743185, 7404512875, 1957012732, 2377197252, 2641814521, 2629348141, 3498287750, 5040547301, 2793661030, 1822013784, 1870550855, 1879736664, 2713896690, 1875637535, 1842003087, 2505366060, 2566210883, 2793249040, 7229022867, 5641945524, 5553344898, 5703691563, 1772963420, 6041381224, 1912276373, 2967609077, 2726829321, 2700139612, 5040707368, 3816469392, 1829429022, 3822050732, 5963561854, 3801936998, 7580170944, 2231226450, 1678760767, 5167858918, 6102659543, 2239206790, 5156605985, 5194109219, 3986778169, 5574376216, 1709530122, 3670537835, 6254592526, 1785858197, 2003290583, 5323453602, 1933042555, 1935420581, 1949028264, 2003311787, 2026391993, 2026602277, 2129559897, 2131552181, 2609208723, 2694233487, 2695234993, 2704189011, 2705474915, 2713552437, 2003983151, 2806571912, 7307117323, 2295991671, 1741649093, 5327929228, 3578499254, 5405803276, 5121309753, 6298309170, 3231585264, 3358727302, 7467367146, 5239996199, 5240076353, 7283323624, 6929937600, 6606252079, 1945920104, 2137077665, 6097944574, 3805743016, 2210057511, 5126145678, 2477881202, 5648197225, 5648197225, 5648197225, 7443691765, 7334081623, 3518348697, 5112322764, 5112043558, 6249404404, 3204649743, 7431768425, 5504284051, 2044294590, 2130123987, 5727851640, 2372918482, 6655180863, 5894406597, 2911235684, 3582003857, 2709848083, 5935869261, 1729451425, 2710285214, 1059686545, 1259242664, 3057259221, 5698524554, 2610572551, 3274680774, 2101644272, 2130099902, 2088852555, 2088852555, 2671585323, 2671585323, 2132310967, 3204874180, 5762634482, 2115391222, 2079941155, 5553615638, 6135169946, 2038679162, 6157284109, 5890555464, 5678485738, 5833474116, 2699789122, 2004712303, 5724936411, 7687507014, 5241226182, 7489212526, 6918811545, 3275322994, 2972349730, 1910570284, 5573669001, 5281824854, 7567702557, 1999319542, 5245117290, 2626172813, 2885697350, 5245117290, 6386086826, 2694819501, 7723655801, 3852889432, 3853215792, 5820269091, 2036484930, 2036484930, 3146598147, 3825386757, 2708166922, 3498400290, 2710632464, 5365437353, 3096194755, 2759930833, 3170068974, 2759930833, 3170068974, 3096194755, 6267568322, 2739205695, 2935968902, 5453841837, 2801047074, 2719740261, 3161520174, 3161520174, 6060029777, 6342655602, 6342655602, 2097951714, 5066283409, 3106066073, 3539160757, 2282052454, 2332128252, 2501245253, 2817046204, 7182810217, 2034146020, 2593678174, 1909890244, 5876552325, 5077341673, 2806376854, 5248261429, 1729013651, 2654187800, 2625330385, 3405836142, 3562407224, 2654179110, 2654228812, 2653628130, 2718370160, 2654187600, 2654189800, 2654091144, 2653809954, 2654150440, 7311870794, 2653928214, 2653816030, 2653768964, 7002736942, 2622602854, 2072785721, 6624625921, 6624625921, 7015918591, 6437981888, 2663989641, 2094983435, 5310236602, 5098849159, 3790530537, 2565071167, 5107374700, 2150672052, 2267547633, 1167323425, 2255722561, 1958445594, 2696038891, 7707402019, 5222026235, 2108118473, 6868045930, 2108810225, 6215413462, 7501287343, 6215413462, 7036588050, 1769084771, 5913574490, 6991642909, 6121759308, 2360878517, 2160328381, 5913574490, 5236823068, 5821738741, 7002062855, 7002062855, 5821738741, 3217852464, 2805073870, 2805073870, 2038844100, 2788299367, 6115474883, 7645089657, 3572522170, 6626570687, 2315762592, 2315762592, 2315762592, 2315762592, 5713603509, 2284469832, 2165790314, 5977567792, 2625030583, 5657185637, 6313045708, 1895409201, 5297135615, 5292061159, 7511791073, 3227097295, 1730799947, 3170368603, 5561343259, 6088233573, 1730799947, 5829711010, 1885890223, 2096779810, 2571764082, 2638959022, 5035963810, 3187610797, 2622097235, 5889505040, 2622097235, 3660050441, 6021958254, 5874901998, 7215326249, 6297903196, 3487299015, 6008668629, 5545801843, 2337672413, 2269517065, 2337672413, 2337672413, 3225140700, 3225113254, 6906673205, 2831627474, 2729214644, 2494429024, 2240035174, 3511365780, 5547977692, 6341710737, 3212750340, 1743756202, 1751717230, 6475684251, 6535803153, 6629107401, 5067898827, 2167199754, 5369291418, 2137599207, 2885476242, 1647850037, 2256029814, 2475885684, 7507344439, 7517754222, 5643894841, 7433062688, 7506242169, 7669828072, 3471687942, 7540079477, 5650802348, 1929023895, 2830725997, 1928962462, 2606627007, 2729695145, 6361449444, 2975548310, 5690994310, 3945884118, 7624897098, 2606283430, 6158564385, 2712119302, 3982502184, 7475611669, 7744196028, 1900445204, 5967189123, 5367256766, 3341280702, 7425921278, 1940411570, 1919081600, 3237815304, 5036329499, 5217998919, 2187349864, 2058569872, 2773460032, 2129169250, 2385304237, 2384661045, 2050271603, 5888489004, 3207807404, 2962972110, 5182545689, 2727339415, 2705488937, 5182545689, 3506462061, 5147314578, 2464794553, 1775158187, 3177945130, 5599893262, 2919538477, 5622072771, 3933343208, 3283360417, 5171351779, 3744430010, 5066015435, 5250361527, 3129551923, 5250361527, 5066015435, 3129551923, 3066452263, 1650507560, 2248769664, 5884291885, 1896108780, 5184374875, 1984213677, 5175751693, 2116495934, 2100521990, 2116515894, 6760877342, 2731109625, 2861164821, 3366988054, 1734599330, 2677021893, 2762744150, 6525567726, 2260018447, 5341520560, 5132862451, 7743661663, 3647435023, 3167927993, 3174534180, 5655345262, 1678194810, 5140823950, 5077018756, 3546063413, 2710485221, 6167719405, 3028553427, 2090137634, 6147207622, 5634600641, 2937207114, 2937207114, 3427697930, 2573164190, 6233028460, 6562095694, 2426590685, 3799148465, 7588441852, 6513236032, 2096213413, 2096429157, 1730276312, 2096071737, 3213302683, 5057653465, 5057653465, 2938595333, 5058325896, 2298861502, 2948530357, 3653843642, 5201819939, 6505869401, 2972530083, 2060352104, 1840067451, 1840067451, 2050736113, 1840067451, 3887966172, 3887966172, 3887966172, 3887966172, 1638776085, 2814569013, 2903713795, 7705877220, 7587024683, 5919361662, 5946607838, 5894557680, 2823807551, 5569951527, 2960470414, 2960470414, 7721875407, 2355685052, 2559458972, 2175198555, 3326333852, 7539230158, 1764536032, 7073732522, 3170375607, 3171317592, 2939464627, 3486054517, 3912086680, 1867188642, 2076712595, 2168124624, 2297725417, 2310423704, 2306167955, 5995654573, 2310423704, 3819655769, 2368318665, 2297643567, 2240387492, 2922911083, 2116938280, 2401449264, 2255217413, 2307490335, 2409258332, 2255138805, 2397404010, 2273810320, 2248209604, 2287972450, 2624208747, 2539964981, 2246719802, 2459805920, 2494493074, 2280328780, 2279794240, 2295108854, 2248158984, 7455378113, 2315992063, 2293586223, 2653564802, 2166096931, 2359371447, 2247558697, 2497107061, 2283498030, 2604609304, 2284235075, 2650116405, 1698631892, 2923651221, 3225838575, 1735766697, 2411429764, 3629096270, 2647497301, 2915361753, 3246616982, 3568078420, 3914203814, 7166050528, 5040318487, 1857757530, 2099411502, 2961462557, 1404671423, 1944690590, 1989024195, 1912116361, 2057035227, 2121617215, 2097066400, 7476791250, 3180176535, 5884956159, 3232941182, 2358519290, 1769784332, 5078179296, 5149615864, 5079419459, 5142273951, 5084154775, 1982652331, 5083130519, 2287007137, 3551946770, 3551946770, 7684076483, 1764720652, 5752510628, 3327443650, 3080613860, 1999558963, 3617198981, 7637526619, 7494353692, 3936905839, 3927772456, 1927391347, 1906165234, 6700613967, 1899569433, 1899291447, 1900153712, 1905983321, 1889468352, 2132110495, 1900011450, 2106330532, 1018273844, 1877898777, 1887715377, 1898906582, 1898044774, 1898822863, 1899701137, 1899539855, 1900381794, 1899890831, 1901811872, 2057134213, 2410401555, 1878172393, 1898280157, 1899879751, 3214164182, 1897853375, 1900505881, 1883826641, 1905623155, 1907002553, 1890937202, 1803278047, 1944729332, 7239747130, 7326497766, 7239747130, 2724877607, 1736292551, 2242603603, 1819782233, 2261459980, 2260304797, 2262720055, 1866101447, 6159424727, 6159424727, 2687276083, 2687276083, 5217245096, 2099150487, 2028794171, 2344875291, 2369697037, 2179623947, 1683484344, 2641504365, 5469349889, 3206845764, 7127906744, 2810050402, 2106817257, 2774731397, 7455554529, 3460307084, 5465296398, 6314332180, 6177505132, 7011667425, 5884553365, 2206146634, 3466931314, 5183545882, 3200838003, 3195520463, 1970149674, 3166705165, 2949877242, 2455790560, 2455325054, 2455426714, 2402894213, 2403211833, 2403178913, 2403055203, 2402780205, 2455169314, 2455674350, 2402132715, 2455373084, 2455781770, 2455026202, 2402365855, 2403320637, 2455678090, 2455618172, 2455763124, 2455990582, 2455346074, 2455445490, 3628818870, 2402168501, 2403080397, 2455644830, 2402848323, 2402780855, 1908971630, 2455351670, 2150883590, 2455922174, 2454992520, 2402191711, 2455609620, 2402607765, 2403115103, 2141634535, 2455661272, 2403435453, 1933041385, 1964171395, 2455337344, 2013048290, 5999720637, 5294870079, 3948032369, 6553436127, 1905085511, 2783648690, 6250832223, 5189984980, 3809864661, 3030645775, 2671197714, 2100919873, 2100919873, 6638935562, 7498934988, 5977353032, 1502312302, 2082987771, 2160898343, 2243829300, 7330805814, 2958904610, 1726915750, 5102442350, 7738377434, 6523278315, 2115256272, 2115256272, 6823222868, 6837123587, 3091432537, 6837123913, 7411553066, 1759297263, 3930455184, 2296313281, 5703775048, 5504433980, 5562766077, 3569871067, 2804428570, 2258759544, 6351159505, 5955302990, 2667958710, 2258759544, 5955302990, 2258759544, 6351159505, 5377142841, 2581442670, 3962419422, 7583198837, 2690954060, 2638359204, 3735132853, 6751124625, 1989860137, 1985686985, 1961254430, 1990201205, 1987034795, 1961249630, 1961236752, 1735153104, 3899748867, 2854198752, 5345237556, 3582000840, 6851894881, 3955347469, 6519405912, 2779385392, 2871387544, 2344153620, 2205422452, 5262474879, 2654205761, 3752997981, 6557572819, 2767665562, 1905774980, 7213734463, 3347983740, 3876324378, 7726934318, 2173747130, 2173747130, 2132236243, 1646751053, 5074429522, 3274785034, 1832624440, 3430430734, 5493289988, 6468717200, 1832624440, 3217314175, 2761012084, 2296574600, 6473472876, 2975468310, 1894866867, 1872201124, 1936549352, 2206073544, 2034038120, 5498653174, 6591840977, 7515115492, 2043919712, 6340444081, 5599235277, 5050474085, 3251471320, 3250223914, 3280453350, 3276486614, 3250399774, 3239899972, 3274216700, 3272659074, 3311919470, 3251414990, 3272781282, 3250988394, 2243567872, 2832438597, 3243921450, 3239750632, 3241979844, 3252161900, 3250837242, 3250929234, 3251985484, 3250361382, 3250416910, 3251090010, 3272522882, 3272564034, 3277626800, 3272439072, 3276376810, 3280722124, 3277767924, 3274162460, 3272933762, 3274313072, 3277499984, 3277862460, 3277819004, 3280962704, 3280806872, 3281860140, 3281043540, 3281113000, 3310010940, 3311087702, 2015340377, 6604321370, 7569670558, 3925240726, 7593510802, 6563851210, 6108314449, 6242894586, 3714119823, 5871791622, 7267303679, 3298215591, 5261317080, 6244945052, 1771125683, 6401455981, 5733062007, 6094893250, 5869838072, 5541493098, 3189410301, 5931357688, 7296320015, 2758836954, 6844324685, 7619992758, 3202642311, 3201379823, 5049950017, 2518153920, 5907445023, 2430846064, 3725466410, 2286639420, 2783062910, 2644378302, 5353749791, 7298339799, 7502141876, 7031638849, 7376332067, 5930235304, 5347740490, 2894531031, 2455754844, 5253041006, 3195635520, 6215195092, 2806833512, 2309169217, 5508647440, 3265208544, 3172571211, 1738720884, 3113996705, 2721954342, 6611858965, 2133807570, 6637493516, 6611858965, 5126648168, 1847412660, 3610066471, 3279259474, 5130810725, 1664189844, 2654430373, 2097805992, 7526249027, 2852887355, 3425640060, 2341783814, 7741273881, 2952678114, 1871099063, 2973545614, 3880488739, 2951088012, 3096126237, 2396923854, 3408312170, 3408312170, 5286133028, 1839587655, 2872510640, 2872549454, 2872492912, 2865429362, 2941549250, 5530066377, 2133045871, 5289356896, 2729562351, 2371488733, 1828520181, 2514613723, 2712906541, 1835233193, 2137127963, 2820535833, 3047397865, 3167742055, 2137127963, 2820535833, 3047397865, 3197804725, 6620775403, 7099213851, 1744205384, 2805892702, 2620063073, 6994984421, 6366329925, 7629602032, 6233420331, 3193198157, 6049531778, 2636402061, 7569646693, 6568459599, 5598495462, 7014902647, 7492956451, 7493898836, 2841740134, 3603348783, 5772966047, 5564308634, 1958859084, 5142004166, 5132934796, 2031550877, 7121157286, 5702845461, 5063661011, 7556834482, 1769926317, 2169041975, 7435152049, 2608305191, 5199712742, 1947302390, 5517760248, 7459508462, 5361730967, 2107177911, 3675752922, 1787415513, 1938835517, 2050611444, 6304970631, 2992819773, 1912366631, 3633303562, 6315569832, 5876576820, 2242569192, 2385455373, 3559980807, 3786234273, 2668218951, 7620494830, 7514440366, 5067821478, 2718812014, 3577079941, 5067824147, 2245646292, 7503326656, 6222569861, 2792667432, 3754159394, 3754151754, 3701549713, 3162449840, 3812984032, 6123189663, 7461439904, 5643645674, 7722523227, 5880338570, 5529928750, 1829456205, 2403373977, 5120490345, 2832700860, 6517048463, 3754806002, 7526787387, 2094683030, 5504451172, 2094655804, 2094655804, 5836695391, 2719327451, 3950503735, 5835732436, 5837397881, 2094664670, 2094655804, 5504509531, 7686351867, 2772730762, 2772730762, 2466020272, 2823627492, 2283837230, 2614266061, 3766783031, 3766783031, 2609030064, 2618348993, 5568747591, 5881990356, 5099326877, 5099326877, 5255527053, 3217006617, 1929827143, 2490380623, 6062055465, 2910562854, 7720328654, 7752438910, 7557387560, 7462279903, 1906334603, 2373608053, 2408090437, 6059154121, 6059154121, 6059157019, 3188087395, 5206666265, 5165388765, 2344066500, 7458700491, 6537163962, 6525019153, 6524650238, 6525309876, 6227327020, 6536473707, 6536379432, 6535539345, 2597724970, 7724108080, 7170613598, 5340946519, 1713746081, 5340947130, 2977477211, 7484556729, 7435736338, 6611523124, 5327042057, 5031368134, 5478350194, 6064272203, 6431114304, 1867262833, 1990005687, 2296747675, 2482203097, 5934463568, 1800659263, 1867700255, 1880725332, 2602732211, 1888637023, 2602732211, 1770920725, 5075033684, 1770920725, 3869113118, 1770920725, 2774836445, 5075033684, 2212578723, 2094085224, 5650700463, 6004227188, 7624903226, 1715489375, 3174609810, 5388701910, 5587855035, 7368188013, 5649946936, 6685270864, 2014254514, 3240780774, 2548691997, 2807016841, 2044418493, 1738731745, 2712897447, 3204128474, 3429057954, 7747565760, 2978934074, 2853989232, 2003318665, 6066551608, 6126637908, 2519148590, 2527714012, 2514789790, 6557995930, 2013815962, 5306531207, 5883190066, 6033264838, 5419699048, 2093706613, 1658876261, 5588774018, 6931206689, 5504255649, 7581527991, 2625017245, 6648370015, 1805119752, 2682663901, 7215418774, 6393802022, 3945110755, 2682663901, 2616024665, 2669746752, 3719111320, 3719111320, 3188701057, 3676723382, 2886258714, 1889702180, 3292749953, 1889702180, 2043174307, 2043174307, 5669935523, 7467606506, 3340283052, 5426536278, 2189171950, 5467550211, 1732879825, 1732879825, 5467550211, 2189171950, 7746914558, 7330142220, 7432914201, 5546814868, 5640855764, 3011239141, 2129970343, 3539321247, 3811316104, 6584148708, 6213343392, 6196482203, 1905122740, 1905136044, 6584148708, 2605653905, 1962997085, 2960469700, 3824183079, 3216735404, 2753760763, 2313726862, 3231610330, 3769327450, 3926919780, 2619380344, 3204817594, 2355290632, 6352943573, 1960514070, 2112151410, 7499023922, 3480491991, 2463923424, 3516182381, 3513894531, 1960514070, 2418729112, 2463961772, 5537311463, 3615157644, 5840543822, 5303343487, 7515267299, 1824545322, 2697394722, 5994884143, 3230635922, 3867678257, 2320250907, 5685904689, 3867678257, 3160836794, 3160836794, 2133524444, 3094213541, 5898101920, 6552156271, 3728218744, 5507376276, 7499123909, 6251558378, 6053013836, 3072298065, 3690140151, 5184576624, 3838387208, 2403053465, 5371069638, 6901717370, 3474246120, 7442451432, 3199407687, 7483504148, 2859979624, 1974475265, 2848424020, 5546967738, 7635776184, 2761844783, 2771486760, 2771491652, 2682264135, 2771461202, 2680930197, 2771481430, 2712970897, 2771403124, 2771473444, 2771419182, 2682215085, 2771470402, 2454078870, 2714314425, 2761206393, 2771408082, 2680843827, 2771393434, 2771459524, 2771387614, 2783358261, 3018771417, 3008065743, 3008077203, 3015822585, 3010824995, 5504424000, 2771406614, 2682238645, 2758027057, 3010837655, 2782337013, 2771485132, 2757921633, 2680851817, 2682244975, 2771464512, 2771397200, 2682187895, 2757980297, 2758007337, 3010774215, 2771410800, 2680887587, 2301480224, 6073747676, 5570856068, 3198222632, 3776807380, 2949135982, 3143855120, 2813025235, 2280465310, 3147965184, 3196734055, 1822103784, 5286757826, 5871757049, 5175768727, 5392279690, 3105884452, 5069402113, 5657725097, 5834726791, 3195326911, 5410856464, 3821744929, 5786273969, 5644853156, 5889615991, 5268954016, 5981557747, 2784705793, 1921067124, 2868510182, 5408367943, 3217872937, 5973213307, 5897613201, 5385429990, 2949135982, 2178727964, 2274478902, 7691451846, 7616496494, 7623900238, 2654661964, 3480582985, 3512919853, 3460516550, 1770633440, 3196401173, 3461625614, 2710374363, 2131326063, 3460230800, 5262165709, 3517513973, 6152243766, 5380871788, 1818470970, 2852360491, 2710044061, 3570665063, 7578861826, 7583279570, 7582029184, 3547917144, 6551274089, 2817099392, 6107928893, 5137675881, 5269471262, 6233418526, 1906153244, 3109495925, 2801892100, 3085453962, 7764883417, 1747365955, 6414364100, 1770936282, 1770936282, 6568252752, 3891773478, 7418387179, 3891773478, 3081895590, 6343646757, 7072883319, 7072883319, 7726531081, 7312476493, 3481045975, 6432789566, 5538510608, 3697215651, 5870166150, 5821731191, 2663665253, 3768325321, 5150282622, 2039682481, 5405618343, 5490324122, 5902813225, 2593212084, 5305462060, 7356332004, 2049740263, 6520050401, 1958277871, 5647662917, 3547946141, 7594742251, 5506674082, 2106386061, 7549293494, 5698510950, 7273486667, 3880823953, 6481756868, 7046627012, 2049771057, 5467006280, 2504566083, 7410073968, 7320110132, 3116842215, 5881647288, 2880391791, 5475436941, 5944498415, 7316944682, 7639112889, 5504475958, 5616990687, 5323448249, 3368201924, 3262442414, 5411457254, 3094927215, 2316838401, 2147404721, 5580630575, 3195506970, 5655364803, 2080668003, 7317086521, 2820906157, 3918737315, 5045753736, 7011440361, 5872708965, 5042203116, 5307698859, 7401488150, 3213007383, 3655142745, 3655142745, 2678459111, 7683404207, 1747817850, 5617890577, 3048292807, 5815566503, 1968046123, 1968046123, 5815566503, 5184592751, 3202694265, 5170954962, 3205984720, 5235783283, 7734857508, 7005317745, 3462404802, 2766276773, 3157031621, 5562561396, 3118954887, 7327229937, 5405384405, 2669574121, 2608314951, 1911875400, 3198056700, 7685003722, 3315296480, 6387421222, 3498315075, 5149872493, 1919814331, 5721142943, 2610558147, 5975466024, 6003479221, 5200482350, 6550829106, 3229149677, 3229149677, 5190807523, 6857237986, 5128179203, 3655520877, 3047867705, 3769368692, 3218601193, 6837788690, 6823563210, 6769163826, 2810734707, 5280451164, 7687954379, 5529929764, 5574727576, 5606830873, 5242020050, 3046154347, 1721739114, 3843641811, 5135393457, 2655884061, 5321511754, 6493210031, 7605619087, 3525116024, 5828074536, 3846401733, 6383385613, 1627081404, 6205686365, 2746053917, 3193616272, 2162161881, 6449226669, 5647622802, 5493270225, 5785693941, 3535292295, 5919799156, 3228092272, 5490377669, 3563234355, 7717822582, 2561717641, 2695097801, 5483487105, 6283879506, 2334217861, 3166099641, 5587109807, 3879578055, 1870211913, 7529234620, 3225455353, 3247681032, 5753916482, 5515315831, 3206792311, 2306976780, 3772295791, 5184427285, 7488491920, 7652256006, 7652258065, 7266551299, 7646066423, 2141775341, 6547240587, 2825061414, 6270119462, 6058827135, 2685565573, 2305156987, 2694109677, 2484816851, 2241829257, 2642668583, 2410852311, 2833011440, 2612545665, 2685920143, 2823709062, 2832045104, 1440740597, 1750265681, 1838255740, 2100156652, 2116960390, 2141850567, 2136051484, 2556031344, 2685957931, 2684667353, 2684620711, 2685275973, 2703145923, 2704315905, 2747716520, 2776161963, 2832006152, 2910285904, 5704854263, 3898318460, 5612079568, 6996888126, 6361184306, 3443794292, 3443794292, 5529987836, 2861049314, 7492805254, 5303400169, 5303400169, 1846994611, 5497298651, 6518936602, 2357982697, 1660437413, 1803901827, 2868310250, 2736680621, 2868310250, 2736680621, 7405423173, 5073068493, 1757545555, 3280468930, 3280526274, 2142065763, 3512226324, 5787329641, 5622062060, 6426649663, 6500815503, 2154309151, 5310916989, 2596505910, 3519022455, 5623892424, 3481197561, 6315873669, 7028477756, 5184597186, 5460627000, 5746861153, 5560388410, 3093433892, 5548532804, 5375769596, 5148962455, 5147128719, 5148903764, 5148726285, 6336714754, 7623892147, 5165549449, 2622382834, 5649053836, 7627896189, 6422102704, 3899749521, 5172781870, 2628465341, 7011435091, 5592619217, 3213797310, 3175991017, 3179002353, 3295011421, 2791598070, 7452995416, 3967708439, 3572393402, 7714858954, 3916204323, 3911924349, 3178158010, 7710471511, 7714055356, 5377639357, 6409843666, 5541657953, 5474500823, 3881632071, 7072843470, 2809269782, 3047628293, 2747757905, 2254439512, 2809269782, 1900516685, 5829164420, 2800831482, 1990590827, 5619406065, 6210954458, 6510864723, 7270745379, 5198615611, 7320490502]
    for i in range(70, len(id_list)):
        WeiboUserScrapy(user_id=id_list[i], filter=0, download_img=False)
