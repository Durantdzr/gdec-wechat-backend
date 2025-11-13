import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", '')
password = os.environ.get("MYSQL_PASSWORD", '')
db_address = os.environ.get("MYSQL_ADDRESS", '')
database = os.environ.get("MYSQL_database", '')
ENV = os.environ.get("ENV", '')
COS_BUCKET = os.environ.get("COS_BUCKET", '')
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", 'your-secret-key')
FERNET_KEY = os.environ.get("FERNET_KEY", '')

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", '*')

VERSION = os.environ.get("VERSION", '')

SecretId = os.environ.get("SecretId", '')
SecretKey = os.environ.get("SecretKey", '')
SdkAppId= os.environ.get("SdkAppId", '')

CA_url = os.environ.get("CA_url", "")
CA_appId = os.environ.get("CA_appId", '')
CA_appSecret = os.environ.get("CA_appSecret", '')

TOY_MAX_NUM=os.environ.get("TOY_MAX_NUM", 10)

MAX_LOGIN_ERROR_TIMES=os.environ.get("MAX_LOGIN_ERROR_TIMES", 5)
LOGIN_ERROR_LOCK_TIME=os.environ.get("LOGIN_ERROR_LOCK_TIME", 5)