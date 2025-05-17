# wp_analyzer/__init__.py

import os
from flask import Flask, render_template
from flask_cors import CORS

def create_app():
    # Crea la Flask app, specificando dove cercare i template e gli static
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
    )
    CORS(app)

    # registra i blueprint (senza url_prefix qui, li mettiamo negli import stessi)
    from .content         import bp as content_bp;        app.register_blueprint(content_bp,        url_prefix='/analyze/content')
    from .seo             import bp as seo_bp;            app.register_blueprint(seo_bp,            url_prefix='/analyze/seo')
    from .performance     import bp as perf_bp;           app.register_blueprint(perf_bp,           url_prefix='/analyze/performance')
    from .lighthouse      import bp as lh_bp;             app.register_blueprint(lh_bp,             url_prefix='/analyze/lighthouse')
    from .accessibility   import bp as access_bp;         app.register_blueprint(access_bp,         url_prefix='/analyze/accessibility')
    from .security        import bp as sec_bp;            app.register_blueprint(sec_bp,            url_prefix='/analyze/security')
    from .theme_plugin    import bp as tp_bp;             app.register_blueprint(tp_bp,             url_prefix='/analyze/theme-plugin')
    from .users           import bp as users_bp;          app.register_blueprint(users_bp,          url_prefix='/analyze/users')
    from .broken          import bp as broken_bp;         app.register_blueprint(broken_bp,         url_prefix='/analyze/broken')
    from .reports         import bp as reports_bp;        app.register_blueprint(reports_bp,        url_prefix='/reports')
    from .export_csv      import bp as export_csv_bp;     app.register_blueprint(export_csv_bp)

    @app.route('/')
    def index():
        # usa render_template, non send_from_directory
        return render_template('index.html')

    return app

# Se lanci con `python -m wp_analyzer`
if __name__ == '__main__':
    create_app().run(debug=True)
