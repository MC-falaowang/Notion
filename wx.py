# coding:utf-8
from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks, Response
import uvicorn
import hashlib
import xmltodict
import time
import datetime
import json
import requests

# 常量
# 微信的token令牌
WECHAT_TOKEN = "mynotion"
WECHAT_APPID = ""
WECHAT_APPSECRET = ""


def count_week(date):
    """根据date 计算这是第几年第几周"""
    year, week, w = date.isocalendar()
    return f"{year}年第{week}周"


def count_month(date: datetime.date):
    """根据date 计算这是第几年第几周"""
    year = date.year
    month = date.month
    return f"{year % 2000}年{month}月"


class MyNotion():
    secret_key = "secret_oqbGfZAVsNWKytsqB5jq1gXT9e1nooxBeMJ6uXU73vb"
    days_database_id = "068634687a7b4184b676ca35e285cad6"
    weeks_database_id = "68f6983a61a34f1099271ba303465e87"
    bill_database_id = "74c0fcba51c04536a342b320e648d721"
    month_database_id = "896722e3cdb5419dbab5ffec8394a101"

    def __init__(self):
        self.session = requests.session()
        headers = {
            "Authorization": self.secret_key,
            "Notion-Version": "2022-06-28"
        }
        self.session.headers = headers

    # 针对习惯管理的一些方法
    # 创建每天的记录  如果我忘记记录了  则创建一个都为空的
    def add_day_log(self, day_name=None, learn_en=False):

        """日期 是否学习了新技能  是否背单词"""

        if day_name is None:
            # 如果日期为None 则以今天的日期为名字
            _date = datetime.date.today()
            day_name = str(_date)
            current_weeks = count_week(_date)
        else:
            _date = datetime.datetime.strptime(day_name, "%Y-%m-%d")
            day_name = str(_date)

            current_weeks = count_week(_date)
        # print(_date)
        week_relation_id = self.query_current_weeks(current_weeks)
        # print(week_relation_id)
        properties = {'名称': {'id': 'title',
                               'title': [{'plain_text': day_name,
                                          'text': {'content': day_name, 'link': None},
                                          'type': 'text'}],
                               'type': 'title'},
                      '学习一个新技能': {'checkbox': False, 'type': 'checkbox'},
                      '日期': {'date': {'end': None, 'start': day_name, 'time_zone': None},

                               'type': 'date'},
                      '每周汇总': {'has_more': False,

                                   'relation': [{'id': week_relation_id}],
                                   'type': 'relation'},
                      '背单词': {'checkbox': learn_en, 'type': 'checkbox'},
                      '文献管理': {'has_more': False, 'relation': [], 'type': 'relation'}}
        result = self.save_to_database(self.days_database_id, properties)
        return result["id"]

    def query_day_info(self, day_name):
        """
        根据名称查询下数据库   拿来查询数据库的结构用
        """

    def query_current_weeks(self, week_name):

        """查询是否存在当前周数
            如果存在周数就返回id
            如果不存在就创建一个并返回id
        """
        query = {"filter": {"property": "周数", "rich_text": {"contains": week_name}}}
        week_info = self.query_database(self.weeks_database_id, query)
        # print(week_relation_id)
        if len(week_info["results"]) == 0:
            # 没有周数  则进行创建一个
            props = {"周数": {"id": "title", "type": "title",
                              "title": [{"type": "text", "text": {"content": week_name, "link": None},

                                         "plain_text": week_name, "href": None}]}}
            result = self.save_to_database(self.weeks_database_id, props)
            return result["id"]
            # print(result)
        else:
            return week_info["results"][0]["id"]

    # 记账方面的函数

    def add_bill(self, name=None, money=0, _type="", day_name=None):

        """日期 是否学习了新技能  是否背单词"""

        if day_name is None:
            # 如果日期为None 则以今天的日期为名字
            _date = datetime.date.today()
            day_name = str(_date)
            current_month = count_month(_date)
        else:
            _date = datetime.datetime.strptime(day_name, "%Y-%m-%d")
            day_name = str(_date)

            current_month = count_month(_date)
        # print(_date)
        month_relation_id = self.query_current_month(current_month)
        # print(week_relation_id)
        properties = {'名称': {'id': 'title',
                               'title': [{'plain_text': name,
                                          'text': {'content': name, 'link': None},
                                          'type': 'text'}],
                               'type': 'title'},
                      '类型': {'select': {
                          # "id":";Dqw",
                          "name": _type,
                          # "color":"pink"
                      },
                          'type': 'select'},
                      '日期': {'date': {'end': None, 'start': day_name, 'time_zone': None},

                               'type': 'date'},
                      '小金库': {'has_more': False,

                                 'relation': [{'id': month_relation_id}],
                                 'type': 'relation'},
                      '金额': {'number': money, 'type': 'number'},
                      # '读文献记录': {'has_more': False, 'id': 'AlMP', 'relation': [], 'type': 'relation'}

                      }
        result = self.save_to_database(self.bill_database_id, properties)
        return result["id"]

    def query_by_date(self, start, end, data_base_id):
        """
        根据名称查询下数据库   拿来查询数据库的结构用
        """
        query = {
            "filter": {
                "and": [
                    {
                        "property": "日期",
                        "date": {
                            "on_or_before": end}
                    }, {
                        "property": "日期",
                        "date": {
                            "on_or_after": start}
                    }

                ]
            }

        }
        data = self.query_database(data_base_id, query)
        # print(data)
        return data["results"]

    def count(self, start, end):

        bills = self.query_by_date(start, end, self.bill_database_id)
        bill_info = {
            "支出": 0,
            "收入": 0,
            "借贷": 0
        }
        for bill in bills:
            properties = bill["properties"]
            bill_info["支出"] += properties["支出汇总"]["formula"]["number"]
            bill_info["收入"] += properties["收入汇总"]["formula"]["number"]
            bill_info["借贷"] += properties["借贷汇总"]["formula"]["number"]

        days = self.query_by_date(start, end, self.days_database_id)
        day_info = {
            "记单词": 0,
            "阅读文献": 0,
            "学会的技能": 0
        }
        for day in days:
            properties = day["properties"]
            # print(properties)
            if properties["学习一个新技能"]["checkbox"]:
                day_info["学会的技能"] += 1

            if properties["背单词"]["checkbox"]:
                day_info["记单词"] += 1
            # if properties["学习一个新技能"]["checkbox"]:
            day_info["阅读文献"] += len(properties["文献管理"]["relation"])

        # 开始拼接下模板

        model = """支出 {} 元\n收入 {} 元\n借贷 {} 元\n---------\n记单词天数：{}\n阅读文献数量：{}\n学会的技能数量：{}""".format(
            round(bill_info["支出"], 2), round(bill_info["收入"], 2), round(bill_info["借贷"], 2),
            day_info["记单词"], day_info["阅读文献"], day_info["学会的技能"],

        )
        return model

    def query_current_month(self, current_month):

        """查询是否存在当前周数
            如果存在周数就返回id
            如果不存在就创建一个并返回id
        """
        query = {"filter": {"property": "总账月份", "rich_text": {"contains": current_month}}}
        month_info = self.query_database(self.month_database_id, query)
        # print(week_relation_id)
        if len(month_info["results"]) == 0:
            # 没有周数  则进行创建一个
            props = {"总账月份": {"id": "title", "type": "title",
                                  "title": [{"type": "text", "text": {"content": current_month, "link": None},

                                             "plain_text": current_month, "href": None}]}}
            result = self.save_to_database(self.month_database_id, props)
            return result["id"]
            # print(result)
        else:
            return month_info["results"][0]["id"]

    def query_database(self, database_id, query):
        # 获取用get

        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        resp = self.session.post(url, json=query)
        # print(resp.text)
        resp = json.loads(resp.text)
        return resp

    def save_to_database(self, database_id, properties):
        # 提交数据用post
        body = {
            # 父级信息（即你要创建的页面的上一级页面）
            "parent": {
                # 父级页面类型，如果我们想在服药记录的数据库中增加一条记录，那么新纪录是什么类型呢？
                # 答对了！是页面类型，我们创建的是记录，它展开后是一条页面，所以输入 page_id
                "type": "database_id",
                # 注意，下面的 "page_id" 项仍需要根据你的创建项目类型变化
                # 所需要提供的 ID 就是父级页面的 ID，需要手动在链接中进行复制
                "database_id": database_id
            },
            # 属性项，在这里决定新记录的属性是什么，这里我用服药记录举例
            "properties": properties
        }
        url = "https://api.notion.com/v1/pages/"
        resp = self.session.post(url, json=body)
        # print(resp.text)
        return json.loads(resp.text)

    def delete_block(self, _id):
        url = "https://api.notion.com/v1/blocks/" + _id
        resp = self.session.delete(url)
        # print(resp.text)
        # data=json.loads(resp.text)
        if resp.status_code == 200:
            return True
        return False


model = {
    "记账模板": "[什么]花了[金额]；[什么]赚了[金额];买本子花了11",
    "习惯模板": "记了单词【技能手动设置】"
}

bill_keys = ["花了", "赚了", "借给", "还钱"]
days_keys = ["记了", "没记"]
count_keys = ["今天汇总", "本周汇总", "本月汇总", "本年汇总", "昨天汇总", "上周汇总", "上月汇总"]


def get_type(text):
    if text in ["早饭", "午饭", "晚饭", "早餐", "午餐", "晚餐"]:
        return "三餐"
    for i in ["京东", "淘宝", "线下", "天猫", "抖音"]:
        if i in text:
            return "购物"
    for i in ["老板", "京粉", "淘宝联盟"]:
        if i in text:
            return "外快"
    for i in ["借给"]:
        if i in text:
            return "借贷"
    for i in ["还钱"]:
        if i in text:
            return "还款"
    for i in ["基金", "股票"]:
        if i in text:
            return "理财"
    for i in ["聚会", "聚餐"]:
        if i in text:
            return "聚餐"
    for i in ["随礼", "红包"]:
        if i in text:
            return "人情往来"
    return "日用"


def parse_bill(text):
    pass
    for key in bill_keys:
        text_list = text.split(key)
        if len(text_list) > 1:
            break
    if bill_keys.index(key) < 2:
        # 花了  赚了
        # sign 表示金额的正负
        sign = (bill_keys.index(key) - 1) or 1
        money = float(text_list[-1])
        money *= sign
        _type = get_type(text_list[0])
        result = notion.add_bill(text_list[0], money, _type)
        return "记录成功了！\n" + f'<a href="weixin://bizmsgmenu?msgmenuid=0&msgmenucontent=删除{result}">点击撤回</a>'

    else:
        # 借贷 和还钱的逻辑
        sign = -1 if key == "借给" else 1
        money = float(text_list[-1])
        money *= sign
        _type = get_type(text_list[0])
        result = notion.add_bill(text_list[0], money, _type)
        return "记录成功了！\n" + f'<a href="weixin://bizmsgmenu?msgmenuid=0&msgmenucontent=删除{result}">点击撤回</a>'

    # return result


def parse_day(text):
    is_learn = "记了单词" in text
    result = notion.add_day_log(learn_en=is_learn)
    return "记录成功了！\n" + f'<a href="weixin://bizmsgmenu?msgmenuid=0&msgmenucontent=删除{result}">点击撤回</a>'


def delete(text):
    text = text.replace("删除", "").strip()
    if notion.delete_block(text):
        return "删除成功！"
    return "删除失败"


def count(text):
    # 先查询账单   在统计习惯
    if text == "今天汇总":
        start = datetime.date.today()
        end = start
    elif text == "本周汇总":
        end = datetime.date.today()
        start = datetime.date.today() - datetime.timedelta(end.weekday())
    elif text == "本月汇总":
        end = datetime.date.today()
        start = datetime.date(end.year, end.month, 1)
        # end = datetime.datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    elif text == "本年汇总":
        end = datetime.date.today()
        start = datetime.date(end.year, 1, 1)
    elif text == "昨天汇总":
        now = datetime.date.today()
        end = datetime.date.today() - datetime.timedelta(1)
        start = end
    elif text == "上周汇总":
        now = datetime.date.today()
        start = datetime.date.today() - datetime.timedelta(now.weekday() + 7)
        end = start + datetime.timedelta(6)
    elif text == "上月汇总":
        now = datetime.date.today()
        if now.month == 1:
            year = now.year - 1
            month = 12
        else:
            year = now.year
            month = now.month - 1
        start = datetime.date(year, month, 1)
        end = datetime.date(now.year, now.month, 1) - datetime.timedelta(1)

    texts = notion.count(str(start), str(end))
    return text + "\n" + texts + "\n日期：" + "-".join([str(start), str(end)])


def parse_text(text):
    # print(text)
    if text == "关键词":
        return "|".join(bill_keys + days_keys)
    if text == "汇总":
        return "|".join(count_keys)
    if text.startswith("删除"):
        return delete(text)
    if text in model.keys():
        return model.get(text)

    if text in count_keys:
        return count(text)
    # 不是固定回复就 开始匹配

    for i in bill_keys:
        if i in text:
            return parse_bill(text)

    for i in days_keys:
        if i in text:
            return parse_day(text)
    return "没有读懂哟"


def core(xml_dict):
    text = parse_text(xml_dict.get("Content"))
    resp_dict = {
        "xml": {
            "ToUserName": xml_dict.get("FromUserName"),
            "FromUserName": xml_dict.get("ToUserName"),
            "CreateTime": int(time.time()),
            "MsgType": "text",
            "Content": text
        }
    }
    # print(xml_dict.get("MsgId"),type(xml_dict.get("MsgId")))
    #     token=get_token()
    #
    #     url="https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token="+token
    #     data={
    #     "touser":xml_dict.get("FromUserName"),
    #     "msgtype":"text",
    #     "text":
    #     {
    #          "content":"Hello World"
    #     }
    # }
    #     resp = requests.post(url,json=data)
    #     print(resp.text)
    result_dict[xml_dict.get("MsgId")] = text
    return text


def get_token():
    url = "https://api.weixin.qq.com/cgi-bin/token?appid=%s&secret=%s&grant_type=client_credential" \
          % (WECHAT_APPID, WECHAT_APPSECRET)
    resp = requests.get(url)
    # print(resp.text)
    data = json.loads(resp.text)
    return data["access_token"]


def verfiy(request: Request):
    signature = request.query_params.get("signature")
    timestamp = request.query_params.get("timestamp")
    nonce = request.query_params.get("nonce")

    # 校验参数
    if not all([signature, timestamp, nonce]):
        raise HTTPException(
            status_code=401,
            detail="不要乱搞哦"
        )

    # 按照微信的流程进行计算签名
    li = [WECHAT_TOKEN, timestamp, nonce]
    # 排序
    li.sort()
    # 拼接字符串
    tmp_str = "".join(li)
    # 进行sha1加密, 得到正确的签名值
    sign = hashlib.sha1(tmp_str.encode()).hexdigest()

    # 将自己计算的签名值与请求的签名参数进行对比，如果相同，则证明请求来自微信服务器
    if signature != sign:
        # 表示请求不是微信发的
        raise HTTPException(
            status_code=401,
            detail="不要乱搞哦"
        )


app = FastAPI(dependencies=[Depends(verfiy)])


@app.get("/wechat")
def sign(request: Request):
    echostr = request.query_params.get("echostr")
    if not echostr:
        raise HTTPException(
            status_code=400,
            detail="不要乱搞哦"
        )
    return Response(content=echostr, media_type="text/html; charset=utf-8")


@app.post("/wechat")
async def wechat(request: Request, task: BackgroundTasks):
    """对接微信公众号服务器"""

    # 表示微信服务器转发消息过来
    xml_str = await request.body()
    if not xml_str:
        raise HTTPException(
            status_code=400,
            detail="不要乱搞哦"
        )

    # 对xml字符串进行解析
    xml_dict = xmltodict.parse(xml_str)
    xml_dict = xml_dict.get("xml")

    # 提取消息类型
    msg_type = xml_dict.get("MsgType")
    if xml_dict.get("FromUserName") != "om651567jGiPyz4Hyrx663dqMbbM":
        resp_dict = {
            "xml": {
                "ToUserName": xml_dict.get("FromUserName"),
                "FromUserName": xml_dict.get("ToUserName"),
                "CreateTime": int(time.time()),
                "MsgType": "text",
                "Content": "没权限,user:" + xml_dict.get("FromUserName")

                # "Content": "正在记录，稍后查询结果...\n可回复本次ID查询结果，ID：{}".format(xml_dict.get("MsgId"))
            }
        }
    else:
        if msg_type == "text":
            # 表示发送的是文本消息
            # 构造返回值，经由微信服务器回复给用户的消息内容
            if xml_dict.get("MsgId") in msg_set:
                for i in range(10):
                    if xml_dict.get("MsgId") in result_dict.keys():
                        break

                    time.sleep(.5)
                # if xml_dict.get("Content") in result_dict.keys():
                resp_dict = {
                    "xml": {
                        "ToUserName": xml_dict.get("FromUserName"),
                        "FromUserName": xml_dict.get("ToUserName"),
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                        "Content": result_dict[xml_dict.get("MsgId")]
                    }
                }
            else:
                msg_set.add(xml_dict.get("MsgId"))

                text = core(xml_dict)

                resp_dict = {
                    "xml": {
                        "ToUserName": xml_dict.get("FromUserName"),
                        "FromUserName": xml_dict.get("ToUserName"),
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                        "Content": text

                        # "Content": "正在记录，稍后查询结果...\n可回复本次ID查询结果，ID：{}".format(xml_dict.get("MsgId"))
                    }
                }
                # time.sleep(5)
        else:
            resp_dict = {
                "xml": {
                    "ToUserName": xml_dict.get("FromUserName"),
                    "FromUserName": xml_dict.get("ToUserName"),
                    "CreateTime": int(time.time()),
                    "MsgType": "text",
                    "Content": "请说普通话"
                }
            }

    # 将字典转换为xml字符串
    resp_xml_str = xmltodict.unparse(resp_dict)
    # 返回消息数据给微信服务器
    return Response(content=resp_xml_str, media_type="application/xml")


if __name__ == '__main__':
    notion = MyNotion()
    msg_set = set()
    result_dict = dict()
    uvicorn.run(app, port=80, host="0.0.0.0")
    # app.run(port=80,host="0.0.0.0")

