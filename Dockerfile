# 使用官方的Python基础镜像
FROM python:3.12

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的/app中
COPY . /app

# 安装项目依赖
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 暴露容器的端口
EXPOSE 8000

# 定义容器启动时运行的命令
CMD ["python", "main.py"]