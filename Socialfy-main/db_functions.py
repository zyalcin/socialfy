## This contains our helper functions for connecting to the DB

import cs304dbi as dbi
import pymysql
from datetime import datetime
import bcrypt

# ==========================================================
# The functions that do most of the work.

def get_uid(conn, username):
    '''Returns a user's uid based on their username
    :param conn: connection to db
    :param username: a user's username
    :return: int uid 
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select uid from user where username like %s''', [username])
    uid= curs.fetchone()
    return uid

def get_username(conn, uid):
    '''Returns a user's uid based on their username
    :param conn: connection to db
    :param username: a user's username
    :return: int uid 
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select username from user where uid = %s''', [uid])
    user_list = curs.fetchone()
    return user_list


def get_feed(conn, uid, n):
    '''gets a list of the most recent n posts for a user based on uid

    :param conn: connection to database
    :param uid: user's uid
    :param n: the number of posts to return
    :return: list of dictionaries of the n most recent posts shared with user
    '''
    curs = dbi.dict_cursor(conn)
    ## we need posts 
    # get DM's and posts to all friends
    curs.execute('''select senderId, receiverId, user.username, toAllFriends, url, date, content, postId, type from post
        inner join user on (user.uid = post.senderId)
        where receiverId=%s or
        (toAllFriends=True and
        (senderId in (select followed from friends where follower=%s)))
        order by date DESC
        limit %s''', [uid, uid, n])
        # or senderId in (select uid2 from friends where uid1=%s
    posts = curs.fetchall()
    return posts


def get_comments(conn, pid):
    '''get comments related to a post'''
    curs = dbi.dict_cursor(conn)
    curs.execute(''' select cid, comment, date, uid, username
                    from comment inner join user using (uid) 
                    where pid = %s
                    order by date desc''' , [pid])
    data = curs.fetchall()
    return data

def add_comment(conn, uid, pid, comment):
    '''adds a comment to the comment table'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''INSERT INTO comment(uid, pid, comment, date)
            VALUES (%s, %s, %s, %s); ''', [uid, pid, comment, datetime.now()])
    conn.commit()
    return True

def delete_comment(conn, cid):
    '''deletes comment from comment table based on cid'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''delete from comment
                    where cid = %s''', [cid])
    conn.commit()
    return True


def get_user_songs(conn, uid):
    '''given a user id, find all of the songs they've sent to friends and who they sent them to'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select url,toAllFriends, receiverId, type, date, postId, content from post
        where senderId=%s
        order by date DESC''', [uid])
    songList = curs.fetchall()
    return songList

def create_post(conn, post_info):
    '''
    Inserts a post into the post table

    :param conn: connection to database
    :param post_info: dictionary of post information, doesn't have to be complete
    :return: postId if successful, error message otherwise
    '''
    curs = dbi.dict_cursor(conn)
    try:
        values_to_add = [post_info.get('senderId', None),
                post_info.get('receiverId', None),
                post_info.get('type', None),
                post_info.get('url', None),
                post_info.get('content', None),
                datetime.now(),
                post_info.get('toAllFriends', False)]
        curs.execute('''INSERT INTO post(senderId, receiverId, type, url, content, date, toAllFriends)
            VALUES (%s, %s, %s, %s, %s, %s, %s); ''', values_to_add)
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return str(e)

def delete_post(conn, pid):
    '''deletes a user's post given the postid'''
    curs = dbi.dict_cursor(conn)
    try:
        curs.execute('''DELETE from post where postId = %s''', [pid])
        conn.commit()
    except Exception as e:
        print(e)
        return str(e)


def lookup(conn, name):
    '''searches for a user based on search_name
    returns a list of possible UID's'''
    curs = dbi.dict_cursor(conn)
    name = '%' + name + '%' #format wildcards
    curs.execute('''select uid,username from user where username LIKE %s''', 
                  [name])
    users = curs.fetchall()
    return users

def add_follow(conn,my_uid,followed_uid):
    '''follows a user (if friendship doesn't already exist)'''
    curs = dbi.dict_cursor(conn)
    # check if already friends
    try:
        curs.execute('insert into friends(followed,follower) values (%s,%s)',[followed_uid,my_uid]) 
        conn.commit()
        return True
    except pymysql.err.IntegrityError as err:
        details = err.args
        print('error',details)
        if details[0] == pymysql.constants.ER.DUP_ENTRY: #friendship already exists
            return False

def get_followers(conn, my_uid):
    ''' searches for who is following you'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select uid, username 
                    from friends inner join user on user.uid=friends.follower 
                    where followed = %s''', [my_uid])
    return curs.fetchall()

def get_follows(conn, my_uid):
    ''' searches for who you are following'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select uid, username 
                    from friends inner join user on user.uid=friends.followed 
                    where follower = %s''', [my_uid])
    return curs.fetchall()


def unfollow(conn, my_uid, followed_uid):
    '''unfollows someone'''
    curs = dbi.dict_cursor(conn)
    try:
        curs.execute('''delete from friends
                        where follower = %s and followed = %s''', [my_uid, followed_uid])
        conn.commit()
        return True
    except Exception as e:
        print("An error occured in unfollowing: {}").format(e)
        return False


def check_password(conn,username, passwd):
    '''check if passwd matches hashed password in the database for a user'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select hashed from user where username=%s',[username])
    hashed = curs.fetchone().get('hashed')

    if bcrypt.checkpw(passwd.encode('utf-8'), hashed.encode('utf-8')):
        return True
    else:
        return False

def insert_user(conn,username,passwd):
    '''inserts username and password into user table'''
    curs = dbi.dict_cursor(conn)
    try:
        hashed = bcrypt.hashpw(passwd.encode('utf-8'), bcrypt.gensalt())
        curs.execute('insert into user(username,hashed) values (%s,%s)',[username,hashed])
        conn.commit()
        return True
    except pymysql.err.IntegrityError as err:
        details = err.args
        print('error',details)
        if details[0] == pymysql.constants.ER.DUP_ENTRY:
            return "duplicate username"
        else:
            return details

# ==========================================================
# This starts the ball rolling, *if* the file is run as a
# script, rather than just being imported.    

if __name__ == '__main__':
    dbi.cache_cnf()   # defaults to ~/.my.cnf
    dbi.use('socialfy_db')
    conn = dbi.connect()
    
