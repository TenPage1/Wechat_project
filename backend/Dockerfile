# 微信云托管构建用的 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY . .

# 云托管要求监听 0.0.0.0；端口与 app.py 里的 PORT 保持一致
ENV PORT=80
EXPOSE 80

# 生产环境用 gunicorn 启动（比 flask 内置服务器稳）
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]
