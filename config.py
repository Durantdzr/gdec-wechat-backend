import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'shdata')
password = os.environ.get("MYSQL_PASSWORD", 'Qwer123$')
db_address = os.environ.get("MYSQL_ADDRESS", 'sh-cynosdbmysql-grp-m9l8ybb0.sql.tencentcdb.com:27614')
database = os.environ.get("MYSQL_database", 'GDEC-test')
ENV = os.environ.get("ENV", '')
COS_BUCKET = os.environ.get("COS_BUCKET", '7072-prod-5g9xtpt32ae0a1e3-1328915519')
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", 'your-secret-key')
FERNET_KEY = os.environ.get("FERNET_KEY", 'bCYvy-zUKWPlf0_KC4yiJYDcIXU1IsM1cvjf5hpo7tQ=')

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", '*')

VERSION = os.environ.get("VERSION", '')