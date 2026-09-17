# app.py —— DroneAED 调度中枢后端（Flask）
import os

from flask import Flask, request, jsonify

import db
import drone_link

app = Flask(__name__)

# 注册管理员后台
from admin import admin_bp
app.register_blueprint(admin_bp)

# 微信小程序的 appid / secret（用于 code2Session）
WX_APPID = os.environ.get('WX_APPID', 'wx181ece3a549b2b1e')
WX_SECRET = os.environ.get('WX_SECRET', '')   # 需在云托管环境变量里配


def ok(data=None, msg='ok'):
    return jsonify({'code': 0, 'msg': msg, 'data': data})


def err(msg, code=-1, http=400):
    return jsonify({'code': code, 'msg': msg}), http


# ==================== 基础 ====================
@app.route('/', methods=['GET'])
def index():
    return jsonify({'code': 0, 'msg': 'DroneAED 调度中枢运行中'})


@app.route('/hello', methods=['GET'])
def hello():
    name = request.args.get('name', '小程序')
    return jsonify({'code': 0, 'msg': f'你好，{name}！后端已收到请求'})


# ==================== 登录 ====================
@app.route('/api/login', methods=['POST'])
def login():
    """微信登录：传 code，后端换 openid
    （未配置 secret 时进入 mock 模式，便于 PC 调试）"""
    body = request.get_json(silent=True) or {}
    code = body.get('code')

    if WX_SECRET:
        import json as _json
        import urllib.request
        url = ('https://api.weixin.qq.com/sns/jscode2session'
               f'?appid={WX_APPID}&secret={WX_SECRET}&js_code={code}&grant_type=authorization_code')
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                r = _json.loads(resp.read().decode('utf-8'))
            openid = r.get('openid')
        except Exception as e:
            return err('微信登录失败: ' + str(e))
    else:
        openid = 'mock_' + (code or 'guest')

    if not openid:
        return err('未获取到 openid')

    user = db.get_or_create_user(openid)
    return ok({'openid': openid, 'user_id': user['id']})


# ==================== 点位 ====================
@app.route('/api/points/nearby', methods=['GET'])
def points_nearby():
    """返回所有可用点位（前端再按距离排序）"""
    return ok(db.list_points())


@app.route('/api/points/scan', methods=['GET'])
def points_scan():
    """扫码：按二维码 ID 获取停靠点信息 ?qr_id=xxx"""
    qr_id = request.args.get('qr_id')
    p = db.get_point_by_qr(qr_id)
    if not p:
        return err('二维码无效', http=404)
    return ok(p)


# ==================== 呼叫无人机 ====================
@app.route('/api/call', methods=['POST'])
def call_drone():
    """呼叫无人机 入参：{openid, to_point_id}"""
    body = request.get_json(silent=True) or {}
    openid = body.get('openid')
    to_point_id = body.get('to_point_id')

    if not openid or not to_point_id:
        return err('参数不完整：需要 openid 和 to_point_id')

    to_point = db.get_point(to_point_id)
    if not to_point:
        return err('目的点位不存在')

    drone = db.get_idle_drone()
    if not drone:
        return err('暂无空闲无人机，请稍后再试')

    takeoffs = [p for p in db.list_points() if p['type'] == 'takeoff']
    from_point = takeoffs[0] if takeoffs else None

    order_id = db.create_order(
        openid,
        from_point['id'] if from_point else None,
        to_point_id,
        drone['id']
    )

    db.set_drone_status(drone['id'], 'busy')
    db.update_order(order_id, status='taking_off')

    sent = drone_link.send_to_drone(drone['id'], {
        'cmd': 'goto',
        'order_id': order_id,
        'to': {'lng': to_point['longitude'], 'lat': to_point['latitude']}
    })

    return ok({
        'order_id': order_id,
        'drone_id': drone['id'],
        'sent': sent,
        'to_point': to_point
    })


@app.route('/api/order/status', methods=['GET'])
def order_status():
    """轮询订单 + 无人机实时位置 ?order_id=1"""
    oid = request.args.get('order_id', type=int)
    order = db.get_order(oid)
    if not order:
        return err('订单不存在', http=404)
    return ok(order)


# ==================== 个人中心 ====================
@app.route('/api/history', methods=['GET'])
def history():
    openid = request.args.get('openid')
    if not openid:
        return err('缺少 openid')
    return ok(db.list_orders(openid))


@app.route('/api/feedback', methods=['POST'])
def feedback():
    body = request.get_json(silent=True) or {}
    openid = body.get('openid')
    content = (body.get('content') or '').strip()
    if not content:
        return err('建议内容不能为空')
    db.add_feedback(openid, content)
    return ok(msg='感谢你的建议！')


# ==================== 调试：模拟无人机移动（无真实无人机时用） ====================
@app.route('/api/debug/simulate_move', methods=['POST'])
def debug_simulate_move():
    body = request.get_json(silent=True) or {}
    oid = body.get('order_id')
    order = db.get_order(oid)
    if not order:
        return err('订单不存在')
    to_point = db.get_point(order['to_point_id'])
    cur_lng = order['drone_lng'] or (to_point['longitude'] - 0.01)
    cur_lat = order['drone_lat'] or (to_point['latitude'] - 0.01)

    step = 0.2
    nlng = cur_lng + (to_point['longitude'] - cur_lng) * step
    nlat = cur_lat + (to_point['latitude'] - cur_lat) * step
    reached = abs(nlng - to_point['longitude']) < 1e-4 and abs(nlat - to_point['latitude']) < 1e-4
    status = 'arrived' if reached else 'flying'

    db.update_order(oid, drone_lng=nlng, drone_lat=nlat, status=status)
    db.set_drone_position(order['drone_id'], nlng, nlat)
    if reached:
        db.set_drone_status(order['drone_id'], 'idle')
    return ok({'drone_lng': nlng, 'drone_lat': nlat, 'status': status})


# ==================== 启动 ====================
db.init_db()
drone_link.start_tcp_server()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)

