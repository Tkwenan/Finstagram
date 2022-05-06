#Import Flask Library
from flask import render_template, request, redirect, url_for,session,flash
from db_connection import conn
from app import app
import sys


###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"


#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    queryPhotos = 'SELECT firstName, lastName, filePath, Person.username, postingDate, pID, caption FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) WHERE follower = %s AND filePath IS NOT NULL UNION SELECT firstName, lastName, filePath, Person.username, postingDate, pID, caption FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) WHERE TRUE AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT firstName, lastName, filePath, Person.username, postingDate, pID, caption FROM PHOTO JOIN Person ON (Photo.poster = Person.username) WHERE Photo.poster = %s ORDER BY postingDate DESC '
    cursor.execute(queryPhotos, (user, user, user))
    dataPhotos = cursor.fetchall()
    taggedPeople = 'SELECT Tag.username, Photo.pID FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE follower = %s AND filePath IS NOT NULL UNION SELECT Tag.username, Photo.pID  FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE TRUE AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT Tag.username, Photo.pID FROM PHOTO JOIN Person ON (Photo.poster = Person.username) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE Photo.poster = %s '
    cursor.execute(taggedPeople, (user, user, user))
    dataTags = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, photos = dataPhotos, Tags = dataTags)

        
# @app.route('/post', methods=['GET', 'POST'])
# def post():
#     username = session['username']
#     cursor = conn.cursor();
#     blog = request.form['blog']
#     query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
#     cursor.execute(query, (blog, username))
#     conn.commit()
#     cursor.close()
#     return redirect(url_for('home'))



@app.route('/followersToTag', methods=['GET', 'POST'])
def send_tag_request():
    user = session['username']
    if request.method == 'POST':
        cursor = conn.cursor();
        users_to_tag = request.form.getlist("tag_for _follower")
        pic_for_tag = request.form["picture_for_tag"]
        query = 'INSERT INTO Tag VALUES(%s, %s, %s)' 

        for follower in users_to_tag:
            query_for_visible_photo = 'SELECT pID FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) WHERE follower = %s AND filePath IS NOT NULL UNION SELECT pID FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) WHERE TRUE AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT pID FROM PHOTO JOIN Person ON (Photo.poster = Person.username) WHERE Photo.poster = %s '
            cursor.execute(query_for_visible_photo, (follower, follower, follower)) 
            pictures = cursor.fetchall()
            query_for_unique_tags = 'SELECT pID FROM Tag where pID = %s AND username = %s'
            cursor.execute(query_for_unique_tags, (pic_for_tag,follower))
            valid_row = cursor.fetchall()
            pictures = [d['pID']for d in pictures]
            #pic_tag= (int)(pic_for_tag)
            if  valid_row:
                message = follower +" is already tagged "
                flash(message)
                return redirect('tag_users') 
            if user == follower:
              cursor.execute(query, (pic_for_tag, user, 1))
              conn.commit()
            elif int(pic_for_tag) in pictures:
                cursor.execute(query, (pic_for_tag, follower, 0))
                conn.commit()
            else:
                message = "The photo isn't visible to "+ follower
                flash(message)
                return redirect('tag_users')               
        cursor.close()
    return redirect(url_for('photo.manage_tags'))



@app.route('/share', methods=['GET','POST'])
def share_photo_to_group():
    user = session['username']
    
    if request.method == 'POST':
        cursor = conn.cursor();
        pID = request.form["photos_to_share"]
        print(request.form["friendgroup"], file=sys.stdout)
        groupName, creator = request.form["friendgroup"].split('|')
        query = 'INSERT INTO SharedWith VALUES(%s, %s, %s)'
        try:
            cursor.execute(query, (pID, groupName, creator))
            conn.commit()
            cursor.close()
            message = pID + " has been shared with " + groupName + " created by " + creator
            flash(message)
        except (conn.Error, conn.Warning) as e:
            print(e, file=sys.stderr) 
            message = pID + " has already been shared with " + groupName + " created by " + creator
            flash(message)   
            return redirect(url_for('share_photos'))  
    return home()


@app.route('/share_photo')
def share_photos():
    return render_template('share_photo.html')


@app.route('/upload_form')
def upload_form():
	return render_template('upload.html')

#---------------------------Search by Poster--------------------------------------
@app.route('/select_blogger')
def select_blogger():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT Follow.followee FROM Follow WHERE Follow.follower = %s AND followStatus = 1 UNION SELECT DISTINCT username FROM BelongTo WHERE (groupName,groupCreator) IN (SELECT groupName, groupCreator  FROM BelongTo WHERE username = %s)'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM ((SELECT firstName, lastName, filePath, username, postingDate, pID, caption FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1 AND followStatus = 1) JOIN Person on (Person.username = photo.poster) WHERE follower = %s AND followee = %s AND filePath IS NOT NULL) UNION (SELECT firstName, lastName, filePath, username, postingDate, pID, caption FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = Photo.poster) WHERE Photo.poster = %s AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) ) UNION (SELECT firstName, lastName, filePath, Person.username, postingDate, pID, caption FROM PHOTO JOIN Person ON (Photo.poster = Person.username) WHERE Photo.poster = %s ORDER BY postingDate DESC ) ) AS sub WHERE username = %s '
    cursor.execute(query, (user, poster, poster, user, user, poster))
    photos = cursor.fetchall()
    #queryTags = 'SELECT Tag.username, Photo.pID FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1 AND followStatus = 1) JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE follower = %s AND followee = %s AND filePath IS NOT NULL UNION SELECT Tag.username, Photo.pID FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = Photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE Photo.poster = %s AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s)'
    #cursor.execute(queryTags, (user, poster, poster, user))
    queryTags = 'SELECT username, pID FROM Tag WHERE tagStatus = 1'
    cursor.execute(queryTags)
    Tags = cursor.fetchall()
    cursor.close()
    error  = None

    if (photos):
        return render_template('show_posts.html', photosByUser = photos, poster = poster, Tags = Tags)
    else:
        error = "No posts by the User"
        return render_template('show_posts.html', error = error, photosByUser = photos, poster = poster, Tags = Tags)
#--------------------------------------------------------------------------------------------------

#---------------------------Search by tagged--------------------------------------
@app.route('/select_tagged')
def select_tagged():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT Follow.followee FROM Follow WHERE Follow.follower = %s AND followStatus = 1 UNION SELECT DISTINCT username FROM BelongTo WHERE (groupName,groupCreator) IN (SELECT groupName, groupCreator  FROM BelongTo WHERE username = %s)'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_tagged.html', tagged_list = data)

@app.route('/show_tagged', methods=["GET", "POST"])
def show_tagged():
    tagged = request.args['tagged']
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT firstName, lastName, filePath, Person.username, postingDate, Photo.pID, caption FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE follower = %s AND Tag.username = %s AND filePath IS NOT NULL UNION SELECT firstName, lastName, filePath,Person.username, postingDate, Photo.pID, caption FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE TRUE AND Tag.username = %s AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT firstName, lastName, filePath, Person.username, postingDate, Photo.pID, caption FROM PHOTO JOIN Person ON (Photo.poster = Person.username) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE Photo.poster = %s AND Tag.username = %s ORDER BY postingDate DESC '
    cursor.execute(query, (user, tagged, tagged, user, user, tagged)) 
    photos = cursor.fetchall()
    queryTags = 'SELECT username, pID FROM Tag WHERE tagStatus = 1'
    #queryTags = 'SELECT Tag.username, Photo.pID FROM Photo JOIN Follow ON (photo.poster = Follow.followee AND allFollowers = 1  AND followStatus = 1) JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE follower = %s AND filePath IS NOT NULL UNION SELECT Tag.username, Photo.pID FROM Photo NATURAL JOIN SharedWith JOIN Person on (Person.username = photo.poster) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE TRUE AND Tag.username = %s AND (groupName, groupCreator) IN (SELECT DISTINCT groupName, groupCreator FROM BelongTo Where username = %s) UNION SELECT Tag.username, Photo.pID FROM PHOTO JOIN Person ON (Photo.poster = Person.username) JOIN Tag ON (Tag.pID = Photo.pID AND tagStatus = 1) WHERE Photo.poster = %s AND Tag.username = %s'
    #cursor.execute(queryTags, (user, tagged, user, user, tagged))
    cursor.execute(queryTags)
    Tags = cursor.fetchall()
    cursor.close()
    error  = None

    if (photos):
        return render_template('show_tagged.html', photosByTags= photos , taggedPerson = tagged, Tags = Tags)
    else:
        error = "No photos where the user is tagged"
        return render_template('show_tagged.html', error = error, photosByTags = photos, taggedPerson = tagged, Tags = Tags)

#--------------------------------------------------------------------------------------------------
#--------------------------------------Manage Follows--------------------------------------------------------
#Define route for manage follows
@app.route('/manage_follows')
def manage_follows():
    return render_template('manage_follows.html')

@app.route('/find_followee')
def find_followee():
    return render_template('find_followee.html')


 #search for a user you'd like to follow 
 # query1: check if there's such a user registered
 # query2: check that you don't already follow that user
@app.route('/find_user', methods=['GET', 'POST'])
def find_user():
    follower = session['username']
    if request.method == 'GET':
     followee = request.args.get('user')
    cursor = conn.cursor();

    # query1: check if there's such a user registered
    query1 = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query1, (followee))
    data1 = cursor.fetchone()

    # query2: check that you don't already follow that user
    query2 = 'SELECT * FROM Follow WHERE follower = %s AND followee = %s AND followStatus = 1'
    cursor.execute(query2, (follower, followee))
    data2 = cursor.fetchone()

    # check if you sent a follow request and it's still pending
    query3 = 'SELECT * FROM Follow WHERE follower = %s AND followee = %s AND followStatus = 0'
    cursor.execute(query3, (follower, followee))
    data3 = cursor.fetchone()

    
    error = None
    if (data1):
       #user exists, check if we already follow them
        if (data2):
             error = "You already follow this user"
             return render_template('find_followee.html', error = error)
       
        elif(data3): # you already sent this user a follow request and it's pending
             error = "Follow request pending..."
             return render_template('find_followee.html', error = error)  

        else: #user exists but you don't follow them
             query2 = 'INSERT INTO Follow (follower, followee, followStatus) VALUES(%s, %s, 0)'
             cursor.execute(query2, (follower, followee))
             return render_template('find_followee.html')

    else: #user doesn't exist
        error = "User not found"
        return render_template('find_followee.html', error = error)


#when you click on the 'unfollow' link, display this page
@app.route('/unfollow')
def unfollow():
    return render_template('unfollow.html')


#unfollow a user that you no longer wish to follow
#first check that the current user follows the user they'd like to unfollow
@app.route('/unfollow_user', methods=['GET', 'POST'])
def unfollow_user():
    follower = session['username']
    if request.method == 'GET':
     followee = request.args.get('user')
    cursor = conn.cursor();
    query1 = 'SELECT * FROM Follow WHERE follower = %s AND followee = %s AND followStatus = 1'
    cursor.execute(query1, (follower,followee))
    data = cursor.fetchone()
    error = None
    if (data):
        # if the query returns, the current user follows the followee
        # automatically unfollow
        query2 = 'DELETE FROM Follow WHERE follower = %s AND followee = %s AND followStatus = 1'

        #delete from the Tag table where current user had tagged followee
        query3 = 'DELETE FROM Tag WHERE username = %s AND tagStatus = 1 AND pID IN (SELECT pID from Photo WHERE poster = %s)'


        cursor.execute(query2, (follower, followee))
        cursor.execute(query3, (followee, follower))
        conn.commit()
        cursor.close()
        return render_template('unfollow.html')
    else:
        error = "Attempted to unfollow a user that you do not currently follow"
        return render_template('unfollow.html', error = error)
   

#Handling follow requests
# view a list of your follow requests
@app.route('/show_requests')
def show_requests():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM Follow WHERE followee = %s AND followStatus = 0'
    cursor.execute(query, username)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_requests.html', requests_list = data)
    
    
#accept follow requests 
@app.route('/accept_request')   
def accept_request():
    username = session['username']
    follower = request.args['user']
    cursor = conn.cursor();
    query = 'UPDATE Follow SET followStatus = 1 WHERE follower = %s AND followee = %s' 
    cursor.execute(query,(follower,username))
    conn.commit()
    cursor.close()
    return render_template('show_requests.html')

#reject follow requests 
@app.route('/reject_request')
def reject_request():
    username = session['username']
    follower = request.args['user']
    cursor = conn.cursor()
    query = 'DELETE FROM Follow WHERE follower = %s AND followee = %s' 
    cursor.execute(query,(follower,username))
    conn.commit()
    cursor.close()
    return render_template('show_requests.html')


#-----------------------------------------------------FRIEND GROUPS---------------------------------------------------------------------------------
#display webpage that allows us to deal with friendgroups
@app.route('/friendgroups')
def friendgroups():
    return render_template('friendgroups.html')


#display webpage to create new friendgroup
@app.route('/newfriendgroup')
def newfriendgroup():
    return render_template('newfriendgroup.html')


#create a new friendgroup
@app.route('/new_friendgroup', methods=['GET', 'POST'])
def new_friendgroup():
    username = session['username']
    groupname = request.form['groupname']
    description = request.form['description']
    cursor = conn.cursor()

    #check that user doesn't already have a friendgroup with that name
    query = 'SELECT groupName, groupCreator FROM FriendGroup WHERE groupName = %s AND groupCreator = %s'
    cursor.execute(query, (groupname, username))
    data = cursor.fetchone()
    error = None
    if(data):
        #If the previous query returns data, then friend group with that name exists
        error = "Friend group with this name already exists"
        return render_template('newfriendgroup.html', error = error)
    
    else:
        #else create new friendgroup
        ins1 = 'INSERT INTO FriendGroup VALUES(%s, %s, %s)'

        #make current user a member of the group that they just created
        ins2 = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'

        cursor.execute(ins1, (groupname, username, description))

       
        cursor.execute(ins2, (username, groupname, username))

        conn.commit()
        cursor.close()
        return render_template('friendgroups.html')

#display web page to add someone to a friend group
@app.route('/addtogroup', methods=['GET', 'POST'])
def addtogroup():
#query to get the user's friend groups; display friend groups in drop down list
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT groupName FROM FriendGroup WHERE groupCreator = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()    
    return render_template('addtogroup.html', friendgroups = data)


#add someone to an existing friendgroup
@app.route('/addtofriendgroup',  methods=['GET', 'POST'])
def addtofriendgroup(): 
    groupCreator = session['username']
    if request.method == 'GET':
        friendname = request.args.get('friendname')  
        groupName = request.args.get('groupname')  
     #friendname = request.form['friendname']
     #groupName = request.form['groupname']
    cursor = conn.cursor()

    #check that the user we want to add to friendgroup exists i.e. check whether there is exactly one person with that name 
    query1 = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query1, (friendname))
    data1 = cursor.fetchone()

    #check that the user doesn't already belong to the friendgroup
    query2 = 'SELECT username, groupName, groupCreator FROM BelongTo WHERE username = %s AND groupName = %s AND groupCreator = %s'
    cursor.execute(query2, (friendname, groupName, groupCreator))
    data2 = cursor.fetchone()

    #always display the current user's friend groups
    query3 = 'SELECT groupName FROM FriendGroup WHERE groupCreator = %s'
    cursor.execute(query3, (groupCreator))
    data3 = cursor.fetchall()

    error = None
    if(data1):
        #If query1 returns data, then there's such a user registered in the system
        #so, check that user doesn't already belong to the friend group
        if(data2):
         #If query2 returns data, then the user is alredy in the friendgroup
            error = "This user already belongs to the friendgroup"
            return render_template('addtogroup.html', friendgroups = data3, error = error)

        #else add the user to the friendgroup by updating the BelongTo table
        else:
            ins = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
            cursor.execute(ins, (friendname, groupName, groupCreator))
            conn.commit()
            cursor.close()
            return render_template('friendgroups.html')
    else:
        error = "User not found"
        return render_template('addtogroup.html', friendgroups = data3, error = error)

        

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
