import psycopg2, time

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed


def index(conn):
    indexes = [
        '''
CREATE INDEX page_photo_page_id ON page_photo (page_id);
''',
        '''
CREATE INDEX page_user_user_id ON page_user (user_id);
'''
    ]
    cur = conn.cursor()
    for index in indexes:
        cur.execute(index)
    cur.close( )
    conn.commit( )

@timeit
def baseline(conn, ids):
    counts = {}
    
    sql = '''
SELECT * FROM page_photo
INNER JOIN page_user 
    ON (page_user.page_id = page_photo.page_id)
WHERE page_user.user_id = {}
'''
    for id in ids:
        cur = conn.cursor()
        query = sql.format(id)
        cur.execute(query)
        results = cur.fetchall()
        counts[id] = len(results)
        cur.close( )
    return counts

def version(conn):
    cur = conn.cursor()
    print('PostgreSQL database version:')
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    print(db_version)
    cur.close()