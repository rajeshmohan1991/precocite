from flask import render_template, flash, redirect, url_for, request, Response
from app import app, db
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from datetime import datetime
from app.forms import EditProfileForm, ResetPasswordRequestForm
from app.email import send_password_reset_email
from textblob import TextBlob
from functools import wraps

page_dict = {'viewer': 'landing', 'chat': 'index', 'learning': 'learning', 'working': 'blockchain'}
#status = current_user.current_mode
@app.route('/')
@app.route('/landing')
@login_required
def landing():
    status = current_user.current_mode
    posts = [
        {
            'author': {'title': 'Problem'},
            'body': 'Lack of web programming in rural India'
        },
        {
            'author': {'title': 'Solution'},
            'body': 'Use this platform!'
        }
    ]
    return render_template("landing.html", status=status, title='Home Page', posts=posts)

def check_gotstarted(landing):
    @wraps(landing)
    def decorated_function(*args, **kwargs):
        if current_user.current_mode == 'viewer':
            flash("You need to get started or complete this phase!")
            return redirect(url_for(page_dict[current_user.current_mode]))
        return landing(*args, **kwargs)
    return decorated_function

#@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
@check_gotstarted
def index():
#    user_mode = 'viewer'
    status = current_user.current_mode
    user_title = current_user.username.title()
    form = PostForm()
    if form.validate_on_submit():
        body = TextBlob(form.post.data)
        spell_checked_body = str(body.correct())
        post = Post(body=spell_checked_body, author=current_user)
        flash('Your post is now live!')
        testimonial = TextBlob(spell_checked_body)
        polarity = float(testimonial.sentiment.polarity)
        user_score = float(current_user.current_polarity)
        score = user_score + polarity
        current_user.current_polarity = score
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    userscore_reference = current_user.current_polarity
    int_polarity = int(float(current_user.current_polarity))
    if (int_polarity >= 1 and current_user.current_mode == 'chat') and (current_user.followers.count() or current_user.followed.count()):
        promote = 'true'
    else:
        promote = 'false' 
    posts = current_user.followed_posts().all()
    return render_template("index.html", status=status, title='Home Page', form=form, posts=posts, user_title=user_title, promote=promote)

@app.route('/explore')
@login_required
def explore():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', title='Explore', posts=posts)

def check_chat(landing):
    @wraps(landing)
    def decorated_function(*args, **kwargs):
        if (current_user.current_mode == 'viewer') or (current_user.current_mode == 'chat'):
            flash("You need to get started or complete this phase!")
            return redirect(url_for(page_dict[current_user.current_mode]))
        return landing(*args, **kwargs)    
    return decorated_function

@app.route('/learning')
@login_required
@check_chat
def learning():
    status = current_user.current_mode
    posts = [
        {
            'author': {'title': 'lesson1'},
            'body': 'Raspberry Pi is a minified network enabled computer!'
        },
        {
            'author': {'title': 'lesson2'},
            'body': 'Python is a powerful programming language!'
        }
    ]
    return render_template("learning.html", status=status, title='Learning Page', posts=posts)

def check_learnt(learning):
    @wraps(learning)
    def decorated_function(*args, **kwargs):
        if current_user.current_mode != 'working':
            flash("You need to get started or complete this phase!")
            return redirect(url_for(page_dict[current_user.current_mode]))
        return learning(*args, **kwargs)
    return decorated_function

@app.route('/blockchain')
@login_required
@check_learnt
def blockchain():
    posts = [
        {
            'author': {'title': 'hyperledger'},
            'body': 'Hyperledger is from Linux foundation!'
        },
        {
            'author': {'title': 'ethereum'},
            'body': 'Ethereum is the base of bitcoin!'
        }
    ]
    return render_template("blockchain.html", title='Blockchain Page', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('landing')
        elif user.current_mode == 'chat':
            next_page = url_for('index')
        elif user.current_mode == 'learning':
            next_page = url_for('learning')
        elif user.current_mode == 'working':
            next_page = url_for('blockchain')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))

@app.route('/gettingstarted')
@login_required
def gs():
    user = User.query.filter_by(username=current_user.username).first()
    if user.current_mode != 'chat':
        user.current_mode = 'chat'
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/startlearning')
@login_required
def sl():
    user = User.query.filter_by(username=current_user.username).first()
    if user.current_mode != 'learning':
        user.current_mode = 'learning'
        db.session.commit()
    return redirect(url_for('learning'))

@app.route('/startworking')
@login_required
def bc():
    user = User.query.filter_by(username=current_user.username).first()
    if user.current_mode != 'working':
        user.current_mode = 'working'
        db.session.commit()
    return redirect(url_for('blockchain'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, current_mode='viewer', current_polarity=0)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.all()
    return render_template('user.html',  user=user, posts=posts)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
