import cs304dbi as dbi
from datetime import datetime
import db_functions


dbi.cache_cnf()
# set this local variable to 'wmdb' or your personal or team db
db_to_use = 'Socialfy_db' 
dbi.use(db_to_use)
conn = dbi.connect()

post_info = {"senderId": 2, "content": "hi"}
db_functions.create_post(conn, post_info)

# test get_friends_uid
uid = 1
friends = db_functions.get_friends_uid(conn, uid)
print(friends)


# test get_friends_names
friend_ids = [f['uid2'] for f in friends]

friend_names = db_functions.get_friend_names(conn, friend_ids)
print(friend_names)


# test get_friends
print(db_functions.get_friends(conn, uid))



