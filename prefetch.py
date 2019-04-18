#!/usr/bin/env python3
import psycopg2, click, random
from common import index, baseline, timeit, version

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

    function = '''
CREATE OR REPLACE FUNCTION set_allowed_user_ids(user_id INT)
RETURNS VOID AS $$
DECLARE allowed text;
BEGIN
    SELECT string_agg(page_id::varchar, ',')  INTO allowed from page_user p WHERE p.user_id = $1;
    perform set_config('app.allowed_user_ids', allowed, true);
END 
$$
LANGUAGE plpgsql;
  '''
    cur.execute(function)

    policy = '''
CREATE POLICY page_access ON page_photo
  USING(
      page_id = ANY (string_to_array(current_setting('app.allowed_user_ids'), ',')::int[])
    );
'''
    cur.execute(policy)
    user = '''
set role rls_test_user;
'''
    cur.execute(user)
    conn.commit()
    cur.close( )

def allowed_ids(conn, id):
  sql = '''
  SELECT page_id from page_user where user_id = {}
  '''
  cur = conn.cursor()
  query = sql.format(id)
  cur.execute(query)
  results = cur.fetchall()
  cur.close( )
  return map(str, [result[0] for result in results])

@timeit
def prefetch(conn, ids):
    counts = {}
    sql = '''
SELECT set_allowed_user_ids({});
SELECT * FROM page_photo;
'''
    for id in ids:
        query = sql.format(id)
        cur = conn.cursor( )
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
    click.echo("Setting up join function and policy")
    setup(conn)
    actual = prefetch(conn, users)
    if actual != expected:
        raise Exception('Baseline and join query return different results.')

if __name__ == '__main__':
    main()
