import os
import subprocess
from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, SpellCheckerForm, HistoryForm, QueryReviewForm
from app.models import User, UserLoginHistory, UserServiceHistory
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Spell Checker Home')

@app.route("/register", methods=['GET','POST'])
def register():
    result_str = " "
    form = RegistrationForm()
    if request.method == 'GET':
        return render_template('register.html', title='Register', form=form, result_str=result_str)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, phone=form.phone.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        result_str = "success"
        flash('success - Your account has been created - please log in!', 'success')
    else:
        result_str = "failure"        
        flash('failure - Acount Registration failed - please try again!', 'danger')
    return render_template('register.html', title='Register', form=form, result_str=result_str)
    
@app.route("/login", methods=['GET','POST'])
def login():
    result_str = " "
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not bcrypt.check_password_hash(user.password, form.password.data):
            result_str = "Incorrect Two-factor failure"
            flash('Two-factor failure - Login Unsuccessfull', 'danger')
        elif user.phone != form.phone.data:
            result_str = "Incorrect Two-factor failure"
            flash('Two-factor failure - Login Unsuccessfull', 'danger')
        else:
            result_str = "success."
            login_user(user, remember=form.remember.data)
            login_record = UserLoginHistory(user_id = user.id, time_login=datetime.now(), time_logout=None)
            db.session.add(login_record)
            db.session.commit()
    return render_template('login.html', title='Login', form=form, result_str=result_str)

@app.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        try:
            login_records = UserLoginHistory.query.filter(UserLoginHistory.user_id == current_user.id).\
                                                  filter(UserLoginHistory.time_logout == None).\
                                                  filter(UserLoginHistory.time_login < datetime.now()).all()
        except:
            return redirect(url_for('home'))

        if not login_records is None:
            for login_record in login_records:
                login_record.time_logout = datetime.now()
            db.session.commit()

        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()
        logout_user()
    return redirect(url_for('home'))

@app.route("/spell_check", methods=['GET','POST'])
@login_required
def spellcheck():
    if (not current_user.is_authenticated):
        return redirect(url_for('login'))
    form = SpellCheckerForm()
    if form.validate_on_submit():
        input_text = form.input_content.data

        if (str(os.getenv('OS'))[:3] == "Win"):
            spellcheck_file_path = os.path.join(app.root_path, 'spell_check\spell_check.exe')
            input_file_path = os.path.join(app.root_path, 'spell_check\input.txt')
            wordlist_file_path = os.path.join(app.root_path, 'spell_check\wordlist.txt')
        else:
            # spellcheck_file_path = './a.out'
            spellcheck_file_path = os.path.join(app.root_path,  'spell_check/a.out')
            input_file_path = os.path.join(app.root_path, 'spell_check/input.txt')
            wordlist_file_path = os.path.join(app.root_path, 'spell_check/wordlist.txt')
        
        with open(input_file_path, 'w') as f:
            f.write(str(input_text))
        if not f:
            flash('Error creating input file for spell checker!', 'danger')
            return redirect(url_for('spellcheck'))

        form.input_content.data = input_text
        form.output_content.data = input_text
        misspelled_words = subprocess.check_output([spellcheck_file_path, input_file_path, wordlist_file_path], stderr=subprocess.STDOUT).decode('utf-8')

        if (str(os.getenv('OS'))[:3] == "Win"):
            form.misspelled_content.data = misspelled_words.replace("\r", ", ").replace("\n", "").strip()[:-1]
        else:
            form.misspelled_content.data = misspelled_words.replace("\n", ", ").strip()[:-1]

        service_record = UserServiceHistory(user_id = current_user.id, date_posted = datetime.now(), input_content = input_text, misspelled_content = form.misspelled_content.data)
        db.session.add(service_record)
        db.session.commit()

    return render_template('spellcheck.html', form=form)

@app.route("/history", strict_slashes=False, methods=['GET','POST'])
@login_required
def history():
    if (not current_user.is_authenticated):
        return redirect(url_for('login'))
    try:
        form = HistoryForm()
        if request.method == 'GET':
            service_records_cnt = UserServiceHistory.query.filter(UserServiceHistory.user_id == current_user.id).count()
            service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username, UserServiceHistory.input_content, UserServiceHistory.date_posted).\
                                    join(User, User.id == UserServiceHistory.user_id).\
                                    filter(UserServiceHistory.user_id == current_user.id).\
                                    order_by(UserServiceHistory.date_posted.asc()).all()
            return render_template('history.html', title='History', form=form,
                                   service_records_cnt=service_records_cnt, service_records=service_records)
    except:
        return redirect(url_for('home'))

    if form.validate_on_submit():
        if current_user.username != 'admin':
            return redirect(url_for('history'))

        if form.username.data == '*':
            service_records_cnt = UserServiceHistory.query.count()
            service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                     UserServiceHistory.input_content,
                                                                     UserServiceHistory.date_posted). \
                                                    join(User, User.id == UserServiceHistory.user_id). \
                                                    order_by(UserServiceHistory.date_posted.asc()).all()
        else:
            user = User.query.filter(User.username == form.username.data).first()
            if not user:
                flash('failure - invalid user entered - please try again!', 'danger')
                return redirect(url_for('history'))

            service_records_cnt = UserServiceHistory.query.filter(UserServiceHistory.user_id == user.id).count()
            service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                     UserServiceHistory.input_content,
                                                                     UserServiceHistory.date_posted). \
                                                    join(User, User.id == UserServiceHistory.user_id). \
                                                    filter(UserServiceHistory.user_id == user.id). \
                                                    order_by(UserServiceHistory.date_posted.asc()).all()
        return render_template('history.html', title='History', form=form, service_records_cnt=service_records_cnt, service_records=service_records)

    return redirect(url_for('history'))

@app.route("/history/<user_clicked>", methods=['GET','POST'])
@login_required
def historyfor(user_clicked):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if user_clicked[0:5] == 'query':
        # return redirect(url_for('reviewquery', 'user_clicked'))
        return reviewquery(user_clicked)

    if user_clicked and (user_clicked != current_user.username) and (current_user.username != 'admin'):
        user_clicked = current_user.username
    if (not user_clicked) or (user_clicked is None) or (user_clicked == 'None'):
        user_clicked = current_user.username

    try:
        form = HistoryForm()
        if request.method == 'GET':
            if user_clicked == '*':
                service_records_cnt = UserServiceHistory.query.count()
                service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                         UserServiceHistory.input_content,
                                                                         UserServiceHistory.date_posted). \
                                                        join(User, User.id == UserServiceHistory.user_id). \
                                                        order_by(UserServiceHistory.date_posted.asc()).all()
            else:

                user = User.query.filter(User.username == user_clicked).first()
                if not user:
                    flash('Error - User does not exist!', 'danger')
                    return redirect(url_for('history'))
                service_records_cnt = UserServiceHistory.query.filter(UserServiceHistory.user_id == user.id).count()
                service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                         UserServiceHistory.input_content,
                                                                         UserServiceHistory.date_posted). \
                                                        join(User, User.id == UserServiceHistory.user_id). \
                                                        filter(UserServiceHistory.user_id == user.id). \
                                                        order_by(UserServiceHistory.date_posted.asc()).all()
            return render_template('history.html', title='History', form=form, service_records_cnt=service_records_cnt, service_records=service_records)

        if form.validate_on_submit():
            if current_user.username != 'admin':
                return redirect(url_for('history'))

            if form.username.data == '*':
                service_records_cnt = UserServiceHistory.query.count()
                service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                         UserServiceHistory.input_content,
                                                                         UserServiceHistory.date_posted). \
                                                        join(User, User.id == UserServiceHistory.user_id). \
                                                        order_by(UserServiceHistory.date_posted.asc()).all()
            else:
                user = User.query.filter(User.username == form.username.data).first()
                if not user:
                    flash('failure - invalid user entered - please try again!', 'danger')
                    return redirect(url_for('history'))

                service_records_cnt = UserServiceHistory.query.filter(UserServiceHistory.user_id == user.id).count()
                service_records = UserServiceHistory.query.with_entities(UserServiceHistory.id, User.username,
                                                                         UserServiceHistory.input_content,
                                                                         UserServiceHistory.date_posted). \
                                                        join(User, User.id == UserServiceHistory.user_id). \
                                                        filter(UserServiceHistory.user_id == user.id). \
                                                        order_by(UserServiceHistory.date_posted.asc()).all()
            return render_template('history.html', title='History', form=form, service_records_cnt=service_records_cnt, service_records=service_records)
    except:
        return redirect(url_for('home'))

@app.route("/history/<querynum>", methods=['GET','POST'])
@login_required
def reviewquery(querynum):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if querynum[0:5] != 'query':
        historyfor(querynum)

    try:
        queryid = querynum[5:]
        query = UserServiceHistory.query.filter(UserServiceHistory.id == queryid).first()
        if not query:
            return redirect(url_for('history'))
        # check if queryid passed in belongs to current_user
        # UserServiceHistory.user_id == current_user.id
        if not (current_user.username == 'admin'):
            if not query.user_id == current_user.id:
                return redirect(url_for('history'))

        form = QueryReviewForm()
        form.query_text.data = query.input_content
        form.query_results.data = query.misspelled_content

        if request.method == 'GET':
            user = User.query.filter(User.id == query.user_id).first()
            if not user:
                return redirect(url_for('history'))
            return render_template('queryreview.html', title='Query Review', form=form,
                                    queryid=queryid, username=user.username, querytext=query.input_content,
                                    queryresults=query.misspelled_content, querydate=str(query.date_posted)[:-7])
    except:
        return redirect(url_for('history'))

@app.route("/login_history/", defaults={'user_clicked': None}, methods=['GET','POST'])
@app.route("/login_history/<user_clicked>", methods=['GET','POST'])
@login_required
def loginhistory(user_clicked):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if not (current_user.username == 'admin'):
        return redirect(url_for('home'))

    try:
        form = HistoryForm()
        if request.method == 'GET':
            if not user_clicked:
                user_name = current_user.username
            else:
                user_name = user_clicked
                if user_name == '*':
                    activity_records_cnt = UserLoginHistory.query.count()
                    activity_records = UserLoginHistory.query.with_entities(UserLoginHistory.id, User.username,
                                                                             UserLoginHistory.time_login,
                                                                             UserLoginHistory.time_logout). \
                                                            join(User, User.id == UserLoginHistory.user_id). \
                                                            order_by(UserLoginHistory.id.asc()).all()
                else:
                    user = User.query.filter(User.username == user_name).first()
                    if not user:
                        flash('failure - invalid user entered - please try again!', 'danger')
                        return redirect(url_for('home'))
                    activity_records_cnt = UserLoginHistory.query.filter(UserLoginHistory.user_id == user.id).count()
                    activity_records = UserLoginHistory.query.with_entities(UserLoginHistory.id, User.username,
                                                                             UserLoginHistory.time_login,
                                                                             UserLoginHistory.time_logout). \
                                                            join(User, User.id == UserLoginHistory.user_id). \
                                                            filter(UserLoginHistory.user_id == user.id). \
                                                            order_by(UserLoginHistory.id.asc()).all()
            return render_template('activitylog.html', title='LoginHistory', form=form,
                                   activity_records_cnt=activity_records_cnt, activity_records=activity_records)

        if form.validate_on_submit():
            if form.username.data == '*':
                activity_records_cnt = UserLoginHistory.query.count()
                activity_records = UserLoginHistory.query.with_entities(UserLoginHistory.id, User.username,
                                                                         UserLoginHistory.time_login,
                                                                         UserLoginHistory.time_logout). \
                                                        join(User, User.id == UserLoginHistory.user_id). \
                                                        order_by(UserLoginHistory.id.asc()).all()
            else:
                user = User.query.filter(User.username == form.username.data).first()
                if not user:
                    flash('failure - invalid user entered - please try again!', 'danger')
                    return redirect(url_for('home'))
                activity_records_cnt = UserLoginHistory.query.filter(UserLoginHistory.user_id == user.id).count()
                activity_records = UserLoginHistory.query.with_entities(UserLoginHistory.id, User.username,
                                                                        UserLoginHistory.time_login,
                                                                        UserLoginHistory.time_logout). \
                                                        join(User, User.id == UserLoginHistory.user_id). \
                                                        filter(UserLoginHistory.user_id == user.id). \
                                                        order_by(UserLoginHistory.id.asc()).all()
            return render_template('activitylog.html', title='LoginHistory', form=form,
                                   activity_records_cnt=activity_records_cnt, activity_records=activity_records)
    except:
        return redirect(url_for('home'))
