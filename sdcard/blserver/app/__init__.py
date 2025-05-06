from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='/workspaces/httpl/sdcard/blserver/database.db',
        CONFIG_DIR='/workspaces/httpl/sdcard/blserver/conf',
        LOGS_DIR='/workspaces/httpl/sdcard/blserver/logs',
        PIDS_DIR='/workspaces/httpl/sdcard/blserver/pids',
        DEFAULT_DNS='1.1.1.1',
        FAKE_IP='192.168.14.190'
    )
    
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app
