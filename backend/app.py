# Flask 后端 —— 与微信小程序通信的最小示例
from flask import Flask, request, jsonify

app = Flask(__name__)

# 内存存储：{openid: {longitude, latitude}}  （重启会清空，仅用于测试）
STORE = {}


@app.route("/", methods=["GET"])
def index():
    """健康检查：浏览器直接打开能看到，说明服务活着"""
    return jsonify({"code": 0, "msg": "Flask 服务运行中"})


@app.route("/hello", methods=["GET"])
def hello():
    """最简单的连通性测试接口（GET）"""
    name = request.args.get("name", "微信小程序")
    return jsonify({"code": 0, "msg": f"你好，{name}！后端已收到请求"})


@app.route("/save", methods=["POST"])
def save():
    """保存：接收 JSON {openid, longitude, latitude}"""
    body = request.get_json(silent=True) or {}
    openid = body.get("openid", "anonymous")
    longitude = body.get("longitude", "")
    latitude = body.get("latitude", "")

    if not longitude or not latitude:
        return jsonify({"code": -1, "msg": "经纬度不能为空"}), 400

    STORE[openid] = {"longitude": longitude, "latitude": latitude}
    return jsonify({"code": 0, "msg": "保存成功", "data": STORE[openid]})


@app.route("/get", methods=["GET"])
def get_record():
    """读取：?openid=xxx"""
    openid = request.args.get("openid", "anonymous")
    record = STORE.get(openid)
    if not record:
        return jsonify({"code": 0, "msg": "暂无记录", "data": None})
    return jsonify({"code": 0, "msg": "读取成功", "data": record})


if __name__ == "__main__":
    # 云托管要求监听 0.0.0.0；本地调试用 5000 端口
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
