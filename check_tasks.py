import json
import os
import requests
from datetime import datetime, timedelta

PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN')
PUSHPLUS_URL = 'https://www.pushplus.plus/send'
CHECK_WINDOW_MINUTES = 5

def load_tasks():
    with open('tasks.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def send_pushplus(title, content):
    if not PUSHPLUS_TOKEN:
        print('❌ 未配置 PUSHPLUS_TOKEN')
        return False
    payload = {
        'token': PUSHPLUS_TOKEN,
        'title': title,
        'content': content,
        'template': 'markdown'
    }
    try:
        resp = requests.post(PUSHPLUS_URL, json=payload, timeout=10)
        data = resp.json()
        print(f'PushPlus 响应: {data}')
        if data.get('code') == 200:
            print(f'✅ 推送成功: {title}')
            return True
        else:
            print(f'❌ 推送失败: {data}')
            return False
    except Exception as e:
        print(f'❌ 推送异常: {e}')
        return False

def check_and_notify():
    tasks_db = load_tasks()
    now = datetime.utcnow() + timedelta(hours=8)
    today_str = now.strftime('%Y-%m-%d')
    print(f'🕐 当前北京时间: {now.strftime("%Y-%m-%d %H:%M:%S")}')
    check_dates = [today_str, (now + timedelta(days=1)).strftime('%Y-%m-%d')]
    notified = False
    for date_str in check_dates:
        day_tasks = tasks_db.get(date_str, [])
        print(f'📋 检查日期 {date_str}，共 {len(day_tasks)} 个任务')
        for task in day_tasks:
            if task.get('done'):
                print(f'  ⏭️ 已完成，跳过：{task.get("text")}')
                continue
            task_time_str = task.get('time')
            if not task_time_str:
                print(f'  ⏭️ 无时间，跳过：{task.get("text")}')
                continue
            try:
                task_hour, task_minute = map(int, task_time_str.split(':'))
            except:
                continue
            task_date = datetime.strptime(date_str, '%Y-%m-%d')
            task_datetime = task_date.replace(hour=task_hour, minute=task_minute, second=0)
            diff_minutes = (task_datetime - now).total_seconds() / 60
            print(f'  🕐 任务「{task.get("text")}」 {task_time_str}，距现在 {diff_minutes:.1f} 分钟')
            if -CHECK_WINDOW_MINUTES <= diff_minutes <= CHECK_WINDOW_MINUTES:
                date_label = task_date.strftime('%m月%d日')
                content = f"""## {task['text']}

📅 日期：{date_label}
🕐 时间：{task['time']}

请及时完成并打卡 ✅"""
                send_pushplus('⏰ 月嫂任务提醒', content)
                notified = True
    if not notified:
        print('ℹ️ 本次检查没有需要提醒的任务')

if __name__ == '__main__':
    check_and_notify()
