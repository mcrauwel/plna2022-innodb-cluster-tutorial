'''
    A Simple Traffic Simulator 
'''

from threading import Thread 
from pymysql import connect 
import yaml,sys,os,time,random,string
from http.server import HTTPServer,BaseHTTPRequestHandler

# GLobal Variables for status
global_values={
    'writer_last_run': 500,
    'reader_last_run': 200,
    'reader_continue': True,
    'writer_continue': True,
    'reader_pause_interval': 0.1,
    'writer_pause_interval': 1,
    'reader_port': 0,
    'writer_port': 0,
    'total_rows_last_calc': 0,
    'insert_count': 3
}

TABLE_CREATION="""CREATE TABLE IF NOT EXISTS application_data ( id bigint not null auto_increment primary key, vc VARCHAR(64) NOT NULL, hash_key VARCHAR(64) NOT NULL, action_time DATETIME ) ENGINE=INNODB"""

def safe_sleep(sleeptime):
    try:
        time.sleep(sleeptime)
    except:
        return


class StatusRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if global_values['writer_last_run'] == 500 and global_values['reader_last_run'] == 500:
            resp_code = 500
        elif global_values['writer_last_run'] == 500 and global_values['reader_last_run'] == 500:
            resp_code = 205
        else:
            resp_code = 200
        content="""writer_port=%s
reader_port=%s
writer_last_run=%s
reader_last_run=%s
total_rows_last_calc=%s
""" % (global_values['writer_port'],global_values['reader_port'],global_values['writer_last_run'],global_values['reader_last_run'],global_values['total_rows_last_calc'])
        self.send_response(resp_code)
        self.send_header("Content-type", "text/text")
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
        
class WriterThread(Thread):
    def __init__(self,port):
        Thread.__init__(self)
        self.__port = port
        self.__host = '127.0.0.1'
        self.__user = 'application'
        self.__passw = 'application'
        self.__db = 'application'
    
    def run(self):
        try:
            dbc = connect(host=self.__host,user=self.__user,port=self.__port,passwd=self.__passw,database=self.__db)
            cursor = dbc.cursor()
            cursor.execute(TABLE_CREATION)
            cursor.close()
            dbc.close()
        except:
            pass
        while global_values['writer_continue']:
            dbc=None
            connection_open=False
            try:
                dbc = connect(host=self.__host,user=self.__user,port=self.__port,passwd=self.__passw,database=self.__db)
                cursor = dbc.cursor()
                value_list = []
                for i in range(global_values['insert_count']):
                    value_list.append(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(63)))
                final_list = map(lambda l: "( '%s', MD5('%s'), NOW() )" % (l,l),value_list)
                cursor.execute("""INSERT INTO application_data ( vc, hash_key, action_time ) VALUES %s""" % ", ".join(final_list))
                cursor.execute("""commit""")
                cursor.close()
                dbc.close()
                connection_open=False
                global_values['writer_last_run'] = 200
            except:
                if connection_open and dbc:
                    try:
                        dbc.close()
                    except:
                        pass
                global_values['writer_last_run'] = 500
            safe_sleep(global_values['writer_pause_interval'])

class ReaderThread(Thread):
    def __init__(self,port):
        Thread.__init__(self)
        self.__port = port
        self.__host = '127.0.0.1'
        self.__user = 'application'
        self.__passw = 'application'
        self.__db = 'application'

    def run(self):
        while global_values['reader_continue']:
            connection_open=False
            dbc=None 
            try:
                dbc = connect(host=self.__host,user=self.__user,port=self.__port,passwd=self.__passw,database=self.__db)
                connection_open=True
                cursor = dbc.cursor()
                rand_portion = ''.join(random.choice('abcdef' + string.digits) for _ in range(3))
                queries = [
                    "SELECT * FROM application_data WHERE hash_key LIKE '%%%s%%'" % rand_portion,
                    "SELECT * FROM application_data WHERE action_time > DATE_SUB(NOW(),INTERVAL %s MINUTE)" % random.randint(1,10) 
                ]
                cursor.execute("BEGIN")
                for query in queries:
                    cursor.execute(query)
                    v = cursor.fetchall()
                cursor.execute("SELECT COUNT(*) FROM application_data")
                global_values['total_rows_last_calc'] = cursor.fetchone()[0]
                cursor.execute('COMMIT')
                cursor.close()
                dbc.close()
                connection_open=False
                global_values['writer_last_run']=200
            except:
                global_values['reader_last_run']=500
                if connection_open and dbc:
                    try:
                        dbc.close()
                    except:
                        pass

            safe_sleep(global_values['reader_pause_interval'])



if __name__ == '__main__':
    if not os.path.exists(sys.argv[1]):
        print("Config File Specified Does not exist: %s" % sys.argv[1])
        sys.exit(1)
    fd = open(sys.argv[1])
    config = yaml.load(fd)
    rt = ReaderThread(config['ReaderPort'])
    wt = WriterThread(config['WriterPort'])
    global_values['reader_port'] = config['ReaderPort']
    global_values['writer_port'] = config['WriterPort']
    rt.setDaemon(True)
    wt.setDaemon(True)
    wt.start()
    # to allow for the table to created on the first run
    safe_sleep(0.1)
    rt.start()
    
    local_address = ( '0.0.0.0', 5000 )
    server = HTTPServer(local_address,StatusRequestHandler)
    server.serve_forever()
