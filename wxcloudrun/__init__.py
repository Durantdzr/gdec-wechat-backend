from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
from flask_jwt_extended import JWTManager
# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 设定数据库链接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/GDEC'.format(config.username, config.password,
                                                                             config.db_address)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)
# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views

# 加载配置
app.config.from_object('config')


