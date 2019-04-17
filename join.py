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
CREATE FUNCTION can_access_page(page_id BIGINT, user_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE has_access BOOLEAN := false;
BEGIN
  SELECT true FROM page_user AS page
    WHERE page.page_id = $1 AND page.user_id = $2
  INTO has_access;

RETURN has_access;
end;
$$ LANGUAGE plpgsql STABLE;
'''
    cur.execute(function)
    policy = '''
CREATE POLICY page_access ON page_photo
  USING(
    can_access_page(
      page_id, 
      current_setting('app.user_id')::BIGINT
    )
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
def join(conn, ids):
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
    click.echo("Setting up join function and policy")
    setup(conn)
    actual = join(conn, users)
    if actual != expected:
        raise Exception('Baseline and join query return different results.')

if __name__ == '__main__':
    main()
