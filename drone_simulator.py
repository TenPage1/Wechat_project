# drone_simulator.py —— 模拟无人机（HTTP 轮询版，放在工作区根目录）
# 用法：
#   # 连本地后端
#   python drone_simulator.py --base http://127.0.0.1:5000 --id 1
#   # 连云托管后端
#   python drone_simulator.py --base https://flask-0cc2-314918-11-1410604288.sh.run.tcloudbase.com --id 1
#
# 原理：
#   无人机每隔几秒主动 GET /api/drone/poll 问"有任务吗"
#   领到任务 -> 模拟飞向目的地，飞行中 POST /api/drone/report 上报位置
#   到达 -> 上报 arrived / done
#
# 依赖：pip install requests

import argparse
import time

import requests

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:5000', help='后端地址')
parser.add_argument('--id', type=int, default=1, help='无人机ID')
parser.add_argument('--speed', type=float, default=0.15, help='每步移动比例 0~1')
parser.add_argument('--interval', type=float, default=1.0, help='上报间隔(秒)')
parser.add_argument('--poll', type=float, default=2.0, help='轮询间隔(秒)')
args = parser.parse_args()

BASE = args.base.rstrip('/')

# 无人机当前位置（初始在起飞点：大工创新创业学院）
cur_lng, cur_lat = 121.52530, 38.88340


def get(path, params=None):
    return requests.get(BASE + path, params=params, timeout=10).json()


def post(path, data):
    return requests.post(BASE + path, json=data, timeout=10).json()


def fly_to(order_id, to_lng, to_lat):
    """从当前位置逐步飞向目标"""
    global cur_lng, cur_lat
    print(f'[无人机{args.id}] 收到任务 {order_id}，前往 ({to_lng},{to_lat})')
    while True:
        dlng = to_lng - cur_lng
        dlat = to_lat - cur_lat
        if abs(dlng) < 1e-5 and abs(dlat) < 1e-5:
            cur_lng, cur_lat = to_lng, to_lat
            post('/api/drone/report', {'drone_id': args.id, 'order_id': order_id,
                                       'lng': cur_lng, 'lat': cur_lat, 'status': 'arrived'})
            print(f'[无人机{args.id}] 到达目的地 ({cur_lng:.5f},{cur_lat:.5f})')
            time.sleep(1)
            post('/api/drone/report', {'drone_id': args.id, 'order_id': order_id,
                                       'lng': cur_lng, 'lat': cur_lat, 'status': 'done'})
            print(f'[无人机{args.id}] 任务 {order_id} 完成')
            return
        cur_lng += dlng * args.speed
        cur_lat += dlat * args.speed
        post('/api/drone/report', {'drone_id': args.id, 'order_id': order_id,
                                   'lng': cur_lng, 'lat': cur_lat, 'status': 'flying'})
        print(f'[无人机{args.id}] 位置上报 ({cur_lng:.5f},{cur_lat:.5f})')
        time.sleep(args.interval)


def main():
    print(f'[无人机{args.id}] 目标后端：{BASE}')
    print(f'[无人机{args.id}] 开始轮询任务...（Ctrl+C 退出）')
    while True:
        try:
            r = get('/api/drone/poll', {'drone_id': args.id})
            task = (r.get('data') or {}).get('task') if r.get('code') == 0 else None
            if task:
                fly_to(task['order_id'], task['to']['lng'], task['to']['lat'])
            else:
                time.sleep(args.poll)
        except KeyboardInterrupt:
            print('\n[无人机] 退出')
            break
        except Exception as e:
            print(f'[无人机] 轮询异常：{e}，5秒后重试')
            time.sleep(5)


if __name__ == '__main__':
    main()
