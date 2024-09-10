from routes.matches import matches_routes
from routes.api import api_routes
from api.player import player_api
from api.matches import match_api
from routes.nav import nav_routes
from app import app


if __name__ == '__main__':
    app.register_blueprint(matches_routes)
    app.register_blueprint(api_routes)
    app.register_blueprint(player_api)
    app.register_blueprint(match_api)
    app.register_blueprint(nav_routes)
    print(app.url_map)
    app.run(debug=True)
