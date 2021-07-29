# 基于python-flask生态 + HttpRunner 开发的rest风格的测试平台后端

## 线上预览：http://139.196.100.202/#/login  账号：tester、密码：123456

## 前端传送门：https://github.com/zhongyehai/api-test-front

## 系统操作手册：[gitee](https://gitee.com/Xiang-Qian-Zou/api-test-api/blob/master/%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8C.md) ，[github](https://github.com/zhongyehai/api-test-api/blob/main/%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8C.md)

## Python版本：python => 3.9+

### 1.安装依赖包：sudo pip install -i https://pypi.douban.com/simple/ -r requirements.txt

### 2.创建MySQL数据库，数据库名自己取，编码选择utf8mb4，对应config.yaml下db配置为当前数据库信息即可

### 3.初始化数据库表结构（项目根目录下依次执行下面3条命令）：
    sudo python dbMigration.py db init
    sudo python dbMigration.py db migrate
    sudo python dbMigration.py db upgrade

### 4.初始化权限、角色、管理员（项目根目录下执行，账号：admin，密码：123456）
    sudo python dbMigration.py init

### 5.生产环境下的一些配置:
    1.把后端端口改为8024启动
    2.为避免定时任务重复触发，需关闭debug模式（debug=False或去掉debug参数）
    3.准备好前端包，并在nginx.location / 下指定前端包的路径
    4.直接把项目下的nginx.conf文件替换nginx下的nginx.conf文件
    5.nginx -s reload 重启nginx

### 6.启动项目
    开发环境: 运行 main.py
    生产环境: 
        使用配置文件: sudo nohup gunicorn -c gunicornConfig.py main:app &
        不使用配置文件: sudo nohup gunicorn -w 3 -b 0.0.0.0:8024 main:app –preload &
    
    如果报 gunicorn 命令不存在，则先找到 gunicorn 安装目录，创建软连接
    ln -s /usr/local/python3/bin/gunicorn /usr/bin/gunicorn
    ln -s /usr/local/python3/bin/gunicorn  /usr/local/bin/gunicorn
    sudo nohup /usr/local/bin/gunicorn -w 1 -b 0.0.0.0:8024 main:app –preload &

### 修改依赖后创建依赖：sudo pip freeze > requirements.txt


### 7.项目逻辑
    1.项目数据管理：项目 --> 模块 --> 接口
    2.用例数据管理：项目 --> 用例集 --> 用例 --> 步骤（由接口转化而来）
    3.自定义变量：
        1.在项目管理可以创建项目级的自定义变量，在需要使用的时候用 "$变量名" 引用
        2.在用例管理可以创建用例级的自定义变量，在需要使用的时候用 "$变量名" 引用
    4.辅助函数
        1.在自定义函数模块下可以创建用于辅助实现某些功能的py脚本，里面可以创建函数用于实现平台未提供的功能
        2.使用：
            1.在项目管理 或者用例管理，引用此文件
            2.在需要使用的地方，用  "${函数名（参数）}" 引用
    5.参数传递
        1.在每个步骤中都有一个数据提取的模块，此模块支持xpath提取，逻辑为 key: 变量名、value: xpath
        2.当数据提取出来过后，在用例中就可以使用 "$变量名" 引用
    6.支持跨项目的接口组装为用例
        当用例需要多个项目的接口组装为一条用例的时候，支持按需引用，即需要哪个项目的哪个接口，就引入该接口即可

### 创作不易，麻烦给个星哦

### QQ交流群：249728408
### 博客地址：https://www.cnblogs.com/zhongyehai/
