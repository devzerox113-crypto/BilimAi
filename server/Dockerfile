FROM python:3.12-slim
WORKDIR /app
COPY server.py admin.html ./
ENV DB_PATH=/data/bilimai.db PORT=8080
VOLUME /data
CMD ["python", "server.py"]
