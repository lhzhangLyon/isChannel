# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Name : driver_common.py
Description: 提取主列表xpath (列表元素需基于<a>)
Author: lhzhang.Lyon
Date: '2018/6/5' '16:12'
"""

import sys
import logging
import Levenshtein
from driver_common import chrome_option
from lxml import etree
from itertools import combinations
import re
import traceback
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                )


# 判断是否频道页
class ChannelJudge(object):
    def __init__(self, driver, policyid):
        """
        初始化操作，详细见注释
        """        
        # 浏览器大小控制
        ### NOTE: 某些阿里云最大宽度只能设置到1024 高度768
        self.__driverWidth = 1500
        self.__driverHeight = 1000

        # 列表中最小元素数量
        ### NOTE: 最好设置为大于等于三，不然会有误判以及对双列表识别不友好
        self.__minElesInList = 3

        # 一些阈值设置(可自行修改)
        self.__linkTextDensity = 0.06 # 链接文本占父节点总文本的比重
        self.__mianViewRange_more_x = [2/8.0, 6/8.0] # 链接 “更多” 出现在xzhou这个范围内被认为中央区域寒含有更多
        self.__standardTitleLength = 12 # 标准标题长度
        self.__standardTitleDensity = 0.2 # 标准标题密度


        # 页面属性
        self.__pageWidth = 0
        self.__pageHalfWidth = 0
        self.__pageHeight = 0
        self.__pageHalfHeight = 0
        self.__listPosMaxY = 960  # 列表最大起始位置
        self.__pageWidthJs = 'return document.body.scrollWidth;'
        self.__pageHeightJs = 'return document.body.scrollHeight;'

        # 浏览器初始化
        self.driver = driver
        
        # 日志系统初始化
        self.LOG = logging

        # 中央区域是否含有更多，以及更多数量的判断
        self.__return_more = False
        self.more_in_center = False
        self.more_in_center_num = 0
        self.more_in_center_link = ''

        # 实际链接在页面中的范围
        self.real_link_top = 0
        self.real_link_botton = 0
        self.real_link_left = 0
        self.real_link_right = 0

        # 规则定义
        # 翻页判断正则
        self.next_page_re = re.compile(r'^\s*(»下一页|第一页|<<|>>|<|>|尾页|上页|下页|\[?下 页\]?|下 页|\[?上一页\]?|'
                                       r'\[?下一页\]?|前页|后页|前一页|后一页|\[?尾页\]?|最?末页|前一天|后一天|'
                                       r'r<<上一页|下一页>>|&lt;&lt;|上一页|下一页&gt;&gt;|&lt;前页|后页&gt;|Next|末页)\s*$'
                                       , re.I)
 
        # 锚文本黑名单
        self.Black = [
            u"跳转", u"内容区域", u"查询", u"^第一编", u"^第二编", u"^第三编",
            u"^第一章", u"^第二章", u"^第三章", u"^第四章", u"^第五章", u"^第六章", u"^第七章",
            u"^第八章", u"^第九章", u"^第十章",u"关于我们",u"联系我们",u"版权说明",u"关于本站",u"网站地图",u"返回首页",
            u"意见反馈",u"设为首页",u"加入收藏",u"^陕公网安备","设为首页","加入收藏","下载附件"
        ]
        self.anchor_black_regx = re.compile(r'%s' % ("|".join(self.Black)), re.I)

        # 更多相关样式
        self.more = [u"^更多", u"更多.*", "more", u"更 多", "MORE", u"更多>"]
        self.more_regx = re.compile(r'%s' % ("|".join(self.more)), re.I)

        # 列表时间特征
        self.__postFeaturesRegex4 = re.compile(r'\d{1,2}(-|/|\.)\d{1,2}|(((?<!\d)\d{4}|(?<!\d)\d{2})(-|/|\.)\d{1,2}\3\d{1,2}\b([\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?)?)|(\d{1,2}(-|/|\.)\d{1,2}\b[\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?)|(((\d{4}|\d{2})年)?\d{1,2}月\d{1,2}日([\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?)?)|(\d{1,2}日[\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?)|(^[\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?[\s\xa0]*$)|(\d{2}-\d{2}[\s\xa0]+\d{2}-\d{2})|(^[\s\xa0]*[\(\[]?[\s\xa0]*\d{2}(-|/)\d{2}[\s\xa0]*[\)\]]?[\s\xa0]*$)|(\d{1,2}[\s\xa0]*(小时|分钟|秒)前)|((今天|昨天)[\s\xa0]*\d{1,2}:\d{1,2}(:\d{1,2})?)|(^(刚刚|昨天)$)',
            re.I)
        
        # url黑名单
        self.__urlBlack = ["Show!detail.action?", "/detail.action?", "detail.action?docId", "/linkFriend", "/AricleDetail", "/ArticleDetail.",
            "/detail/", "/detail.", "/NewsDetail.", "/IndexDetail.", "/InfoDetail."
        ]
    
    def purification(self, text):
        """
        去除字符串中空白字符
        """
        return re.sub(r'\s','',text)

    def getPage_property_after_request(self):
        """
        获得和设置页面宽度等属性
        """
        try:
            self.__pageWidth = int(self.driver.execute_script(self.__pageWidthJs))
        except:
            self.__pageWidth = 0

        self.__pageWidth = self.__driverWidth if self.__pageWidth < self.__driverWidth else self.__pageWidth
        self.__pageHalfWidth = self.__pageWidth / 2

        try:
            self.__bodypageHeight = int(self.driver.execute_script(self.__pageHeightJs))
        except:
            self.__bodypageHeight = 0
        self.__pageHeight = self.__driverHeight

        if self.__bodypageHeight == 0:
            self.__pageHalfHeight = self.__pageHeight / 2
        else:
            self.__pageHalfHeight = self.__bodypageHeight / 2
        try:
            self.driver.set_window_size(self.__pageWidth, self.__pageHeight)
        except:
            self.LOG.error(u"Failed to initialize browser size")
            self.LOG.error(traceback.format_exc())

    def a_anchor_text_length(self, xpath):
        """
        获取页面中所有<a>文本长度的和
        """
        length = 0
        content = self.driver.find_elements_by_xpath(xpath + "//a")
        for item in content:
            length += len(item.text)
        return length

    def anchor_text_proportion(self, item):
        """
        锚文本占父节点下文本比例
        :return:
        """
        content = self.driver.find_element_by_xpath(item)
        total_text_length = len(content.text)
        a_anchor_text = self.a_anchor_text_length(item)
        try:
            self.LOG.info("anchor_text_proportion: {}".format(float(a_anchor_text) / float(total_text_length)))
            if float(a_anchor_text) / float(total_text_length) >= self.__linkTextDensity:
                return True
            else:
                return False
        except:
            self.LOG.error("float(a_anchor_text) / float(total_text_length) something wrong")
            return False


    def get_father_xpath_two(self, xpath1, xpath2):
        """
        计算两个xpath的最大父节点
        :param xpath1:
        :param xpath2:
        :return:
        """
        res = []
        for idx in range(min(len(xpath1.split("/")), len(xpath2.split("/")))):
            if xpath1.split("/")[idx] == xpath2.split("/")[idx]:
                res.append(xpath1.split("/")[idx])
            else:
                break
        return "/".join(res)

    def get_father_xpath(self, xpaths):
        """
        提取xpath列表的最大父节点
        :param xpaths: 
        :return:
        """
        if len(xpaths) == 1:
            return xpaths[0]
        new = self.get_father_xpath_two(xpaths.pop(),xpaths.pop())
        xpaths.append(new)
        return self.get_father_xpath(xpaths)

    def check_one_Block(self, num_list):
        """
        判断需要提取父节点的元素是否在同一block中
        """
        # self.LOG.info(u"Determine if the extracted elements are in the same block")
        if len(num_list) != self.__minElesInList:
            return False
        if len(set([len(x) for x in num_list])) != 1:
            return False

        # 每两个xpath间不同的层级有且只能有一个
        deff_num = []
        check_point = []
        for idx in range(len(num_list) - 1):
            tmp = 0
            for jdx in range(len(num_list[0])):
                if num_list[idx][jdx] != num_list[idx+1][jdx]:
                    tmp += 1
                    check_point.append(jdx)
            deff_num.append(tmp)
        if len(set(check_point)) == 1 and len(set(deff_num)) == 1 and 1 in set(deff_num):
            return True
        else:
            return False


    def get_list_father_xpath(self, links):
        """
        :return: 是否为同一列表, 最大父节点xpath
        """
        xpath_list = [x[1] for x in links]
        xpath_list_without_num = [re.sub(r"\d", "", x) for x in xpath_list]
        num_list = [re.findall(r'\d+',x) for x in xpath_list]

        if len(set(xpath_list_without_num)) != 1:
            return False, ""

        is_one_block = self.check_one_Block(num_list)

        if not is_one_block:
            return False, ""

        if is_one_block:
            father = self.get_father_xpath(xpath_list)
            try:
                father_location_x = self.driver.find_element_by_xpath(father).location["x"]
            except:
                self.LOG.error("Can not find the list location")
                self.LOG.error(traceback.format_exc())
                return False, ""

        # 获取元素X坐标
        xpath_location_x = []
        for xpath in xpath_list:
            try:
                xpath_location_x.append(self.driver.find_element_by_xpath(xpath).location["x"])
            except:
                self.LOG.error("{}: {}无法正常定位该xpath".format(self.driver.current_url, xpath))
    
        diff_x = (max(xpath_location_x) - min(xpath_location_x)) if len(xpath_location_x) > 0 else 0

        # 判断元素位置信息
        if xpath_location_x and is_one_block and (diff_x < 100 or diff_x > 350) and diff_x < 800 \
                      and ((min(xpath_location_x) - self.real_link_left) < (4/8.0)*(self.__pageWidth) or (father_location_x - self.real_link_left < (4/8.0)*(self.__pageWidth))):
            return True, father
        else:
            return False,""

    def get_father_element(self, Ele_list):
        """
        适用于函数clean_links_Ele 格式化 不要在意
        """
        cala = []
        for elem in Ele_list:
            cala.append(elem[1])
        result_xpath = self.get_father_xpath(cala)
        return (Ele_list[0][0], result_xpath, Ele_list[0][2], Ele_list[0][3])

    def check_location_y(self, xpath, start, end):
        """
        校验xpath元素x坐标在不在范围内
        :param xpath:
        :param start:
        :param end:
        :return: bool
        """
        try:
            content = self.driver.find_element_by_xpath(xpath)
            if (start*self.__pageHeight <= content.location['y'] < end*self.__pageHeight):
                return True
            else:
                return False
        except:
            self.LOG.error("{}:{}无法找到该xpath".format(self.driver.current_url, xpath))

    def check_location_x(self, content, start, end):
        """
        校验元素x坐标在不在范围内
        :param xpath:
        :param start:
        :param end:
        :return: bool
        """
        try:
            # content = self.driver.find_element_by_xpath(xpath)
            if (start*self.__pageWidth <= content.location['x'] < end*self.__pageWidth):
                return True
            else:
                return False
        except:
            self.LOG.error("{}无法找到该xpath".format(self.driver.current_url))

    def clean_links_Ele(self, links_Ele):
        """
        相邻且相同href认为同一链接， 提取其最大公共父亲节点
        :return: 清洗后的链接列表
        """
        result = []
        del_Ele = []
        for idx in range(len(links_Ele)-1):
            cala_father = [links_Ele[idx]]
            for jdx in range(idx+1, len(links_Ele)):
                if links_Ele[jdx][2] == "" or links_Ele[jdx][2] != links_Ele[idx][2]\
                        or links_Ele[idx][3] is not None:
                    new = self.get_father_element(cala_father)
                    result.append(new)
                    break
                else:
                    cala_father.append(links_Ele[jdx])
                    del_Ele.append(links_Ele[jdx])

        if len(links_Ele) > 0 and links_Ele[-1] not in del_Ele:
            result.append(links_Ele[-1])

        new_links = [x for x in result if x not in del_Ele]
        temp = set()
        new_link = []
        for i in new_links:
            if i not in temp:
                temp.add(i)
                new_link.append(i)

        return new_link

    def watch_links(self):
        """
        元素预处理，判断元素是否可见，判断是否符合反向特征
        """
        # 获取所有<a>元素
        all_links = self.driver.find_elements_by_xpath("//a")
        self.LOG.info("Number of all links before filtering: {}".format(len(all_links)))
        lefts = []
        tops = []
        self.LOG.info("Judging element visibility.")
        self.LOG.info("And also judging the reverse characteristics.")
        links = {"notext":[],"cansee":[],"nosee":[],}

        for idx,link in enumerate(all_links):
            # 获取链接位置
            try:
               left = link.location["x"] if link.location["x"] else 0
               lefts.append(left)
               top = link.location["y"] if link.location["y"] else 0
               tops.append(top)
            except:
                self.LOG.error("Cannot get X-axis or Y-axis coordinates in: NO." + str(idx) + " link" )
                continue

            # 中央区域是否包含 “更多” 的链接
            if len(self.more_regx.findall(link.text.replace(" ",''))) > 0:
                if (link.get_attribute("href") and "#" not in link.get_attribute("href") and \
                    len(link.text.replace(" ",'')) < 8 and link.get_attribute("href") != self.driver.current_url)\
                        or link.get_attribute("onclick") is not None:
                    if self.check_location_x(link, self.__mianViewRange_more_x[0], self.__mianViewRange_more_x[1]):
                        self.more_in_center = True
                        self.more_in_center_num += 1
                        self.more_in_center_link = link.get_attribute("href")
                        if self.more_in_center_num > 1:
                            self.more_in_center_num = 0
                            self.LOG.warn("too many more in center")
                            return False
            
            # 链接字数小于4被认为无文本 （导航栏链接多为4）（不重要）
            if len(link.text.replace(r'\r', '').replace(r'\n', '').replace(' ', '').strip()) < 4:
                links["notext"].append(link)
            
            # 可见性标记（重要）
            if (link.get_attribute("href") and link.get_attribute("href") != self.driver.current_url \
                    and link.get_attribute("href") != self.driver.current_url + "#" \
                    and link.is_displayed()) or \
                    link.get_attribute("onclick") is not None:
                links["cansee"].append(link)
            else:
                links["nosee"].append(link)
        self.LOG.info("Start modifying link properties (cansee and nosee and notext(此属性不重要))")
        # 运行JS修改html
        for attr, all in links.items():
            if attr == "cansee":
                for one in all:
                    try:
                        if not one.is_displayed():
                            all.remove(one)
                    except:
                        continue
            for one in all:
                try:
                    self.driver.execute_script("arguments[0].setAttribute('"+attr+"','yeap');", one)
                except:
                    continue
        # 实际链接在页面上范围。
        ### NOTE: 适配情况 iframe整体靠右的情况
        if len(lefts) > 0:
            self.real_link_left = 0# min(lefts) if min(lefts) > 0 else 0
            self.LOG.info("real left is {}".format(self.real_link_left))
        else:
            self.real_link_left = 0
        if len(tops) > 0:
            self.real_link_top = 0# min(tops) if min(tops) >= 0 else 0
            self.LOG.info("real top is {}".format(self.real_link_top))
            self.real_link_botton = max(tops) if max(tops) >= 0 else 0
            self.LOG.info("real botton is {}".format(self.real_link_botton))
        else:
            self.real_link_top = 0
            self.real_link_botton = self.__pageHeight
        return True

    def tag_a_min_father_node(self,list_download = False):
        """
        计算提取可疑列表区域        
        :return: [xpath1,xpath2,xpath3,...]
        """
        links_Ele = []
        father_list = []
        # 预处理: 将可见<a>设置属性cansee
        if not self.watch_links():
            return []
        
        # xpath提取基于etree
        root = etree.HTML(self.driver.page_source)
        Eleroot = etree.ElementTree(root)
        links =  Eleroot.findall('//a[@cansee]')
        self.LOG.info("Filtered after all the number of links: {}".format(len(links)))

        # 有效链接
        links_Ele = [(self.purification(x.xpath("string(.)")),
                      Eleroot.getpath(x).replace("/html/body/html/body", "/html/body"),
                      x.attrib.get("href",""),
                      x.attrib.get("onclick", None)) \
                      for x in links \
                      if self.purification(x.xpath("string(.)")) and len(self.purification(x.xpath("string(.)"))) > 3 and self.anchor_black_regx.search(self.purification(x.xpath("string(.)"))) is None\
                        and not x.attrib.get("href","") == ("javascript:void(0)")\
                        and (not x.attrib.get("href","").startswith("#") and not x.attrib.get("href","") == "./" or
                        x.attrib.get("onclick", None) is not None)
                     ]

        # 元素清洗
        # 相邻标签相同href，需合并
        links_Ele = self.clean_links_Ele(links_Ele)

        # 扫描有效链接，提取最小父节点xpath
        for idx in range(len(links_Ele) - self.__minElesInList - 1):
            is_list, father_xpath = self.get_list_father_xpath(links_Ele[idx : idx + self.__minElesInList])
            if is_list:
                # 符合列表逻辑
                father_list.append(father_xpath)

        return list(set(father_list))

    def get_page_list(self,list_download = False):
        """
        可疑列表区域提取
        获取符合要求的列表xpath
        要求：
        1. 可见
        2. 列表元素数量超过最小要求数量
        """
        #可疑列表区域
        list_area = self.tag_a_min_father_node(list_download)
        self.LOG.info("List before filtering: {}".format(list_area))
        self.LOG.info("The number of lists before filtering: {}".format(len(list_area)))
        return list_area

    def judge_list_xpath(self, list_download = False):
        """
        判断获取到的列表xpath是否在主视图区域
        :return:
        """
        a_list= []
        list_xpath = []
        result = []
        list_xpath = self.get_page_list(list_download)

        if list_xpath:
            for item in list_xpath:
                a_size_list = []
                a_x_list = []
                a_list =[]
                try:
                    a_list = self.driver.find_elements_by_xpath(item + '//a[@cansee]')
                except:
                    self.LOG.error("{}:{}无法找到该xpath" .format(self.driver.current_url, item + '//a[@cansee]'))
                    continue

                for element in a_list:
                    try:
                        a_size_list.append(element.size['width'])
                        a_x_list.append(element.location['x'])
                    except:
                        self.LOG.error("{}:{}无法正常定位该xpath".format(self.driver.current_url, item))
                        a_size_list.append(0)
                # 有的html可能不规范，会出现定位不到元素的情况
                max_a_size = max(a_size_list) if len(a_size_list) > 0 else 0
                try:
                    if max_a_size == 0:
                        max_a_size = self.driver.find_element_by_xpath(item).size['width'] if self.driver.find_element_by_xpath(item).size['width'] and \
                                                                                              self.driver.find_element_by_xpath(item).size['width'] != 0 else 0
                except:
                    self.LOG.error("{}:{}无法找到该xpath".format(self.driver.current_url, item ))
                    max_a_size = 0
                if max_a_size == 0:
                    continue
                # 判断size最大的a标签的位置
                content = self.driver.find_element_by_xpath(item)
                # 超过3000认为异常情况
                if content.size['width'] > 3000:
                    continue
                # 判断是否过页面宽度中位线
                ### 这个也许有更好的方法
                start = content.location['x']
                if self.real_link_left > self.__pageHalfWidth and content.location['x'] > self.__pageHalfWidth:
                    self.__pageHalfWidth = ((self.__pageHalfWidth * 2 - self.real_link_left)/2)+self.real_link_left
                if (0 <= start < self.__pageHalfWidth):
                    if (start + max_a_size) > (self.__pageHalfWidth - 50) or (
                                start + content.size['width']) > (self.__pageHalfWidth - 50):
                        result.append(item)

        self.LOG.info("List after main-view filtering: {}".format(result))
        return result

    def filter_xpath(self, xpaths):
        """
        多列表块合并
        一系列的过滤规则
        """

        result = xpaths

        if len(result) > 1:
            self.LOG.info("Next, try multi-table fast merge: {}".format(len(result)))
            result = self.try_to_Merge(result)
            self.LOG.info("len of list after Merge: {}".format(len(result)))
            result = self.last_xpath_level(result)
        self.LOG.info("len of list after level filter: {}".format(len(result)))
        if len(result) == 1:
            result = self.filter(result, True)
            result = self.last_xpath_rule(result)
            self.LOG.info("len of list after view filter -- Only: {}".format(len(result)))
        if len(result) > 1 or len(result) == 0:
            return []
        best_xpath = self.final_check(result)
        return best_xpath

    def check_merge_ele(self, xpaths):
        """
        merge校验，写的比较丑
        :return:
        """
        xpath_first = xpaths[0]
        xpath_second = xpaths[1]

        list_A = self.driver.find_elements_by_xpath(xpath_first + "//a[@cansee]")
        list_B = self.driver.find_elements_by_xpath(xpath_second + "//a[@cansee]")
        list_A_x = [x.location["x"] for x in list_A]
        list_B_x = [x.location["x"] for x in list_B]

        a = self.driver.find_element_by_xpath("/html").text.replace(" ","").find(self.driver.find_element_by_xpath(xpath_first).text.replace(" ",''))
        b = len(self.driver.find_element_by_xpath(xpath_first).text.replace(" ",''))
        c = self.driver.find_element_by_xpath("/html").text.replace(" ","").find(self.driver.find_element_by_xpath(xpath_second).text.replace(" ",''))
        d = len(self.driver.find_element_by_xpath(xpath_second).text.replace(" ",''))
        if a > c:
            dis = a - c - d
        else:
            dis = c - a - b
        self.LOG.info("who is ur father ? dis is {}".format(dis * (-1)))
        if dis*dis > (3)*(3):
            self.LOG.info("i am not ur father {}".format(dis * (-1)))
            return False
        if len(set(list_A_x)) == len(set(list_B_x)):
            return True
        return False

    def try_to_Merge(self, xpath_list):
        '''
        尝试合并
        :param xpath_list:
        :return:
        '''
        res_xpath = []
        xpaths_Merge = list(combinations(xpath_list, 2))
        for xpaths in xpaths_Merge:
            x_axis = [self.driver.find_elements_by_xpath(x)[0].location['x'] for x in xpaths]
            x_num = [len(x.split("/")) for x in xpaths]
            x_xpath = [re.sub(r"\d", "", x) for x in xpaths]

            if len(list(set(x_axis))) == 1 and len(list(set(x_num))) == 1 and len(list(set(x_xpath))):
                if self.check_merge_ele(list(xpaths)):
                    res = self.merge_xpath(list(xpaths))
                    if len(res[0].split("/")) < x_num[0]:
                        xpath_list.append(res[0])
                        if xpaths[0] in xpath_list:
                            xpath_list.remove(xpaths[0])
                        if xpaths[1] in xpath_list:
                            xpath_list.remove(xpaths[1])
        res_xpath = list(set(xpath_list))
        return res_xpath

    def merge_xpath(self, xpath_list):
        """
        多列表块类型的合并
        """
        res = []
        res.append(self.get_father_xpath(xpath_list))
        return res

    def check_some_word(self, lastest_xpath):
        """
        一些页脚之类的 可有可无
        """
        xpath = lastest_xpath[0]
        if (self.driver.find_element_by_xpath(xpath).text.replace(r'\r', '').replace(r'\n', '').replace(' ', '')).find(
                "备案序号：") >= 0:
            self.LOG.info("some word i don`t want to see")
            return False
        a_List = self.driver.find_elements_by_xpath(xpath+"//a[@cansee]")
        for a in a_List:
            if len(a.text.replace(r'\r', '').replace(r'\n', '').replace(' ', '')) < 9 and \
                    (a.text.replace(r'\r', '').replace(r'\n', '').replace(' ', '').find("更多") >= 0 or
                    a.text.replace(r'\r', '').replace(r'\n', '').replace(' ', '').find("More") >= 0):
                self.LOG.info("i wanna more not just u")
                self.more_in_center = True
        return True

    def get_list_area(self, list_download = False):
        _, resultList = self.is_channel_page_list(list_download)
        return resultList

    def list_judge(self, list_download):
        """
        找出符合逻辑的列表块，并判断是否在主视图区域等一系列规则
        """
        try:
            xpaths = self.judge_list_xpath(list_download)
            result = self.filter_xpath(xpaths)
        except:
            self.LOG.info(traceback.format_exc())
            return -1, []

        if list_download and result:
            return True, result
        elif list_download and not result:
            return False, result

        # 比例判断，a锚文本长度占父节点区域文本长度比例大于0.06才算频道页
        last_result = []
        if result:
            for element in result:
                if self.anchor_text_proportion(element):
                    last_result.append(element)
        else:
            return False, []

        if last_result:
            return True, last_result
        else:
            return False, []

    def text_ratio(self, reverse = False):
        """
        页面总字数不能超过链接总字数的40倍
        """
        a_text_len = 0
        a_content = self.driver.find_elements_by_xpath("//a")
        for a_text in a_content:
            a_text_len += len(a_text.text)

        body_content = self.driver.find_element_by_xpath("/html/body")
        scripts = self.driver.find_elements_by_xpath("/html/body//script")
        script_len = 0
        for script in scripts:
            script_len += len(script.text)
        body_text_len = len(body_content.text.replace("\t","").replace(" ","")) - script_len
        self.LOG.info("body_text_len:{}, a_text_len:{}".format(body_text_len, a_text_len))
        if a_text_len > 0:
            if not reverse:
                return body_text_len / float(a_text_len)
            else:
                return float(a_text_len) / body_text_len
        else:
            return 41

    def check_text(self, father_xpath=None):
        self.LOG.info("start check text")
        if not self.check_some_word(father_xpath):
            return []
        return father_xpath

    def final_check(self, xpath_list):
        """
        最后一些小规则 补丁式
        """
        if len(xpath_list) == 0:
            return []
        res = self.check_text(xpath_list)
        self.LOG.info("finish check text")
        if len(xpath_list) == 0:
            return []

        if len(res) == 1:
            if self.more_in_center:
                self.__return_more = True
        if len(res) > 0:
            return res
        else:
            return []

    def check_proportion_of(self, xpath, proportion):
        try:
            contents = self.driver.find_elements_by_xpath(xpath+"//a[@cansee]")
            contents_location = [x.location["y"] for x in contents]
            contents_diff = max(contents_location) - min(contents_location)
            self.LOG.info("contents_diff is {}".format(contents_diff))
            self.LOG.info("real_link_diff is {}".format((self.real_link_botton - self.real_link_top)))
            if proportion * (self.real_link_botton - self.real_link_top) < contents_diff:
                return True
            else:
                return False
        except:
            self.LOG.info("check_proportion_of fail {}".format(xpath))
            return False

    def is_Flip_in_xpath(self, xpath):
        try:
            contents = self.driver.find_elements_by_xpath(xpath + "//a[@cansee]")
            links = self.driver.find_elements_by_xpath("//a[@cansee]")
            last_ele = max([x.location["y"] for x in contents])
            want_links = [x for x in links if x.location["y"] >= last_ele]
            for link in want_links:
                try:
                    if len(self.next_page_re.findall(link.text.replace(" ", ''))) > 0:
                        return True
                except:
                    self.LOG.error("xpath中某元素无法使用 {}".format(xpath))
            return False
        except:
            self.LOG.error("is_Flip_in_xpath 发现不可预见异常\n {}".format(traceback.format_exc()))
            return False

    def last_xpath_level(self, xpath_list, if_y = True):
        """
        # 最终xpath超过两个， xpath小于3层
        :return:
        """
        for xpath in xpath_list:
            xlist = xpath.split('/')
            if len(xlist) < 4:
                if xpath in xpath_list:
                    xpath_list.remove(xpath)
        return xpath_list

    def last_xpath_rule(self, xpath_list, if_y = True):
        """
         最终xpath超过两个， xpath小于4层
        :return:
        """
        for xpath in xpath_list:
            # 对不同高度列表块进行校验
            # 不可超过1.3屏
            if xpath in xpath_list and if_y and not self.check_location_y(xpath, 0, 1.3):
                if xpath in xpath_list and not self.is_Flip_in_xpath(xpath):
                    self.LOG.info("remove {} beacuse location_y".format(xpath_list))
                    xpath_list.remove(xpath)
            # 1-1.3屏之间的
            if xpath in xpath_list and if_y and self.check_location_y(xpath, 1, 1.3) and not self.check_proportion_of(xpath, 0.3):
                if xpath in xpath_list:
                    self.LOG.info("remove {} beacuse check_proportion_of".format(xpath_list))
                    xpath_list.remove(xpath)
            
            self.LOG.info("start check more {}".format(xpath_list))

            if xpath in xpath_list and self.check_more(xpath):
                if xpath in xpath_list:
                    xpath_list.remove(xpath)
            self.LOG.info("finish check more {}".format(xpath_list))
            self.LOG.info("start check link_img {}".format(xpath_list))
            if xpath in xpath_list and self.img_in_link(xpath):
                if xpath in xpath_list:
                    xpath_list.remove(xpath)
            self.LOG.info("finish check link_img {}".format(xpath_list))

        return xpath_list

    def check_more(self, xpath):
        """
        检查 更多式的链接
        """
        all_links = self.driver.find_elements_by_xpath(xpath + "//a[@cansee]")
        self.LOG.info("all links before filter: {}".format(len(all_links)))
        links_num = len(set([x.get_attribute('href') for x in all_links]))
        self.LOG.info("all href before filter: {}".format(links_num))
        num = 0
        for link in all_links:
            if len(self.more_regx.findall(link.text.replace(" ", ''))) > 0 and \
                len(self.purification(link.text)) < 7:
                num+=1
                self.__return_more = True
        if num >= 2 and float(num) < float(links_num) * 0.8:
            return True
        return False

    def filter(self, xpaths, noly = False):
        """
        列表内元素文本分布规律达到要求 或 列表内列表日期数量达到要求
        且
        元素不再同一行(类似导航栏，最新通知)
        """
        res = []
        for xpath in xpaths:
            if self.check_text_num(xpath) or self.check_date_num(xpath):
                if self.is_like_nav(xpath):
                    res.append(xpath)
        return res
    
    def is_like_nav(self, xpath):
        """
        确保列表内元素不再同一行
        """
        links = self.driver.find_elements_by_xpath(xpath + "//a[@cansee]")
        all_y = [x.location["y"] for x in links]
        all_y = list(set(all_y))
        diff = (max(all_y) - min(all_y)) if len(all_y) > 0 else 0
        if diff < 40:
            self.LOG.info("now in :{}".format(xpath))
            self.LOG.warn("Elements in the same line")
            return False
        return True

    def check_text_num(self, xpath):
        """
        判断列表内元素文本分布规律是否符合规则
        1.标题大于12字的密度超过0.2
        2.标题大于四个字且排列整齐
        """
        self.LOG.info("now :{}".format(xpath))
        links = self.driver.find_elements_by_xpath(xpath + "//a[@cansee]")
        hrefs = []
        tmp = []
        for link in links:
            if link.get_attribute('href'):
                hrefs.append(link.get_attribute('href'))

        num = 0
        for link in links:
            if len(link.text.strip().replace("·","")) > 4:
                text = re.sub(r"\d", "", link.text)
                tmp.append(len(text.strip()))
            if len(link.text) >= self.__standardTitleLength or (len(link.text) == 0 and link.size["width"] > 400):
                num += 1
    
        if float(num) >= len(list(set(hrefs))) * self.__standardTitleDensity:
            self.LOG.info("Headings exceeding the standard length (" + str(self.__standardTitleLength) + ") exceed the standard density(" + str(self.__standardTitleDensity) + ")")
            return True
        if float(num) < len(list(set(hrefs))) * self.__standardTitleDensity and len(set(tmp)) == 1 and float(len(tmp)) > len(list(set(hrefs)))* 0.7:
            self.LOG.info("The value of the title over the standard length is less than the standard density but is neatly arranged")
            return True

        self.LOG.info("effect have :{}".format(float(num)))
        self.LOG.info("now count:{}".format(len(set(tmp))))
        self.LOG.info("all count:{}".format(len(list(set(hrefs)))))
        return False

    def check_date_num(self, xpath):
        """
        字数过短则取列表时间
        :param xpath:
        :return:
        """
        links = self.driver.find_elements_by_xpath(xpath + "//a[@cansee]")
        content = self.driver.find_element_by_xpath(xpath).text
        self.LOG.info("find date count:{}".format(len(self.__postFeaturesRegex4.findall(content))))
        self.LOG.info("links count:{}".format(len(links)))
        if len(self.__postFeaturesRegex4.findall(content)) > len(links) / 2:
            return True
        return False


    # too slow !!!
    def img_in_link(self, xpath):
        """
        检查列表中有图片的规则，此步骤贼慢，xpath缘故，后期优化
        """
        if xpath == "/html/body/div[5]/div[2]/ul[1]" and ".cac.gov." in self.driver.current_url:
            return False
        if xpath == "/html/body/div[5]/div/ul" and ".sheitc.gov." in self.driver.current_url:
            return False
        #加入规则硬匹配 1
        links = self.driver.find_elements_by_xpath(xpath + "//a[@href and @notext and not(starts-with(@href,'#'))\
                                                                 and not(starts-with(@href,'java'))]\
                                                                    //img")
        if not links:
            self.LOG.info("have no link_img in {}".format(xpath))
            return False

        all_link = self.driver.find_elements_by_xpath(xpath + "//a[@href and @cansee and not(starts-with(@href,'#'))\
                                                                    and not(starts-with(@href,'java'))]")

        if len(self.driver.find_elements_by_xpath(xpath + "//a//img")) == len(all_link):
            return False

        page_links = self.driver.find_elements_by_xpath(xpath + "//*[contains(@id,'page') or contains(@id,'Page')]//a[@href and @notext and not(starts-with(@href,'#'))\
                                                                    and not(starts-with(@href,'java'))]\
                                                                    //img")
        links = list(set(links) - set(page_links))


        all_link_num = [x.get_attribute("href") for x in all_link if x.get_attribute("href")]
        if (len(links) > 0 and float(len(links)) < len(list(set(all_link_num)))/3.0):
            self.LOG.info("img in link, WTF")
            return True
        return False

    def is_channel_page_list(self, list_download = False):
        """
        判断是否为频道页
        return格式: [[is_channel, has_more], [xpath]]
        return类型: [[bool, bool], [string]]
        """
        # 在已知是列表的情况下
        if list_download:
            self.getPage_property_after_request()
            result, resultList = self.list_judge(list_download)
            self.LOG.info("url :{} (http list): {}".format(self.driver.current_url, result))
            return result, resultList
        
        # 黑名单规则匹配
        try:
            if ".yantian." in self.driver.current_url and self.driver.find_element_by_xpath("/html/head/meta[@name='ArticleTitle']") is not None:
                self.LOG.info("channel judge: meta contains ArticleTitle")
                return False, []
        except:
            self.LOG.error("channel judge:meta can go on")
            
            for url_black in self.__urlBlack:
                if url_black in self.driver.current_url:
                    return False, []

        # title是首页不为目录页
        try:
            r2 = EC.title_is(u'首页')(self.driver)
            if r2:
                self.LOG.info("channel judge: title contains {}".format(r2))
                return False, []
        except:
            self.LOG.error("channel judge:title contains judge fail")

        # 网页总文本长度/锚文本长度 > 40
        # 链接密度过小
        try:
            ratio = self.text_ratio()
            self.LOG.info("channel judge ratio:{}".format(ratio))
            if ratio > 40:
                return [False,False], []
        except:
            self.LOG.error("channel judge: body len and a text len fail")

        # 设置页面属性
        self.getPage_property_after_request()
        result, resultList = self.list_judge(list_download)

        # has_more是后期需求
        # 格式化接口参数
        tmp = []
        tmp.append(result)
        tmp.append(self.__return_more)
        result = tmp
        self.__return_more = False

        self.LOG.info("url :{} (http list): {}".format(self.driver.current_url, result))
        return result, resultList

    def is_channel_page(self, list_download = False):

        result, resultList = self.is_channel_page_list(list_download)
        return result, resultList


# 频道识别
def is_channel_judge(chrome_driver, policyid, list_download = False):
    judge = ChannelJudge(chrome_driver, policyid)
    return judge.is_channel_page(list_download)

# 返回列表区域的xpath
def get_list_xpath(chrome_driver, policyid, list_download = False):
    area = ChannelJudge(chrome_driver, policyid)
    return area.get_list_area(list_download)

if __name__ == '__main__':
    # 单例测试
    c = chrome_option("test")
    driver = c.chrome_init()
    # 请你关注我好么
    # 下面是我的简书页面
    c.open_url("https://www.jianshu.com/u/83c7ce3fa495",driver)
    import time,random
    time.sleep(random.uniform(5, 8))
    print(get_list_xpath(driver, "test"))
    driver.quit()
