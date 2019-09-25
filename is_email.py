# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import smtplib
import string
import threading
import time

import dns.resolver


# import socket
# from httplib2 import socks


class MyThread(threading.Thread):
    def __init__(self, func, args=()):  # func函数名，args参数
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


# dns解析发件域名
def fetch_mx(host):
    try:
        answers = dns.resolver.query(host, 'MX')
    except Exception:
        return ['']
    res = [str(rdata.exchange)[:-1] for rdata in answers]
    return res


# 验证邮件真实性
def verify_istrue(email):
    final_res = {"True_email": [], "False_email": [], "None_email": [], "ERROR_email": []}
    email_list = []  # 需要检验的邮件地址
    email_obj = {}  # 邮箱域名分类(dns去进行域名检查)
    if isinstance(email, str):
        email_list.append(email)
    else:
        email_list = email

    for em in email_list:
        name, host = em.split('@')
        if email_obj.get(host):
            email_obj[host].append(em)
        else:
            email_obj[host] = [em]

    for key in email_obj.keys():
        host = random.choice(fetch_mx(key))
        if host:  # dns检验通过
            # email_port = 587 if key in ["gmail.com", "qq.com", "yahoo.com.cn", "live.com"] else 25
            try:
                # socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '34.80.213.252', 28441)
                # socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '117.191.11.103', 8080)  # 用于ip代理
                # socket.socket = socks.socksocket
                smtp_obj = smtplib.SMTP(host, timeout=10)  # smtplib.SMTP_SSL(host, 587, timeout=8)
                for need_verify in email_obj[key]:  # 需要校验的邮箱不能跟发件邮箱同一个域名
                    try:
                        email_domain = random.choice(['datapointcloud.com', 'handibigdata.com', 'yingxiaodata.com'])
                        # email_domain = 'yingxiaodata.com'
                        random_str = ''.join(random.sample(string.letters + string.digits, random.randint(6, 10)))
                        smtp_obj.docmd('EHLO %s' % email_domain)  # 发件提供的域名
                        # 163.com等邮件服务器比较特殊，会判断邮件是否真的从发件人邮件服务器发出的
                        send_mail = "%s@%s" % (random_str, email_domain)
                        smtp_obj.docmd('MAIL FROM:<%s>' % send_mail)  # 发件邮箱
                    except Exception as e:
                        print 111, e
                        pass
                    finally:
                        send_from = smtp_obj.docmd('RCPT TO:<%s>' % need_verify)  # 收件邮箱
                        print send_from, need_verify
                        if send_from[0] in [250, 251, 451]:
                            final_res["True_email"].append(need_verify)  # 存在
                        elif send_from[0] == 550:
                            final_res["False_email"].append(need_verify)  # 不存在
                        else:
                            final_res["None_email"].append(need_verify)  # 未知
                smtp_obj.close()
            except Exception as e:
                for need_verify in email_obj[key]:
                    print "访问异常：", need_verify, e
                    final_res["ERROR_email"].append(need_verify)

        else:  # 域名有误
            for need_verify in email_obj[key]:
                final_res["False_email"].append(need_verify)
    return final_res


def email_addrs():
    with open('email.txt', 'r') as f:
        result = [line.strip('\n') for line in f.readlines() if line not in ['', None]]
    return result or []


if __name__ == '__main__':
    s = time.time()
    email_list = email_addrs()
    thread_list = []
    res = {"True_email": [], "False_email": [], "None_email": [], "ERROR_email": []}
    for i in range(10):
        t = MyThread(verify_istrue, (email_list[i * 1000:(i + 1) * 1000],))
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()
        res["True_email"].extend(t.get_result()["True_email"])
        res["False_email"].extend(t.get_result()["False_email"])
        res["None_email"].extend(t.get_result()["None_email"])
        res["ERROR_email"].extend(t.get_result()["ERROR_email"])

    print "不存在邮箱个数:" + str(len(res["False_email"])), res["False_email"]
    print "正确邮箱个数:" + str(len(res["True_email"]))
    print "未知邮箱个数:" + str(len(res["None_email"]))
    print "检测失败个数:" + str(len(res["ERROR_email"]))
    print time.time() - s
