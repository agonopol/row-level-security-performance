#!/usr/bin/env python3
import psycopg2, click, random
from common import version 

def init(conn):

    tables = [
'''create table if not exists page_user (
  page_id INTEGER not null primary key,
  user_id INTEGER not null
);''',

'''create table if not exists page (
  id INTEGER not null primary key,
  name TEXT not null,
  public BOOL not null
);''',

'''create table if not exists page_photo (
  id INTEGER not null primary key,
  image_url TEXT not null,
  page_id INTEGER not null
);''']

    cur = conn.cursor()
    for table in tables:
        click.echo(f'Executing \n{table}')
        cur.execute(table)
    conn.commit()
    cur.close()

def populate_page_user(conn):
    cur = conn.cursor()
    data = [(x,x) for x in range(10000)]
    records = ','.join(['%s'] * len(data))
    sql = 'INSERT INTO page_user(page_id, user_id) VALUES {}'.format(records)
    cur.execute(sql, data)
    cur.close( )

def populate_page(conn):
    cur = conn.cursor()
    data = [(x, f'http://localhost/{x}.html', bool(random.getrandbits(1))) for x in range(10000)]
    records = ','.join(['%s'] * len(data))
    sql = 'INSERT INTO page(id, name, public) VALUES {}'.format(records)
    cur.execute(sql, data)
    cur.close( )

def populate_page_photo(conn):
    cur = conn.cursor()
    data = [(x,f'http://localhost/{x}.jpg', random.randint(0, 10000)) for x in range(100000)]
    records = ','.join(['%s'] * len(data))
    sql = 'INSERT INTO page_photo(id, image_url, page_id) VALUES {}'.format(records)
    cur.execute(sql, data)
    cur.close( )


@click.command()
@click.option('--port', default=5496, help='number of greetings')
def populate(port):
    conn = psycopg2.connect(host="localhost",database="postgres", user="postgres", password="postgres", port=port)
    version(conn)
    click.echo('Setting up tables')
    init(conn)
    click.echo('Populating page_user')
    populate_page_user(conn)
    click.echo('Populating page')
    populate_page(conn)
    click.echo('Populating page_photo')
    populate_page_photo(conn)
    conn.commit( )

if __name__ == '__main__':
    populate()
