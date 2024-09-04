from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_apscheduler import APScheduler

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 设定数据库链接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/GDEC'.format(config.username, config.password,
                                                                       config.db_address)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
jwt = JWTManager(app)
CORS(app, resources={r"/api/manage/*": {"origins": config.CORS_ORIGINS}},supports_credentials=True)
# 初始化DB操作对象
db = SQLAlchemy(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

from wxcloudrun.cronjob import send_begin_msg
@scheduler.task('interval', id='send_begin_msg', hours=1, misfire_grace_time=900)
def job1():
    send_begin_msg()

# 加载控制器
from wxcloudrun import views, mangerviews

# 加载配置
app.config.from_object('config')
