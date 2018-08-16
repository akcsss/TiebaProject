from . import utils
from .models import User,Sign,Data
import requests
import logging
import time

# 定时任务 设置在setting.py
# flag = 0  默认（未update,未sign）
# flag = 1  新用户update
# flag = 2  新用户sign

def do():
    # 云回帖
    u = User.objects.all()
    data = Data.objects.get(pk=1)
    content = requests.get('https://api.gushi.ci/rensheng.txt').text
    for i in u:
        ltime = time.localtime()
        t = ltime.tm_hour*60 + ltime.tm_min
        for j in i.tieba_set.all():
            if t % j.time == 0:
                if j.stop:
                    j.stop_times = j.stop_times + 1
                    j.save()
                    continue
                else:
                    if j.isLou:
                        # 客户端楼中楼
                        try:
                            res = utils.client_LZL(i.bduss,j.name,j.fid,content,j.qid,j.tid)
                            if res['error_code'] == '0':
                                j.success = j.success + 1
                                data.success += 1
                            else:
                                j.fail = j.fail + 1
                        except Exception as e:
                            logging.info(e)
                        finally:
                            j.save()
                    else:
                        if i.i_type:
                            # 客户端回帖模式
                            try:
                                ser = utils.client_Post(i.bduss, j.name, j.tid, j.fid, content)
                                if ser['error_code'] == '0':
                                    j.success = j.success + 1
                                    data.success += 1
                                else:
                                    j.fail = j.fail + 1
                            except Exception as e:
                                logging.info(e)
                            finally:
                                j.save()
                        else:
                            # 网页端回帖模式
                            try:
                                ser = utils.Post(i.bduss, content, j.tid, j.fid, j.name)
                                if ser['err_code'] == 0:
                                    j.success = j.success + 1
                                    data.success += 1
                                else:
                                    j.fail = j.fail + 1
                            except Exception as e:
                                logging.info(e)
                            finally:
                                j.save()
    data.save()



def update():
    #更新用户关注的贴吧列表
    u = User.objects.all()
    for i in u:
        print(i.username + '开始更新...')
        data = utils.get_favorite(i.bduss)
        for j in data['forum_list']['non-gconforum']:
            try:
                Sign.objects.get(fid=j['id'],user=i)
            except Exception:
                s = Sign(name=j['name'],fid=j['id'],level_id=j['level_id'],cur_score=j['cur_score'])
                s.save()
                s.user.add(i)
                s.save()
        for k in data['forum_list']['gconforum']:
            try:
                Sign.objects.get(fid=k['id'],user=i)
            except Exception:
                s = Sign(name=k['name'],fid=k['id'],level_id=k['level_id'],cur_score=k['cur_score'])
                s.save()
                s.user.add(i)
                s.save()


def sign():
    # 每日签到
    u = User.objects.all()
    for i in u:
        tbs = utils.get_tbs(i.bduss)
        for j in i.sign_set.all():
            if j.is_sign == False:
                res = utils.client_Sign(i.bduss,j.name,j.fid,tbs)
                if res['error_code'] == '0' or res['error_code'] == '160002':
                    # 160002 已经签过到了
                    j.is_sign = True
                    j.save()
                else:
                    print('用户：' + i.username + ' 贴吧：' + j.name + ' ')
                    print(res)

def reset():
    # 每日凌晨将签到状态复位
    Sign.objects.all().update(is_sign=False)


def new_update():
    # 轮循数据库查找新用户更新贴吧
    u = User.objects.filter(flag=0)
    for i in u:
        print(i.username+'开始更新...')
        data = utils.get_favorite(i.bduss)
        for j in data['forum_list']['non-gconforum']:
            try:
                Sign.objects.get(fid=j['id'], user=i)
            except Exception:
                s = Sign(name=j['name'], fid=j['id'], level_id=j['level_id'], cur_score=j['cur_score'])
                s.save()
                s.user.add(i)
                s.save()
        for k in data['forum_list']['gconforum']:
            try:
                Sign.objects.get(fid=k['id'], user=i)
            except Exception:
                s = Sign(name=k['name'], fid=k['id'], level_id=k['level_id'], cur_score=k['cur_score'])
                s.save()
                s.user.add(i)
                s.save()
        i.flag = 1
        i.save()


def new_sign():
    # 签到
    u = User.objects.filter(flag=1)
    for i in u:
        tbs = utils.get_tbs(i.bduss)
        for j in i.sign_set.all():
            if j.is_sign == False:
                res = utils.client_Sign(i.bduss, j.name, j.fid, tbs)
                if res['error_code'] == '0' or res['error_code'] == '160002' or res['error_code'] == 340008:
                    # 160002 已经签过到了  340008 在黑名单中
                    j.is_sign = True
                    j.save()
                else:
                    print('用户：'+i.username+' 贴吧：'+j.name+' ')
                    print(res)
        i.flag = 2
        i.save()