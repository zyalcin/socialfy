use zy1_db;  -- if you're running this with your personal account, change this db

drop table if exists comment;
drop table if exists post;
drop table if exists friends;
drop table if exists user;
 
create table user (
  uid int auto_increment,
  username varchar(30),
  hashed char(60) not null,
  primary key (uid),
  unique (username)
)
ENGINE = InnoDB;
create table friends (
  followed int not null,
  follower int not null, 
  primary key(followed, follower),
  foreign key (followed) references user(uid)
      on update restrict
      on delete restrict,    
   foreign key (follower) references user(uid)
      on update restrict
      on delete restrict   
)
ENGINE = InnoDB;

create table post (
  postId int not null auto_increment,
  senderId int not null,
  receiverId int,
  type enum ('track','album','playlist','artist', 'show','episode'),
  url varchar(100),
  content varchar(250),
  date datetime,
  toAllFriends boolean,
  primary key (postId),
  INDEX (senderID),
  foreign key (senderID) references user(uid)
      on update restrict
      on delete restrict
)
ENGINE = InnoDB;

create table comment(
  uid int not null,
  pid int not null,
  cid int auto_increment, 
  comment varChar(250),
  date datetime,
  primary key(cid),
  foreign key (uid) references user(uid)
    on update restrict
    on delete restrict,
  foreign key (pid) references post(postId)
    on update cascade
    on delete cascade
)
ENGINE = InnoDB;
