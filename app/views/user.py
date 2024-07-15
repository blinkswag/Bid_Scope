# app/views/user.py

from flask import render_template, request, redirect, url_for, session, jsonify
from app.services.user_service import UserService
from app.services.ip_service import IPService
from app.utils.validation import validate_password
import bcrypt
from app.utils.helpers import check_user_role
from ..db import Database

db = Database()
def init_user_views(app):

    @app.route('/edit-profile', methods=['GET', 'POST'])
    def edit_profile():
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        current_user_email = session.get('email')
        user = db.users_collection.find_one({"Email": current_user_email})
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            updates = {"Username": username, "Email": email}
            if password:
                valid, message = validate_password(password)
                if not valid:
                    error_messages = [message]
                    return render_template('edit_profile.html', user=user, error_messages=error_messages)
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                updates["Password"] = hashed_password
            result = db.users_collection.update_one({"Email": current_user_email}, {"$set": updates})
            if result.modified_count > 0:
                session['email'] = email
                session['username'] = username
                return redirect('/')
            else:
                error_messages = ["Error updating profile"]
                return render_template('edit_profile.html', user=user, error_messages=error_messages)
        return render_template('edit_profile.html', user=user)
    
    @app.route('/manage-users')
    @check_user_role(['Super Admin', 'Admin'])
    def manage_users():
        current_user_email = session.get('email')
        users = list(UserService.get_all_users())
        filtered_users = [user for user in users if user['Email'] != current_user_email]
        ips = list(IPService.get_all_ips())
        return render_template('manage_users.html', users=filtered_users, role=session.get('role'), ips=ips)

    @app.route('/add-user', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def add_user():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        result = UserService.add_user(username, email, password, role)
        error_messages = []
        if result == "username_exists":
            error_messages.append("Username already exists")
        if result == "email_exists":
            error_messages.append("Email already exists")
        if result == "user_added":
            return redirect('/manage-users')
        else:
            current_user_email = session.get('email')
            users = list(UserService.get_all_users())
            filtered_users = [user for user in users if user['Email'] != current_user_email]
            ips = list(IPService.get_all_ips())
            return render_template('manage_users.html', users=filtered_users, ips=ips, error_messages=error_messages, role=session.get('role'))

    @app.route('/edit-user/<user_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def edit_user(user_id):
        user_to_edit = UserService.get_user_by_id(user_id)
        if not user_to_edit:
            return redirect(url_for('page_not_found'))
        target_user_role = user_to_edit.get('role')
        current_user_role = session.get('role')
        if current_user_role == 'Admin' and target_user_role in ['Super Admin', 'Admin']:
            return redirect(url_for('unauthorized'))
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        password = request.form.get('password', None)
        result = UserService.update_user(user_id, username, email, role, password)
        if result == True or result == False:
            return redirect('/manage-users')
        else:
            error_messages = [result]
            current_user_email = session.get('email')
            users = list(UserService.get_all_users())
            filtered_users = [user for user in users if user['Email'] != current_user_email]
            ips = list(IPService.get_all_ips())
            return render_template('manage_users.html', users=filtered_users, ips=ips, error_messages=error_messages, role=session.get('role'))

    @app.route('/delete-user/<user_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def delete_user(user_id):
        user_to_delete = UserService.get_user_by_id(user_id)
        if not user_to_delete:
            return redirect(url_for('page_not_found'))
        target_user_role = user_to_delete.get('role')
        current_user_role = session.get('role')
        
        if current_user_role == 'Admin' and target_user_role == 'Super Admin':
            return redirect(url_for('unauthorized'))
            
        if UserService.delete_user(user_id):
            return redirect('/manage-users')
        else:
            return "Error deleting user", 400

    @app.route('/add-ip', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def add_ip():
        ip_address = request.form['ip_address']
        tag = request.form['tag']
        result = IPService.add_ip(ip_address, tag)
        if result == "ip_added":
            return redirect('/manage-users')
        else:
            error_messages = ["IP address already exists"]
            current_user_email = session.get('email')
            users = list(UserService.get_all_users())
            filtered_users = [user for user in users if user['Email'] != current_user_email]
            ips = list(IPService.get_all_ips())
            return render_template('manage_users.html', users=filtered_users, ips=ips, error_messages=error_messages, role=session.get('role'))

    @app.route('/delete-ip/<ip_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def delete_ip(ip_id):
        if IPService.delete_ip(ip_id):
            return redirect('/manage-users')
        else:
            return "Error deleting IP address", 400
