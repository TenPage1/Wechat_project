# drone_simulator.py —— 模拟无人机的 TCP 客户端（放在工作区根目录）
# 用法：
#   python drone_simulator.py                      # 默认连 127.0.0.1:9000，无人机ID=1
#   python drone_simulator.py --host 127.0.0.1 --port 9000 --id 1
#
# 作用：
#   - 连接后端 TCP 服务并注册（hello）
#   - 收到 goto 指令后，模拟一步步飞向目标点，实时上报位置
#   - 到达后上报 arrived，并回到 idle 状态

import argparse
import json
import socket
import threading
import time

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=9000)
parser.add_argument('--id', type=int, default=1, help='无人机ID')
parser.add_argument('--speed', type=float, default=0.15, help='每步移动比例 0~1')
parser.add_argument('--interval', type=float, default=1.0, help='上报间隔(秒)')
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_lock = threading.Lock()


def send(obj):
    with send_lock:
        sock.sendall((json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8'))


def fly_to(order_id, to_lng, to_lat, cur):
    """从当前位置 cur=(lng,lat) 逐步飞向目标，实时上报"""
    lng, lat = cur
    print(f'[无人机{args.id}] 收到任务 {order_id}，前往 ({to_lng},{to_lat})')
    while True:
        dlng = to_lng - lng
        dlat = to_lat - lat
        if abs(dlng) < 1e-4 and abs(dlat) < 1e-4:
            lng, lat = to_lng, to_lat
            send({'type': 'position', 'order_id': order_id, 'lng': lng, 'lat': lat, 'status': 'arrived'})
            print(f'[无人机{args.id}] 到达目的地 ({lng},{lat})')
            time.sleep(1)
            send({'type': 'position', 'order_id': order_id, 'lng': lng, 'lat': lat, 'status': 'done'})
            print(f'[无人机{args.id}] 任务 {order_id} 完成')
            break
        lng += dlng * args.speed
        lat += dlat * args.speed
        send({'type': 'position', 'order_id': order_id, 'lng': lng, 'lat': lat, 'status': 'flying'})
        print(f'[无人机{args.id}] 位置上报 ({lng:.5f},{lat:.5f})')
        time.sleep(args.interval)


def main():
    print(f'[无人机{args.id}] 连接 {args.host}:{args.port} ...')
    sock.connect((args.host, args.port))
    send({'type': 'hello', 'drone_id': args.id})
    print(f'[无人机{args.id}] 已注册，等待指令...')

    # 当前位置（默认佘山起飞点）
    cur = [121.196, 31.096]
    buf = b''
    while True:
        data = sock.recv(4096)
        if not data:
            print('[无人机] 连接已断开')
            break
        buf += data
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode('utf-8'))
            except Exception:
                print('[无人机] 非法消息:', line)
                continue

            if msg.get('cmd') == 'goto':
                to = msg.get('to', {})
                t = threading.Thread(
                    target=fly_to,
                    args=(msg.get('order_id'), to.get('lng'), to.get('lat'), (cur[0], cur[1])),
                    daemon=True,
                )
                t.start()
                # 更新本地位置终点（简化处理）
                cur[0], cur[1] = to.get('lng'), to.get('lat')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[无人机] 退出')
    finally:
        sock.close()
