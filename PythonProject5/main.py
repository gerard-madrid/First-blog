from flask import Flask, render_template , request , redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from  flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

connection = sqlite3.connect('sqlite.db', check_same_thread=False)
cursor = connection.cursor()

class User(UserMixin):
    def __init__(self, id,  username,  password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None

def close_db( connection=None):
    if connection is not None:
        connection.close()

@app.teardown_appcontext
def close_connection(exception):
    close_db()


@app.route('/')
def index():
    cursor.execute("""
    SELECT 
        post.id, post.title, post.content, user.username,
        COUNT(likes.post_id) AS likes
    FROM post
    JOIN user
        user ON post.author_id = user.id
    LEFT JOIN likes
         ON post_id = likes.post_id
    GROUP BY 
         post.id, post.title, post.content, user.username """)

    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        posts.append({'id': post[0], 'title': post[1], 'content': post[2], 'username': post[3], 'likes': post[4]})

        if current_user.is_authenticated:
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'",  )
            print(cursor.fetchall())
            likes_result = cursor.fetchall()
            likes_posts = []
            for like in likes_result:
                likes_posts.append(like[0])
            posts[-1]['likes_posts']=['id'] in likes_posts
            comments = cursor.execute(""" SELECT comments.post_id, user.username, comments.comment
             FROM comments
             Join user ON comments.user_id = user.id""").fetchall()
            context = {'posts': posts, 'comments': comments}
    return render_template('index.html', **context)


@app.route('/add/' , methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute('INSERT INTO post (title, content, author_id) VALUES (?,?,?)', (title, content,current_user.id))
        connection.commit()
        return redirect(url_for('index'))
    return render_template('add_post.html')

@app.route('/post/<post_id>')
def post(post_id):
    result = cursor.execute('SELECT * from post where id=?', (post_id,)).fetchone()
    post_dict = {'id': result[0], 'title': result[1], 'content': result[2]}
    return render_template('blog.html', post=post_dict)

@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            cursor.execute(
                "INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, generate_password_hash(password)))
            connection.commit()
            print("user registered successfully")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
         return render_template("register.html",message="username already exists")

    return render_template("register.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form["login_value"]
        password = request.form["password"]
        user = cursor.execute("SELECT * FROM user WHERE username = ? OR email = ?", (login_value,login_value)).fetchone()
        if user and User(user[0], user[1], user[2]).check_password(password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message="invalid username or password")
    return render_template("login.html")

@app.route("/delete/<int:post_id>/" , methods= ["POST"])
@login_required
def delete_post(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post and post[3] == current_user.id:
     cursor.execute("DELETE FROM post WHERE id = ?", (post_id,))
     connection.commit()
     return redirect(url_for('index'))
    else:
      return redirect(url_for('index'))

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def user_is_liking(user_id, post_id):
    likes = cursor.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?",  (user_id, post_id)).fetchone()
    return likes is not None

@app.context_processor
def utility_processor():
    return dict(user_is_liking=user_is_liking)



@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()



    if post:
        if user_is_liking(current_user.id, post_id):
            cursor.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (current_user.id, post_id))
            connection.commit()
            print("You unlike this post")
        else:
            cursor.execute(
                "INSERT INTO likes (user_id, post_id) VALUES (?, ?)",(current_user.id, post_id) )
            print("You like this post")

            connection.commit()
        return redirect(url_for('index'))
    return 'post not found', 404

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    comment =  request.form['comment']

    cursor.execute("INSERT INTO comments(post_id, user_id, comment) VALUES (?,?,?)", (post_id,current_user.id, comment)
                   )

    connection.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()

