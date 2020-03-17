#coding:utf-8
#author:DengYu time:2020-03-16
import json

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
from multiprocessing.dummy import Pool
import time
import requests
from redis import Redis

class tudiPro():
    browser = webdriver.Chrome(executable_path='./chromedriver')

    wait = WebDriverWait(browser, 6)
    headers = {
        'USER_AGENT': 'Mozilla/5.0(Macintosh;IntelMacOSX10_14_6)AppleWebKit/537.36(KHTML,likeGecko)Chrome/79.0.3945.130Safari/537.36'
    }
    detail_urls = []
    pool = Pool(3)
    conn = Redis(host='127.0.0.1',port=6379)


    def startMe(self):
        url = 'https://www.landchina.com/default.aspx?tabid=263'
        self.browser.get(url)

        bc = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        '#TAB_tagContent8 > table > tbody > tr:nth-child(1) > td:nth-child(8)'
                                        )))

        self.browser.find_element_by_id('TAB_QueryConditionItem256').click()
        #调用js代码对网页进行修改，将原本隐藏的文本框的类型hide修改为text，可输入类型
        self.browser.execute_script("document.getElementById('TAB_queryTblEnumItem_256_v').setAttribute('type', 'text');")
        self.browser.find_element_by_id('TAB_queryTblEnumItem_256_v').clear()
        self.browser.find_element_by_id('TAB_queryTblEnumItem_256_v').send_keys('31')
        #点击查询按钮
        self.browser.find_element_by_id('TAB_QueryButtonControl').click()
        dictCookies = self.browser.get_cookies()
        jsonCookies = json.dumps(dictCookies)
        with open('anquan.txt', 'w') as f:
            f.write(jsonCookies)

        page_text = self.browser.page_source


        tree = etree.HTML(page_text)
        detail_list = tree.xpath('//*[@id="TAB_contentTable"]//tr')
        del detail_list[0]  #删除tr列标题

        for detail_info in detail_list:
            detail_url = 'https://www.landchina.com/'+detail_info.xpath('./td[3]/a/@href')[0]
            self.detail_urls.append(detail_url)

        #开启多线程提高爬取效率
        self.pool.map(self.detail_parse, self.detail_urls)

    def detail_parse(self,url):

        with open('anquan.txt', 'r', encoding='utf8') as f:
            listCookies = json.loads(f.read())

        cookie = [item["name"] + "=" + item["value"] for item in listCookies]
        cookiestr = '; '.join(item for item in cookie)
        self.headers['Cookie'] = cookiestr
        response = requests.get(url=url,headers=self.headers)
        tree = etree.HTML(response.text)
        data = []
        #电子监管号
        elenum = tree.xpath('//*[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r1_c4_ctrl"]/text()')[0]
        data.append(elenum)

        #项目名称
        proname = tree.xpath('//*[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r17_c2_ctrl"]/text()')[0]
        data.append(proname)

        #项目位置
        prolocation = tree.xpath('//*[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r16_c2_ctrl"]/text()')[0]
        data.append(prolocation)
        print(data)
        dataresult = ''.join(data)
        # with open('data.txt','a') as fb:
        #     fb.write(dataresult+"\n")

        self.conn.lpush('tudiDB',dataresult)

tudiTest = tudiPro()
tudiTest.startMe()
