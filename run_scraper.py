import argparse
import typing

import yaml
import requests

from pprint import pprint
from prettytable import PrettyTable
from bs4 import BeautifulSoup, Tag

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.future import Engine

#internal libs
from db_init import User, Data_Collection


def get_raw_table(trs: typing.List[Tag]) -> typing.List[typing.List[str]]:
    # getting list of `<tr>...</tr>` tags
    # return list of lists of text from table ceils
    return [[td.text for td in tr.find_all('td')] for tr in trs]


def str2bool(v: str) -> bool:
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


def main() -> None:
    # read the configs
    with open("config.yaml", "r") as f:
        conf: typing.Dict[str, typing.Any] = yaml.safe_load(f)

    print("Parsing tables...")
    scrap_url: str = "https://websitesetup.org/sql-cheat-sheet/"
    response: requests.Response = requests.get(scrap_url)
    soup = BeautifulSoup(response.text, "html.parser")
    tables: typing.List[Tag] = soup.find_all('table')

    for table in tables:
        #seeking 'string data type' table
        trs: typing.List[Tag] = table.tbody.find_all('tr')
        if trs and trs[0].th and trs[0].th.text == "String Data Types":
            raw_table: typing.List[typing.List[str]] = get_raw_table(trs[2:])
            break
    else:
        raise Exception('Table not found')

    #parse script arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--dry_run', '-d', dest="dry_run", default='false')
    args: argparse.Namespace = arg_parser.parse_args()

    if(str2bool(args.dry_run)):
        # output in console
        ptable = PrettyTable()
        ptable.field_names = ["Types", "Descriptions"]
        ptable.max_width["Descriptions"] = 64
        ptable.align = "l"
        ptable.add_rows(raw_table)
        print(ptable)
    else:
        # output in DB
        db_url: str = f"postgresql://{conf['db']['user']}:{conf['db']['password']}@{conf['db']['host']}:{conf['db']['port']}/{conf['db']['name']}"
        print(f"Connection to {db_url}")
        db_engine: Engine = create_engine(db_url)
        db_session = Session(db_engine)

        # delete old data
        print('Deleting old data...')
        rows_to_delete: typing.List[typing.Tuple[Data_Collection,]] = db_session.execute(select(Data_Collection)).all()
        for row in rows_to_delete:
            db_session.delete(row[0])

        # insert new data
        print('Adding new data...')
        for i, row in enumerate(raw_table):
            data_row = Data_Collection(id=i, data_type=row[0], description=row[1])
            db_session.add(data_row)

        db_session.flush()
        db_session.commit()
        print(f"DB succesfull updated!")


if __name__ == "__main__":
    main()
