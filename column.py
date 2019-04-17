#!/usr/bin/env python3
import psycopg2, click, random
from common import index, baseline, timeit, version


def update(conn):
    cur = conn.cursor( )
    cur.execute('SELECT page_id, user_id from page_user')
    results = cur.fetchall( )
    for result in results:
        cur.execute("UPDATE page_photo SET allowed_users = '{%d}' WHERE page_id = %d" % (result[1], result[0]))
    cur.close( )
    conn.commit( )

    
def setup(conn):
    cur = conn.cursor()
    role = '''
create role rls_test_user NOINHERIT;
grant select, insert, update 
   on page, page_photo, page_user
   to rls_test_user;
'''
    cur.execute(role)
    security = '''
alter table page_photo enable row level security;
'''
    cur.execute(security)
    column = '''
ALTER TABLE page_photo
ADD COLUMN allowed_users INTEGER[];
'''
    cur.execute(column)
    update(conn)
    policy = '''
CREATE POLICY page_access ON page_photo
  USING(
    current_setting('app.user_id')::BIGINT = ANY (page_photo.allowed_users::int[])
  );
'''
    cur.execute(policy)
    user = '''
set role rls_test_user;
'''
    cur.execute(user)
    conn.commit()
    cur.close( )

@timeit
def column(conn, ids):
    counts = {}
    sql = '''
SET LOCAL app.user_id = {};
SELECT * FROM page_photo;
'''
    for id in ids:
        cur = conn.cursor()
        query = sql.format(id)
        cur.execute(query)
        results = cur.fetchall()
        counts[id] = len(results)
        cur.close( )
    return counts

@click.command()
@click.option('--port', default=5496, help='number of greetings')
def main(port):
    conn = psycopg2.connect(host="localhost",database="postgres", user="postgres", password="postgres", port=port)
    version(conn)
    users = [random.randint(0, 10000) for x in range(1000)]
    click.echo("Establishing baseline with pure join, 1000 queries")
    index(conn)
    expected = baseline(conn, users)
    click.echo("Setting up column function and policy")
    setup(conn)
    click.echo("Performance testing column query policy")
    actual = column(conn, users)
    if actual != expected:
        raise Exception('Baseline and join query return different results.')

if __name__ == '__main__':
    main()
