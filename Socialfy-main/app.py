from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import random
import db_functions
import api_functions
import re

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

feed_n = 20 # limit feed display to the most recent n posts

@app.route('/')
def index():
    return redirect(url_for('display_feed'))


"""
Provides a user with their feed - ie what has been shared with them. 
This includes posts and comments on those posts (with the option to add and delete comments)
"""
@app.route('/feed/', methods=["GET", "POST"])
def display_feed():
    conn = dbi.connect()
    username = session.get('username')
    uid = session.get('uid')
    
    if uid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    if request.method == "GET":
        ## get the posts, number is based on global var feed_n
        posts = db_functions.get_feed(conn, uid, feed_n)

        for p in posts:
            # determine type if not in table yet
            if p.get('type'):
                content_type = p.get('type')
            else:
                match_attempt = re.search('open.spotify.com/(.*)/', p.get('url'))
                if match_attempt:
                    content_type = match_attempt.group(1)
                    p['type'] = content_type
                else:
                    content_type = None
            
            # generate embed link
            search_string = "open.spotify.com/(.*)\?".format(content_type)
            match_attempt = re.search(search_string, p.get('url'))
            if match_attempt:
            # get track ID from the url
                id_with_type = match_attempt.group(1)
                # also generate embed link
                p['embed_link'] = "https://open.spotify.com/embed/{}?utm_source=generator".format(id_with_type)
            
            p['commentList'] = db_functions.get_comments(conn, p.get('postId'))

        ## then render the page
        return render_template('feed.html',
                                name=username, 
                                posts = posts,
                                uid = uid)
            
    else: 
        # post - could be addition or deletion of comment
        data = request.form
        uid = session.get('uid')

        for k in data.keys():
            if "delete" in k:
                # cid is part of in value of submit button "delete_cid"
                cid = k[7:]
                db_functions.delete_comment(conn, cid)
                return redirect(url_for('display_feed'))

            elif "submit" in k:
                postid = k[7:]
                ## check that it contains text, if not then flash message
                if data[k] == "":
                    flash("that looks like an empty comment. can you try again?")
                else:
                    db_functions.add_comment(conn, uid, postid, data[k])
                return redirect(url_for('display_feed'))

"""
Allows user to share content (url and some text) with people following them (one person or all)
"""
@app.route('/share/', methods=["GET", "POST"])
def music_share_form():
    
    username = session.get('username')
    uid = session.get('uid')
    # check if logged in
    if uid is None:
        return redirect(url_for('login'))

    conn = dbi.connect()

    if request.method == "GET":
        followers = db_functions.get_followers(conn,uid)
        return render_template('musicShareForm.html', friendList = followers)
    else:
        try:            
            # make dictionary with post info 
            # we decided to make a new dictionary because request.form is immutable
            # we think this way also makes our code more readable
            post_info = {}
            post_info['senderId'] = session.get('uid')
            post_info['receiverId'] = request.form.get('friendList')
            post_info['url'] = request.form.get('URL')
            post_info['content'] = request.form.get('message')

            # if to all friends
            if post_info['receiverId'] == "ALL":
                post_info['toAllFriends'] = True
                post_info['receiverId'] = None
            
            # determine type of content from the URL
            match_attempt = re.search('open.spotify.com/(.*)/', post_info['url'])
            if match_attempt:
                post_info['type'] = match_attempt.group(1)

            # actually create the post
            post_id = db_functions.create_post(conn, post_info)

            flash('form submission successful')

            ## then take user to their feed
            return redirect(url_for('display_feed'))

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect( url_for('display_feed') )


"""
User can view their own profile, which shows the number of followers 
they have and how many people they're following, with links to lists of each.
It also shows posts (with comments too) of what the user has shared with others.
Users can delete their own posts, as well as add and delete their comments.
"""
@app.route('/profile/', methods=["GET","POST"])
def view_profile():
    conn = dbi.connect()

    username = session.get('username')
    uid = session.get('uid')
    
    if uid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    if request.method == 'GET':
        #gets all of the songs that have been shared by this user
        userSongList = db_functions.get_user_songs(conn, uid)
        for song in userSongList:
            if song['toAllFriends'] == 0:
                name = db_functions.get_username(conn,song['receiverId'])['username']
                song['username'] = name
            else:
                song['username'] = "all your friends"

            # generate embed link
            search_string = "open.spotify.com/(.*)\?".format(song.get('type'))
            match_attempt = re.search(search_string, song.get('url'))
            if match_attempt:
            # get track ID from the url
                id_with_type = match_attempt.group(1)
                # generate embed link
                song['embed_link'] = "https://open.spotify.com/embed/{}?utm_source=generator".format(id_with_type)
            
            song['commentList'] = db_functions.get_comments(conn, song.get('postId'))

        following = db_functions.get_follows(conn,uid)
        followers = db_functions.get_followers(conn,uid)

        return render_template('profile.html',
                                username=username,
                                following_count = len(following),
                                followers_count = len(followers),
                                userSongList = userSongList,
                                uid = uid)
    elif request.method == "POST":
        # post method - could be addition or deletion of comment or deletion of a post
        data = request.form
        uid = session.get('uid')
        
        for k in data.keys():
            if "comment_delete" in k:
                # cid is part in value of submit button "comment_delete_cid"
                cid = k[15:]
                db_functions.delete_comment(conn, cid)
                return redirect(url_for('view_profile'))

            elif "submit" in k:
                # postid is part in value of submit button "submit_postid"
                postid = k[7:]
                ## check that it contains text, if not then flash message
                if data[k] == "":
                    flash("that looks like an empty comment. can you try again?")
                else:
                    db_functions.add_comment(conn, uid, postid, data[k])
                return redirect(url_for('view_profile'))
            
            elif "post_delete" in k:
                # postid is part in value of submit button "post_delete_postid"
                postid = k[12:]
                db_functions.delete_post(conn, postid)
                return redirect(url_for('view_profile'))

        return redirect(url_for('view_profile'))


"""
View another user's profile. Shows how many followers and how many users they're following.
Has that user's posts to everyone and you can add and delete your own comments.
"""
@app.route('/profile/<string:username>', methods=["GET", "POST"])
def view_friendProfile(username):
    myUsername = session.get('username')
    myUid = session.get('uid')
    
    if myUid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    if request.method == "GET":
        conn = dbi.connect()
        
        # get that user's username from the uid
        uid = db_functions.get_uid(conn, username)['uid']

        userSongList = db_functions.get_user_songs(conn, uid)

        for song in userSongList:
            if song['toAllFriends'] == 0:
                name = db_functions.get_username(conn,song['receiverId'])['username']
                song['username'] = name
            else:
                song['username'] = "all their friends"

            # get embed link
            search_string = "open.spotify.com/(.*)\?".format(song.get('type'))
            match_attempt = re.search(search_string, song.get('url'))
            if match_attempt:
            # get track ID from the url
                id_with_type = match_attempt.group(1)
                song['embed_link'] = "https://open.spotify.com/embed/{}?utm_source=generator".format(id_with_type)
            
            song['commentList'] = db_functions.get_comments(conn, song.get('postId'))
    
        #friend's followers and following List
        following = db_functions.get_follows(conn,uid)
        followers = db_functions.get_followers(conn,uid)

        #my followers and following lists, use to check if this is someone I follow
        myFollowing = db_functions.get_follows(conn,myUid)

        followingUsernames = []
        for dict in myFollowing:
            followingUsernames.append(dict['username'])
            
        return render_template('friendProfile.html',
                                followingUsernames = followingUsernames,
                                username=username,
                                myUsername = myUsername,
                                following_count = len(following),
                                followers_count = len(followers),
                                userSongList = userSongList,
                                friend_uid = uid,
                                friend_username = username,
                                uid = myUid)
    
    if request.method == "POST":
        conn = dbi.connect()
        uid = db_functions.get_uid(conn, username)['uid']
        data = request.form

        if data.get('submit') == "unfollow":
            success = db_functions.unfollow(conn, myUid, uid)
            if not success:
                flash("Sorry, something went wrong. Please try again")
        elif data.get('submit') == "follow":
            success = db_functions.add_follow(conn, myUid, uid)
            if not success:
                flash("Sorry, something went wrong. Please try again")


        # for adding and deleting comments
        for k in request.form.keys():
            if "delete" in k:
                # comments = db_functions.get_cid(conn, uid) ## not sure why needed??
                # cid is part of value of submit button "delete_cid"
                cid = k[7:]
                db_functions.delete_comment(conn, cid)
                return redirect(url_for('view_friendProfile', username=username))

            elif "add_comment" in k:
                postid = k[12:]
                ## check that it contains text, if not then flash message
                if data[k] == "":
                    flash("that looks like an empty comment. can you try again?")
                else:
                    db_functions.add_comment(conn, myUid, postid, data[k])
                return redirect(url_for('view_friendProfile', username=username))
    
        return redirect(url_for('view_friendProfile', username=username))


"""
Allows you to search for users to follow.
"""
@app.route('/findFriends/', methods = ['GET', 'POST'])
def findFriends():
    conn = dbi.connect()
    
    username = session.get('username')
    uid = session.get('uid')
    
    if uid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('findFriends.html')
    else:
         #Update template after adding friend
        if request.form['submit'] == "Search":
            data = request.form
            user = "Users"
            alikeUsers = db_functions.lookup(conn,data['name'])
            if len(alikeUsers) == 0:
                flash("No users found")
            else: 
                flash("Search Completed")
            return render_template('findFriends.html', 
                                    userList = alikeUsers,
                                    username = username,
                                    user = user)
        return redirect(url_for('view_profile'))


"""
Shows a list of who you're following.
"""
@app.route('/following/', methods=['GET'])
def followingList():
    conn = dbi.connect()

    username = session.get('username')
    uid = session.get('uid')
    
    if uid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    following = db_functions.get_follows(conn,uid)
    return render_template('followingList.html',
                            uid = uid,
                            following = following)

"""
Shows a list of your followers.
"""
@app.route('/followers/', methods=['GET'])
def followerList():
    conn = dbi.connect()
    username = session.get('username')
    uid = session.get('uid')
    
    if uid is None:
        flash("You are not logged in yet - taking you to the login page")
        return redirect(url_for('login'))

    following = db_functions.get_follows(conn,uid )
    followers = db_functions.get_followers(conn,uid )
    return render_template('followersList.html',
                            uid = uid,
                            following = following,
                            followers = followers)

"""
Route for logging in. Includes a password check and setting session variables if correct.
"""
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    elif request.method=='POST':
        try:
            username = request.form['username']
            passwd = request.form['password']
            conn = dbi.connect()
            # check if password is correct
            correctPassword = db_functions.check_password(conn,username,passwd)
            if correctPassword:
                flash('Successfully logged in as: '+username)
                session['username'] = username
                session['uid'] = db_functions.get_uid(conn, username).get('uid')
                return redirect(url_for('display_feed'))
            else:
                flash('login incorrect. Try again or sign up')
                return redirect(url_for('login'))

        except Exception as err:
            print('Form submission error '+ str(err))
            return redirect( url_for('login') )


"""
Route for signing up as a new user.
"""
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method=='GET':
        return render_template('signup.html')
    if request.method=='POST':
        try:
            username = request.form['username']
            passwd1 = request.form['password1']
            passwd2 = request.form['password2']
            if passwd1 != passwd2:
                flash('The passwords you have entered do not match')
                return redirect( url_for('signup'))
            
            conn = dbi.connect()
    
            # let's let insert_user function check if username already exists
            inserted = db_functions.insert_user(conn,username,passwd1)
            if inserted == "duplicate username":
                flash("That username is already taken")
                return redirect( url_for('signup'))
            else:
                session['username'] = username
                session['uid'] = db_functions.get_uid(conn, username).get('uid')
                flash('You have signed up and logged in as: '+username)
                return redirect(url_for('display_feed'))
        except Exception as err:
            print('Form submission error '+str(err))
            return redirect( url_for('signup') )

"""
Clears session variables and redirects you to the login page.
"""
@app.route('/logout/', methods=['POST','GET'])
def logout():
    try:
        if 'username' in session:
            username = session['username']
            session.pop('username')
            session.pop('uid')
            flash('You are logged out')
            return redirect(url_for('login'))
        else:
            flash('You are not logged in. Please login or sign up')
            return redirect( url_for('login') )
    except Exception as err:
        flash('sorry, an error occurred '+str(err))
        return redirect( url_for('login') )


@app.before_first_request
def init_db():
    dbi.cache_cnf()
    db_to_use = 'socialfy_db' 
    dbi.use(db_to_use)

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)