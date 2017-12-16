import os, logging
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, \
    render_template, abort, g, flash, _app_ctx_stack, send_from_directory

# configuration
DATABASE = 'data.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def init_db():
        with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select user_id from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None


@app.teardown_appcontext
def close_db_connection(exception):
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from users where user_id = ?',
                          [session['user_id']], one=True)


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = query_db('''select * from users where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'No such user'
        elif user['password'] != request.form['password']:
            error = 'Invalid username or password'
        else:
            session['user_id'] = user['user_id']
            flash('You were logged in and can upload now')
            return redirect(url_for('upload'))
    return render_template('login.html', error=error)




@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error = None
    if not g.user:
        flash('You are not logged in')
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file is None:
            error = 'Invalid file'
        elif file is not None and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploads', filename=filename))
        else:
            error = 'The server encountered an internal error'
    return render_template('upload.html', error=error)


@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)  # when you want to download the file you can add parameter: as_attachment=True


if __name__ == '__main__':
    init_db()
    app.run()
