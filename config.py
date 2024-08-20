import os

# 是否开启debug模式
DEBUG = False

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'root')
db_address = os.environ.get("MYSQL_ADDRESS", '127.0.0.1:3306')

ENV = os.environ.get("ENV", 'prod-8g6293i8889df8e0')
COS_BUCKET = os.environ.get("COS_BUCKET", '7072-prod-8g6293i8889df8e0-1259781903')