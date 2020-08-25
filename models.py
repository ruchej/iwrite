from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


class ServerDB:
    Base = declarative_base()

    class User(Base):
        __tablename__ = "user"
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_conn = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_conn = datetime.datetime.now()

    class ActiveUser(Base):
        __tablename__ = "active_user"
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey("user.id"), unique=True)
        ip = Column(String)
        port = Column(Integer)
        time_conn = Column(DateTime)

        def __init__(self, user, ip, port, time_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.time_conn = time_conn

    class LoginHistory(Base):
        __tablename__ = "login_history"
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey("user.id"), unique=True)
        ip = Column(String)
        port = Column(Integer)
        last_conn = Column(DateTime)

        def __init__(self, user, ip, port, last_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_conn = last_conn

    def __init__(self):
        self.engine = create_engine(
            "sqlite:///iwrite.db3", echo=True, pool_recycle=7200
        )
        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip_addr, port):
        res = self.session.query(self.User).filter_by(login=username)
        if res.count():
            user = res.first()
            user.last_conn = datetime.datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUser(
            user.id, ip_addr, port, datetime.datetime.now()
        )
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, ip_addr, port, datetime.datetime.now())
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.User).filter_by(login=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(self.User.login, self.User.last_conn)
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.User.login,
            self.ActiveUser.ip,
            self.ActiveUser.port,
            self.ActiveUser.time_conn,
        ).join(self.User)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(
            self.User.login,
            self.LoginHistory.last_conn,
            self.LoginHistory.ip,
            self.LoginHistory.port,
        ).join(self.User)
        if username:
            query = query.filter(self.User.login == username)
        return query.all()


if __name__ == "__main__":
    db = ServerDB()
    db.user_login("client_1", "192.168.1.4", 8888)
    db.user_login("client_2", "192.168.1.5", 7777)
    # выводим список кортежей - активных пользователей
    print(db.active_users_list())
    # выполянем 'отключение' пользователя
    db.user_logout("client_1")
    print(db.users_list())
    # выводим список активных пользователей
    print(db.active_users_list())
    # запрашиваем историю входов по пользователю
    # db.login_history('client_1')
    # # выводим список известных пользователей
    # print(db.users_list())
