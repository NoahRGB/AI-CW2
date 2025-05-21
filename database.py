#cd C:/Program Files/PostgreSQL/17/bin (replace 17 with postgre version)
#createdb -h localhost -p 5432 -U postgres AIDB
#Password: password
import psycopg2
def connectDB():
    password = "password"
    DBName = "AIDB"
    #database connection
    conn = psycopg2.connect(
       database=DBName, user='postgres', password=password, host='127.0.0.1', port= '5432'
    )
    conn.autocommit = True
    #this allows for command execution
    cur = conn.cursor()
    return conn, cur
def runQuery(query, conn, cur):
    #runs the query and closes the connection
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close

def deleteTable():
    conn, cur = connectDB()
    runQuery("DROP TABLE IF EXISTS recents;", conn, cur)
    
    
def createDatabase():
    #creating the database
    conn, cur = connectDB()
    query = '''
    CREATE TABLE IF NOT EXISTS recents (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    dep_location VARCHAR(100),
    destination VARCHAR(100),
    dep_time TIME,
    dep_date DATE,
    query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    runQuery(query, conn, cur)

def insert_query(dep_loc, destination, dep_time, dep_date):
    conn, cur = connectDB()
    #query inserts new query into database
    query = '''
    INSERT INTO recents (dep_location, destination, dep_time, dep_date)
    VALUES (%s, %s, %s, %s);
    '''
    cur.execute(query, (dep_loc, destination, dep_time, dep_date))
    #query deletes oldest if theres more than 5
    query2 = '''
    DELETE FROM recents
    WHERE id IN (
        SELECT id FROM recents
        ORDER BY query_time DESC
        OFFSET 5
        );
        '''
    runQuery(query2, conn, cur)

def getRecents():
    conn, cur = connectDB()
    #selects all rows and orders them by newest time of creation
    query = '''
    SELECT id, dep_location, destination, dep_time, dep_date
    FROM recents
    ORDER BY query_time DESC;
    '''
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def openRecent(row):
    #opens the selected query and returns the values
    rows = getRecents()
    recent = rows[row-1]
    id, dep_location, destination, dep_time, dep_date = recent
    return id, dep_location, destination, dep_time, dep_date

def updateRecent(id, dep_location, destination, dep_time, dep_date):
    #updates the id of the row that was opened with new values
    conn, cur = connectDB()
    query = '''
    UPDATE recents
    SET dep_location = %s, destination = %s, dep_time = %s, dep_date = %s, query_time = CURRENT_TIMESTAMP 
    WHERE id = %s
    '''
    cur.execute(query, (dep_location, destination, dep_time, dep_date, id))
    conn.commit()
    cur.close()
    conn.close
    
def existingQuery(dep_location, destination, dep_time, dep_date):
    conn, cur = connectDB()
    query = '''
            SELECT * FROM recents
            WHERE dep_location = %s AND destination = %s AND dep_time = %s AND dep_date = %s
        '''
    cur.execute(query, (dep_location, destination, dep_time, dep_date))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if rows:
        return True
    else:
        return False


