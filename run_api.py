import typing

import yaml

import tornado.web
import tornado.ioloop

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.future import Engine

#internal libs
from db_init import User, Data_Collection


def main() -> None:
    # read the configs
    with open("config.yaml", "r") as f:
        conf: typing.Dict[str, typing.Any] = yaml.safe_load(f)

    # connect to DB
    db_url: str = f"postgresql://{conf['db']['user']}:{conf['db']['password']}@{conf['db']['host']}:{conf['db']['port']}/{conf['db']['name']}"
    print(f"Connection to {db_url}")
    db_engine: Engine  = create_engine(db_url)
    db_session = Session(db_engine)

    #web app handlers
    class LoginHandler(tornado.web.RequestHandler):
        def get(self) -> None:
            user: bytes = self.get_secure_cookie("user")
            if not user:
                # simple authenthification page
                self.write("""<html><body>
                    <form action="/api/login" method="post">
                           login: <input type="text" name="login"><br>
                           password: <input type="password" name="password"><br>
                           <input type="submit" value="Sign in">
                    </form>
                </body></html>""")
            else:
                # cute json 200 answer
                self.write({"Hello": user.decode('utf-8')})

        def post(self) -> None:
            login: str = self.get_argument("login")
            password: str = self.get_argument("password")

            if not (login and password):
                self.send_error(401)
                return

            # check password
            user: typing.Union[None, typing.Typle[User,]] = db_session.execute(
                select(User)
                .where(User.login == login)
                .where(User.password == password)
            ).first()

            if not user:
                self.send_error(401)
                return

            self.set_secure_cookie("user", login)
            self.write({"Hello": login})    #cute json 200 answer

    class DataHandler(tornado.web.RequestHandler):
        def get(self) -> None:
            user: bytes = self.get_secure_cookie("user")
            if not user:
                self.send_error(401)
                return

            # select datas from DB
            data_coll: typing.List[typing.Tuple[Data_Collection,]] = db_session.execute(select(Data_Collection)).all()
            dc_json: typing.Dict[str, typing.Any] = {"data": [], "total": len(data_coll)}
            for it, row in enumerate(data_coll):
                data: Data_Collection = row[0]
                dc_json["data"].append({"id": data.id, "data_type": data.data_type, "description": data.description})

            # send datas
            self.write(dc_json)

    #web app initialization
    application = tornado.web.Application([
        (r"/api/login", LoginHandler),
        (r"/api/data",  DataHandler)
    ], cookie_secret='2148')
    application.listen(conf['web_app']['port'])
    print(f"App started")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
