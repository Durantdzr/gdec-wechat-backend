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

TOY_MAX_NUM=int(os.environ.get("TOY_MAX_NUM", 10))

MAX_LOGIN_ERROR_TIMES=os.environ.get("MAX_LOGIN_ERROR_TIMES", 5)
LOGIN_ERROR_LOCK_TIME=os.environ.get("LOGIN_ERROR_LOCK_TIME", 5)

DOOR_OPEN_TIME=os.environ.get("DOOR_OPEN_TIME", 1764000000)
DOOR_CLOSE_TIME=os.environ.get("DOOR_CLOSE_TIME", 1764037800)
OPEN_SCHEDULE_ID=os.environ.get("OPEN_SCHEDULE_ID", 413)
MAIN_SCHEDULE_ID=os.environ.get("MAIN_SCHEDULE_ID", 447)
OPEN_SCHEDULE_COLOR=os.environ.get("OPEN_SCHEDULE_COLOR", "#3482CA")
MAIN_SCHEDULE_COLOR=os.environ.get("MAIN_SCHEDULE_COLOR", "#FC8328")
BLACK_COLOR=os.environ.get("BLACK_COLOR", "#000000")
ERCODE_EXCHANGE_TIME=os.environ.get("ERCODE_EXCHANGE_TIME", 1764042300)
VIP_USAGE_TIMES=int(os.environ.get("VIP_USAGE_TIMES", 4))


CACHE_TYPE = os.environ.get("CACHE_TYPE", "simple")
CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 60))
CACHE_ENABLED = int(os.environ.get("CACHE_ENABLED", 1))