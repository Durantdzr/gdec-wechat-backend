import os

# 是否开启debug模式
DEBUG = False

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", '')
password = os.environ.get("MYSQL_PASSWORD", '')
db_address = os.environ.get("MYSQL_ADDRESS", '')

ENV = os.environ.get("ENV", '')
COS_BUCKET = os.environ.get("COS_BUCKET", '')
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", 'your-secret-key')

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", '*')