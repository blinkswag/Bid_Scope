from flask import render_template

def init_error_views(app):
    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('401.html'), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('500.html'), 500

    @app.route('/unauthorized')
    def unauthorized():
        return render_template('401.html'), 401
