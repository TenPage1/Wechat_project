# admin.py —— 管理员后台（简易网页，Flask Blueprint）
# 访问：http://域名/admin?token=管理密码
import os

from flask import Blueprint, request, render_template_string, redirect

import db

admin_bp = Blueprint('admin', __name__)

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'admin123')   # 生产环境请在云托管配环境变量


def check_token():
    return request.args.get('token') == ADMIN_TOKEN


PAGE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DroneAED 管理后台</title>
<style>
  body { font-family: -apple-system, "Microsoft YaHei", sans-serif; margin: 0; background: #f5f7fa; color: #1f2937; }
  header { background: #2563eb; color: #fff; padding: 16px 24px; font-size: 18px; font-weight: 600; }
  .wrap { max-width: 1080px; margin: 24px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }
  h2 { font-size: 17px; margin: 0 0 16px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { text-align: left; padding: 10px; border-bottom: 1px solid #eef1f5; }
  th { color: #6b7280; font-weight: 500; }
  input, select { padding: 8px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; width: 100%; box-sizing: border-box; }
  .row { display: flex; gap: 10px; margin-bottom: 12px; }
  button { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 10px 18px; font-size: 14px; cursor: pointer; }
  button.danger { background: #ef4444; }
  .actions a { color: #2563eb; text-decoration: none; margin-right: 12px; font-size: 13px; }
  .tag { font-size: 12px; padding: 2px 8px; border-radius: 6px; background: #eef1f5; color: #6b7280; }
</style>
</head>
<body>
<header>🚁 DroneAED 调度中枢 · 管理后台</header>
<div class="wrap">

  <div class="card">
    <h2>无人机点位管理</h2>
    <table>
      <tr><th>ID</th><th>类型</th><th>名称</th><th>经度</th><th>纬度</th><th>二维码ID</th><th>状态</th><th>操作</th></tr>
      {% for p in points %}
      <tr>
        <td>{{p.id}}</td>
        <td>{{'起飞点' if p.type=='takeoff' else '停靠点'}}</td>
        <td>{{p.name}}</td>
        <td>{{p.longitude}}</td>
        <td>{{p.latitude}}</td>
        <td>{{p.qr_id or '-'}}</td>
        <td><span class="tag">{{p.status}}</span></td>
        <td class="actions">
          <a href="/admin/point/delete?id={{p.id}}&token={{token}}" onclick="return confirm('确认删除？')">删除</a>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>新增点位</h2>
    <form method="post" action="/admin/point/add?token={{token}}">
      <div class="row">
        <select name="type">
          <option value="takeoff">起飞点</option>
          <option value="landing">停靠点</option>
        </select>
        <input name="name" placeholder="点位名称" required>
      </div>
      <div class="row">
        <input name="longitude" placeholder="经度" required>
        <input name="latitude" placeholder="纬度" required>
        <input name="qr_id" placeholder="二维码ID（停靠点必填）">
      </div>
      <button type="submit">添加点位</button>
    </form>
  </div>

  <div class="card">
    <h2>用户列表</h2>
    <table>
      <tr><th>ID</th><th>openid</th><th>创建时间</th><th>操作</th></tr>
      {% for u in users %}
      <tr>
        <td>{{u.id}}</td>
        <td style="word-break:break-all;">{{u.openid}}</td>
        <td>{{u.create_time}}</td>
        <td class="actions"><a href="/admin/user/delete?id={{u.id}}&token={{token}}" onclick="return confirm('确认删除？')">删除</a></td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>呼叫订单</h2>
    <table>
      <tr><th>ID</th><th>用户</th><th>无人机</th><th>目的点位</th><th>状态</th><th>无人机位置</th><th>时间</th></tr>
      {% for o in orders %}
      <tr>
        <td>{{o.id}}</td>
        <td style="word-break:break-all;">{{o.user_openid}}</td>
        <td>{{o.drone_id}}</td>
        <td>{{o.to_point_id}}</td>
        <td><span class="tag">{{o.status}}</span></td>
        <td>{{o.drone_lng}}, {{o.drone_lat}}</td>
        <td>{{o.create_time}}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>用户建议</h2>
    <table>
      <tr><th>ID</th><th>用户</th><th>内容</th><th>时间</th></tr>
      {% for f in feedbacks %}
      <tr>
        <td>{{f.id}}</td>
        <td style="word-break:break-all;">{{f.openid}}</td>
        <td>{{f.content}}</td>
        <td>{{f.create_time}}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

</div>
</body>
</html>
'''


@admin_bp.route('/admin')
def admin_home():
    if not check_token():
        return '<h3>无权限：请在 URL 后加 ?token=你的管理密码</h3>', 403
    return render_template_string(
        PAGE,
        token=request.args.get('token'),
        points=db.list_points(),
        users=db.list_users(),
        orders=db.list_orders(),
        feedbacks=db.list_feedback(),
    )


@admin_bp.route('/admin/point/add', methods=['POST'])
def admin_add_point():
    if not check_token():
        return '无权限', 403
    db.add_point({
        'type': request.form.get('type'),
        'name': request.form.get('name'),
        'longitude': float(request.form.get('longitude')),
        'latitude': float(request.form.get('latitude')),
        'qr_id': request.form.get('qr_id') or None,
    })
    return redirect('/admin?token=' + request.args.get('token'))


@admin_bp.route('/admin/point/delete')
def admin_delete_point():
    if not check_token():
        return '无权限', 403
    db.delete_point(request.args.get('id', type=int))
    return redirect('/admin?token=' + request.args.get('token'))


@admin_bp.route('/admin/user/delete')
def admin_delete_user():
    if not check_token():
        return '无权限', 403
    db.delete_user(request.args.get('id', type=int))
    return redirect('/admin?token=' + request.args.get('token'))
