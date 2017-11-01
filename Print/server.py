from flask import Flask, render_template, request, g, jsonify
import sqlite3, os, hashlib, time, base64, math, re

_DATABASE = './util.db'
_MASTER_KEY = '0123456789abcdef'

_SERVICE_BEGIN = 0
_SERVICE_LEN = 0

app = Flask(__name__, static_url_path='/static')

clearwhite = re.compile('\\s', re.M | re.U)
clearblank = re.compile('\\n\\n\\n+', re.M | re.U)

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], str(value))
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(_DATABASE)
        db.row_factory = make_dicts
    return db


def query_db(query, args=(), one=False, ret=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if ret:
        return (rv[0] if rv else None) if one else rv
    else:
        return None


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()


'''
主界面
'''


@app.route('/')
def index_json():
    logined = False
    error = False
    error_text = ""
    username = request.cookies.get('username', -1)
    password = request.cookies.get('password', -1)
    if username == -1:
        error = True
        error_text = "Not Login"
    else:
        try:
            res = query_db('SELECT * FROM `user` WHERE `name` = ? AND `passwd` = ? LIMIT 1',
                           args=(username, password), ret=True)
            if (len(res) != 0):
                logined = True
                teamname = res[0]['note']
            else:
                error = True
                error_text = "Wrong Password"
        except:
            error_text = "Unknown Error"
            error = True
    return render_template('index.html', logined = logined, error = error, error_text = error_text, username = username, teamname = teamname)


'''
用户登陆
'''


@app.route('/login.json', methods=['POST'])
def login_json():
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        res = query_db('SELECT * FROM `user` WHERE `name` = ? AND `passwd` = ? LIMIT 1',
                       args=(username, password), ret=True)
        if (len(res) == 0):
            return jsonify({'result': 'fail', 'text': 'Wrong Password'})
        else:
            return jsonify({'result': 'success', 'text': 'Login Success!'})
    except:
        return jsonify({'result': 'fail', 'text': 'Unknown Error'})


'''
用户提交打印任务
'''


@app.route('/print.json', methods=['POST'])
def print_json():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    res = query_db('SELECT * FROM `user` WHERE `name` = ? AND `passwd` = ? LIMIT 1',
                   args=(username, password), ret=True)
    if (len(res) == 0):
        return jsonify({'result': 'fail', 'text': 'Please Login'})
    code = clearblank.sub('\n\n', request.form['code'])
    code_to_sha256 = clearwhite.sub('', code)
    m = hashlib.sha256()
    m.update(code_to_sha256.encode('utf-8'))
    uid = m.hexdigest()
    length = len(code)
    if (length > 8192 or length < 64):
        return jsonify({'result': 'fail', 'text': 'Task is too short or too long'})
    try:
        query_db(
            'INSERT INTO `task` (`uid`, `user`, `content`, `status`, `submit`, `printkey`, `lastupdate`, `len`) VALUES (?, ? , ?, ?, ?, ?, ?, ?)',
            args=(uid, username, code, 0, int(time.time()), '', int(time.time()), length), ret=False)
        return jsonify({'result': 'success', 'text': uid})
    except:
        return jsonify({'result': 'fail', 'text': 'Duplicate task (original task id is {})'.format(uid[0:7])})

'''
用户获取打印任务状态
'''


@app.route('/result.json')
def result_json():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    res = query_db('SELECT * FROM `user` WHERE `name` = ? AND `passwd` = ? LIMIT 1',
                   args=(username, password), ret=True)
    if (len(res) == 0):
        return jsonify({'result': 'fail', 'text': 'Please login'})
    ret = query_db('SELECT `uid`, `submit`, `len`, `status` FROM `task` WHERE `user` = ? ORDER BY `submit` DESC', args=(username, ), ret=True)
    return jsonify({'result': 'success', 'data': ret})


'''
打印机获取未打印任务
'''


@app.route('/admin/<key>/<tim>/fetch.json')
def admin_fetch_json(key, tim):
    if (math.sqrt((int(tim) - time.time()) ** 2) > 30):
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    m = hashlib.sha256()
    m.update((tim+":"+_MASTER_KEY).encode('utf-8'))
    auth = m.hexdigest()
    if not auth == key:
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    m.update(str(time.time()).encode('utf-8'))
    printkey = m.hexdigest()[0:16]
    query_db('''UPDATE `task` SET `printkey` = ? , `status` = ? WHERE rowid IN (SELECT rowid
                FROM `task`
                WHERE `status` = ?
                ORDER BY `submit` ASC
                LIMIT 1)''', args=(printkey, 1, 0))
    ret = query_db('SELECT * FROM `task` WHERE `printkey` = ?', args = (printkey, ), one = True, ret = True)
    user = {}
    if (ret != None):
        user = query_db('SELECT * FROM `user` WHERE `name` = ?', args = (ret['user'], ), one = True, ret = True)
        return jsonify({'result':'success', 'text':'', 'data': ret, 'user': user})
    else:
        return jsonify({'result':'fail', 'text': '无打印任务'})


'''
打印机传送打印状态
'''


@app.route('/admin/<key>/<tim>/<printkey>/update.json')
def admin_update_json(key, tim, printkey):
    if (math.sqrt((int(tim) - time.time()) ** 2) > 30):
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    m = hashlib.sha256()
    m.update((tim+":"+_MASTER_KEY).encode('utf-8'))
    auth = m.hexdigest()
    if not auth == key:
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    query_db('UPDATE `task` SET `status` = ? WHERE `printkey` = ?', args = (2, printkey))
    return jsonify({'result': 'success', 'text':'成功设置'})

@app.route('/admin/<key>/<tim>/<status>/<printkey>/update.json')
def admin_update_json(key, tim, status, printkey):
    if (math.sqrt((int(tim) - time.time()) ** 2) > 30):
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    m = hashlib.sha256()
    m.update((tim+":"+_MASTER_KEY).encode('utf-8'))
    auth = m.hexdigest()
    if not auth == key:
        return jsonify({'result':'fail', 'text':'认证失败，检查一下时间？'})
    query_db('UPDATE `task` SET `status` = ? WHERE `printkey` = ?', args = (status, printkey))
    return jsonify({'result': 'success', 'text':'成功设置'})



if __name__ == '__main__':
    app.run('0.0.0.0')
