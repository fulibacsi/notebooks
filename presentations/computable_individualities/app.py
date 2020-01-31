import os
import sqlite3
import argparse

from flask import Flask, render_template, request


app = Flask(__name__,
            template_folder=os.path.abspath('web'),
            static_folder=os.path.abspath('web'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/log', methods=['POST'])
def log():
    results = request.json

    db = sqlite3.connect('./data/results.db')
    with db as cursor:
        cursor.execute(f'''INSERT INTO results
                           VALUES ('{results['ai']}',
                                   '{results['result']}',
                                   '{results['user']}',
                                   '{results['turn']}');''')
    db.close()

    return 'success'


def create_table():
    db = sqlite3.connect('./data/results.db')
    c = db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (ai text,
                  result text,
                  user text,
                  turn integer);''')
    db.commit()
    db.close()


def drop_table():
    db = sqlite3.connect('./data/results.db')
    with db as cursor:
        cursor.execute('DROP TABLE results')
    db.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, help='command to run',
                        choices=["create_db", "clear_db", "server"])
    return parser.parse_args()


if __name__ == "__main__":
    command = parse_args().command

    if command == 'server':
        app.run(debug=True, host='0.0.0.0')
    elif command == 'create_db':
        create_table()
    elif command == 'clear_db':
        # no truncation available in SQLite3, so DROP table then CREATE again
        drop_table()
        create_table()
