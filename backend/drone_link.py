# drone_link.py —— 后端与无人机的 TCP 通信通道
# 协议：一行一个 JSON，以 \n 分隔
#   后端 -> 无人机 : {"cmd":"goto","order_id":1,"to":{"lng":..,"lat":..}}
#   无人机 -> 后端 : {"type":"hello","drone_id":1}
#                    {"type":"position","order_id":1,"lng":..,"lat":..,"status":"flying"}
import json
import socket
import threading

import db

TCP_HOST = '0.0.0.0'
TCP_PORT = 9000

# 在线的无人机连接： {drone_id: socket}
_clients = {}
_lock = threading.Lock()


def send_to_drone(drone_id, payload: dict):
    """向指定无人机发送一条 JSON 指令"""
    with _lock:
        sock = _clients.get(drone_id)
    if not sock:
        return False
    try:
        line = (json.dumps(payload, ensure_ascii=False) + '\n').encode('utf-8')
        sock.sendall(line)
        return True
    except Exception as e:
        print(f'[TCP] 发送给无人机 {drone_id} 失败: {e}')
        with _lock:
            _clients.pop(drone_id, None)
        return False


def online_drones():
    with _lock:
        return list(_clients.keys())


def _handle_client(sock, addr):
    print(f'[TCP] 无人机已连接: {addr}')
    drone_id = None
    buf = b''
    try:
        while True:
            data = sock.recv(4096)
            if not data:
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
                    print(f'[TCP] 非法消息: {line}')
                    continue
                _on_message(drone_id, msg)
                # hello 之后绑定 drone_id
                if msg.get('type') == 'hello':
                    drone_id = msg.get('drone_id')
                    with _lock:
                        _clients[drone_id] = sock
                    db.set_drone_status(drone_id, 'idle')
                    print(f'[TCP] 无人机 {drone_id} 已注册')
    except Exception as e:
        print(f'[TCP] 连接异常: {e}')
    finally:
        if drone_id is not None:
            with _lock:
                _clients.pop(drone_id, None)
            db.set_drone_status(drone_id, 'offline')
            print(f'[TCP] 无人机 {drone_id} 已离线')
        sock.close()


def _on_message(drone_id, msg):
    """处理无人机上报的消息"""
    mtype = msg.get('type')
    if mtype == 'position':
        oid = msg.get('order_id')
        lng = msg.get('lng')
        lat = msg.get('lat')
        status = msg.get('status')          # flying / arrived / done
        if drone_id is not None:
            db.set_drone_position(drone_id, lng, lat)
        if oid:
            fields = {'drone_lng': lng, 'drone_lat': lat}
            if status == 'arrived':
                fields['status'] = 'arrived'
            elif status == 'done':
                fields['status'] = 'done'
            db.update_order(oid, **fields)
        print(f'[TCP] 无人机 {drone_id} 上报位置: ({lng},{lat}) 订单{oid} {status}')


def start_tcp_server():
    """在后台线程启动 TCP 服务器"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((TCP_HOST, TCP_PORT))
    srv.listen(8)
    print(f'[TCP] 无人机 TCP 服务已启动，监听 {TCP_HOST}:{TCP_PORT}')

    def loop():
        while True:
            try:
                sock, addr = srv.accept()
                t = threading.Thread(target=_handle_client, args=(sock, addr), daemon=True)
                t.start()
            except Exception as e:
                print(f'[TCP] accept 异常: {e}')

    threading.Thread(target=loop, daemon=True).start()
