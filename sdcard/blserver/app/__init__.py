from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='/sdcard/blserver/database.db',
        CONFIG_DIR='/sdcard/blserver/conf',
        LOGS_DIR='/sdcard/blserver/logs',
        PIDS_DIR='/sdcard/blserver/pids',
        DEFAULT_DNS='1.1.1.1',
        FAKE_IP='192.168.14.190'
    )
    
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app
