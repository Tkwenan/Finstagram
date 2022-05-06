import os
import sys
from flask import flash, request, redirect, render_template, Blueprint, current_app, session, url_for
from werkzeug.utils import secure_filename
from db_connection import conn
photo = Blueprint('photo', __name__, static_folder="static",
                  template_folder="templates")

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@photo.route('/', methods=['POST'])
def upload_file():
    user = session['username']
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            cursor = conn.cursor()
            # if request.form['allFollowers'] == True: allFollowers = 1
            if request.form.get('allFollowers'):
                allFollowers = 1
            else:
                allFollowers = 0
            caption = request.form['caption']
            query = 'SELECT COUNT(pID) as totalpID FROM Photo'
            cursor.execute(query)
            count_of_pID = cursor.fetchone()
            filename = str(count_of_pID["totalpID"]) + \
                secure_filename(file.filename)
# system call to save file:
            file.save(os.path.join(
                current_app.config['UPLOAD_FOLDER'], filename))
            full_filename = os.path.join(
                current_app.config['UPLOAD_FOLDER'], filename)
            query = 'INSERT INTO Photo (filePath,allFollowers,caption,poster) VALUES (%s, %s, %s, %s)'
            cursor.execute(query, (full_filename, allFollowers, caption, user))
            conn.commit()
            cursor.close()
            flash('File successfully uploaded')
            return redirect('/home')
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(request.url)


def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= current_app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


@photo.route('/share_photo',  methods=['GET', 'POST'])
def share_photo():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT piD FROM photo WHERE poster = %s AND allFollowers = 0'
    cursor.execute(query, (user))
    photos_to_share = cursor.fetchall()
    query = 'SELECT groupName, groupCreator FROM BelongTo WHERE username = %s'
    cursor.execute(query, (user))
    friendgroups = cursor.fetchall()
    conn.commit()
    cursor.close()
    return render_template('share_photo.html', photos_to_share=photos_to_share, friendgroups=friendgroups)


@photo.route('/manage_tags',  methods=['GET', 'POST'])
def manage_tags():
    return render_template("manage_tags.html")


@photo.route('/tag_users',  methods=['GET', 'POST'])
def tag_users():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT follower FROM Follow WHERE followee =%s AND followStatus = 1'
    cursor.execute(query, (user))
    followers = cursor.fetchall()
    query = 'SELECT pID FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) WHERE follower = %s AND filePath IS NOT NULL UNION SELECT pID FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) WHERE TRUE AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT pID FROM PHOTO JOIN Person ON (Photo.poster = Person.username) WHERE Photo.poster = %s '
    cursor.execute(query, (user, user, user))
    pictures = cursor.fetchall()
    conn.commit()
    cursor.close()
    return render_template('tag_users.html', followers=followers, visiblePictures=pictures)


@photo.route('/tag_requests')
def tag_requests():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT pID FROM Tag WHERE username = %s AND tagStatus = 0'
    cursor.execute(query, username)
    tag_requests = cursor.fetchall()
    cursor.close()
    return render_template('tag_requests.html', tag_requests=tag_requests)


#accept follow requests
@photo.route('/accept_or_decline_request')
def accept_request():
    username = session['username']
    print(request.args['accept'], file=sys.stdout)
    accept_request = request.args['accept'] if request.args['accept'] else request.args['reject']
    cursor = conn.cursor()
    if accept_request:
        query = 'UPDATE Tag SET tagStatus = 1 WHERE username = %s AND pID = %s'
        cursor.execute(query, (username, request.args['user']))
        conn.commit()
        cursor.close()
    else:
        query = 'DELETE FROM Tag WHERE username= %s AND pID = %s'
        cursor.execute(query, (username, request.args['user']))
        conn.commit()
        cursor.close()
    return redirect('manage_tags')
