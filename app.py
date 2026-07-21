from flask import Flask, render_template, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import datetime
import os

os.environ['TZ'] = 'UTC' # Make sure the python process always use UTC
app = Flask(__name__)
app.secret_key = '6#1-&75-?66'

#ssh piro-atlas-lab.fysik.su.se
host='piro-atlas-lab-vserver-01.fysik.su.se'
prod_database='tiledb'
dev_database='tiledbdev'


login_template = "login.html"
menu_template = "menu.html"
new_lot_template = "new_lot.html"
new_batch_template = "new_batch.html"
list_lot_template = "list_lot.html"
lot_update_template = "lot_update.html"
list_assembly_template = "list_assembly.html"
batch_update_template = "batch_update.html"
new_dboard_template = "new_dboard.html"
list_dboard_template = "list_dboard.html"
new_test_template = "new_test.html"
list_bench_template = "list_bench.html"
def_kintex_template = "def_kintex.html"


# ------------------------
# Helper Functions
# ------------------------

def get_db_connection():
    """Create and return a database connection using session credentials."""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=session.get('db_user'),
            password=session.get('db_pass'),
            database=session['db_name']
        )
        conn.time_zone = '+00:00' # Make sure that the SQL client always use UTC
        return conn
    except Error as e:
        print("Error while connecting to database:", e)
        return None

# ------------------------
# Routes
# ------------------------

# Login Route
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        development = request.form.get('development')
        if development is not None:
            database=dev_database
        else:
            database=prod_database
        try:
            conn = mysql.connector.connect(
                host=host,
                user=username,
                password=password,
            )
            if conn.is_connected():
                session['logged_in'] = True
                session['db_user'] = username
                session['db_pass'] = password
                session['db_name'] = database
                conn.close()
                return redirect(url_for('menu'))
        except Error as e:
            flash("Error connecting to database: " + str(e))
            return render_template(login_template)
    return render_template(login_template)

# Menu Route
@app.route('/menu')
def menu():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template(menu_template)

# new_component_lot
@app.route('/new_lot', methods=['GET', 'POST'])
def new_lot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    message = ""
    if request.method == 'POST':
        text1 = request.form['text1']
        text2 = request.form['text2']
        text3 = request.form['text3']
        try:
            int1 = int(request.form['int1'])
        except ValueError:
            message = "Please enter valid integers."
            return render_template(new_lot_template, message=message)
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                is_ok=False
                args = (text1, text2, text3, int1, is_ok)
                cursor.callproc('new_component_lot', args)
                conn.commit()
                message = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"

            except Error as e:
                message = "Error executing stored procedure: " + str(e)
            finally:
                cursor.close()
                conn.close()
        else:
            message = "Database connection error."
    return render_template(new_lot_template, message=message)

# new_assembly_batch
@app.route('/new_batch', methods=['GET', 'POST'])
def new_batch():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    message = ""
    if request.method == 'POST':
        text1 = request.form['text1']
        text2 = request.form['text2']
        text3 = request.form['text3']
        try:
            int1 = int(request.form['int1'])
        except ValueError:
            message = "Please enter valid integers."
            return render_template(new_batch_template, message=message)
        
        conn = get_db_connection()
        if conn:
            try:
                int2=-1
                cursor = conn.cursor()
                is_ok=False
                args = (text1, text2, int1, text3, int2, is_ok)
                cursor.callproc('new_assembly_batch', args)
                conn.commit()
                message = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"

            except Error as e:
                message = "Error executing stored procedure: " + str(e)
            finally:
                cursor.close()
                conn.close()
        else:
            message = "Database connection error."
    return render_template(new_batch_template, message=message)

# List component lot
@app.route('/list_lot', methods=['GET', 'POST'])
def list_lot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    error = None
    results = None
    if request.method == 'POST':
        filter_value = request.form.get('filter')
        if not filter_value or filter_value.strip() == "":
            error = "Please provide a valid filter condition."
        else:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = "SELECT typ, manuf_date_code, quantity,received_cern FROM component_lot WHERE typ LIKE %s"
                    like_param = "%" + filter_value + "%"
                    cursor.execute(query, (like_param,))
                    results = cursor.fetchall()
                    if not results:
                        error = "No component lot found!"
                        return render_template(list_lot_template, error=error)
                except Error as e:
                    error = "Error executing query: " + str(e)
                finally:
                    cursor.close()
                    conn.close()
            else:
                error = "Database connection error."
    return render_template(list_lot_template, error=error, results=results)

@app.route('/edit_lot/<lot_mdc>', methods=['GET', 'POST'])
#@app.route('/tiledb/edit_lot/<lot_mdc>', methods=['GET', 'POST'])
def edit_lot(lot_mdc):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mess=None
    error = None
    comment=None
    history=None
    lot=None
    conn = get_db_connection()

    if request.method == 'POST':
        if conn:
            try:
                is_ok=False
                cursor = conn.cursor()
                args = (
                    lot_mdc,
                    request.form.get('pre_ntested') or None,
                    request.form.get('pre_npass') or None,
                    request.form.get('tid_ntested') or None,
                    request.form.get('tid_max') or None,
                    request.form.get('tid_npass') or None,
                    request.form.get('niel_ntested') or None,
                    request.form.get('niel_max') or None,
                    request.form.get('niel_npass') or None,
                    request.form.get('sel_ntested') or None,
                    request.form.get('sel_max') or None,
                    request.form.get('sel_npass') or None,
                    request.form.get('op') or None,
                    request.form.get('comment') or None,
                    is_ok
                )
                status=cursor.callproc('update_component_lot', args)
                print(status)
                conn.commit()
                mess = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"
            except Error as e:
                error = "Error updating lot: " + str(e)
            finally:
                cursor.close()
        else:
            error = "Database connection error."

    if not error:
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM component_lot WHERE manuf_date_code = %s', (lot_mdc,))
                lot = cursor.fetchone()
                if not lot:
                    error = "No component lot found!"
                    return render_template(lot_update_template, error=error)
                query = "SELECT concat(tstamp,' (UTC), ',op,': ',note) as item FROM comment WHERE foreign_typ=1 and foreign_id=%s"
                cursor.execute(query, (lot['id'],))
                history = cursor.fetchall()
            except Error as e:
                error = "Error looking up lot: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template(lot_update_template, mess=mess, error=error,
                                  comment=comment, history=history, lot=lot)

# list assembly batch
@app.route('/list_batch', methods=['GET', 'POST'])
def list_batch():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    error = None
    results = None
    if request.method == 'POST':
        filter_value = request.form.get('filter')
        if not filter_value or filter_value.strip() == "":
            error = "Please provide a valid filter condition."
        else:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = "SELECT received,id,version,IF(atlas_lab,'Yes','No'),quantity FROM assembly_batch WHERE status = %s"
                    like_param = filter_value
                    cursor.execute(query, (like_param,))
                    results = cursor.fetchall()
                    if not results:
                        error = "No assembly batch found!"
                        return render_template(list_assembly_template, error=error)
                except Error as e:
                    error = "Error executing query: " + str(e)
                finally:
                    cursor.close()
                    conn.close()
            else:
                error = "Database connection error."
    return render_template(list_assembly_template, error=error, results=results)

@app.route('/edit_batch/<batch_id>', methods=['GET', 'POST'])
#@app.route('/tiledb/edit_batch/<batch_id>', methods=['GET', 'POST'])
def edit_batch(batch_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mess=None
    error = None
    comment=None
    history=None
    batch=None
    conn = get_db_connection()

    if request.method == 'POST':
        if conn:
            try:
                is_ok=False
                cursor = conn.cursor()
                args = (
                    batch_id,
                    request.form.get('atlas_lab') or None,
                    request.form.get('status') or None,
                    request.form.get('quantity') or None,
                    request.form.get('op') or None,
                    request.form.get('comment') or None,
                    is_ok
                )
                status=cursor.callproc('update_assembly_batch', args)
                print(status)
                conn.commit()
                mess = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"
            except Error as e:
                error = "Error updating assembly batch: " + str(e)
            finally:
                cursor.close()
        else:
            error = "Database connection error."

    if not error:
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM assembly_batch WHERE id = %s', (batch_id,))
                batch = cursor.fetchone()
                if not batch:
                    error = "No assemby batch found!"
                    return render_template(batch_update_template, error=error)
                query = "SELECT concat(tstamp,' (UTC), ',op,': ',note) as item FROM comment WHERE foreign_typ=2 and foreign_id=%s"
                cursor.execute(query, (batch['id'],))
                history = cursor.fetchall()
            except Error as e:
                error = "Error looking up assembly batch: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template(batch_update_template, mess=mess, error=error,
                                  comment=comment, history=history, batch=batch)

@app.route('/new_dboard/<batch_id>', methods=['GET', 'POST'])
def new_dboard(batch_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mess=None
    error = None
    dboard=None
    state=None
    lot_typ=["KIN","PRO","GBT","INA","LTM","MOS","OP4","OK4","OK1","MEM","SFP"]
    lot={}
    for typ in lot_typ:
        lot[typ]={}
    conn = get_db_connection()

    if request.method == 'POST':
        if conn:
            try:
                is_ok=False
                cursor = conn.cursor()
                args = (
                    request.form.get('serial') or None,
                    request.form.get('kintex_a') or None,
                    request.form.get('kintex_b') or None,
                    batch_id,
                    request.form.get('kin') or None,
                    request.form.get('pro') or None,
                    request.form.get('gbt') or None,
                    request.form.get('ina') or None,
                    request.form.get('ltm') or None,
                    request.form.get('mos') or None,
                    request.form.get('op4') or None,
                    request.form.get('ok4') or None,
                    request.form.get('ok1') or None,
                    request.form.get('mem') or None,
                    request.form.get('sfp') or None,
                    is_ok
                )
                for index,item in enumerate(args):
                    if type(item) is str:
                        if item=='': args[index]=None

                status=cursor.callproc('new_daughterboard', args)
                print(status)
                conn.commit()
                mess = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"
                state=status
            except Error as e:
                error = "Error new daughterboard: " + str(e)
            finally:
                cursor.close()
        else:
            error = "Database connection error."

    if not error:
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                for typ in lot_typ:
                    cursor.execute('SELECT manuf_date_code as item FROM component_lot WHERE typ = %s', (typ,))
                    lot[typ] = cursor.fetchall()
            except Error as e:
                error = "Error: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template(new_dboard_template, mess=mess, error=error,state=state,
                                  dboard=dboard, lot=lot, batch_id=batch_id)

# List dautherboard
@app.route('/list_dboard/<batch_id>', methods=['GET', 'POST'])
def list_dboard(batch_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    error = None
    results = None
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT serial_no, kintex_a_id, kintex_b_id,db_status FROM daughterboard WHERE batch_id=%s"
            cursor.execute(query, (batch_id,))
            results = cursor.fetchall()
            if not results:
                error = "No daughterboards found!"
                return render_template(list_dboard_template, error=error,
                                              batch_id=batch_id)
        except Error as e:
            error = "Error executing query: " + str(e)
        finally:
            cursor.close()
            conn.close()
    else:
        error = "Database connection error."
    return render_template(list_dboard_template, error=error, results=results,
                                  batch_id=batch_id)

# List bench test
@app.route('/list_bench', methods=['GET', 'POST'])
def list_bench():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    error = None
    results = None
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT test_start,test_stop,test_op,db_slot1,db_slot2,db_slot3,db_slot4 FROM benchtest where test_pass=1 order by test_stop desc limit 100"
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                error = "No bench tests found!"
                return render_template(list_bench_template, error=error)
        except Error as e:
            error = "Error executing query: " + str(e)
        finally:
            cursor.close()
            conn.close()
    else:
        error = "Database connection error."
    return render_template(list_bench_template, error=error, results=results)

@app.route('/new_test', methods=['GET', 'POST'])
def new_test():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mess = None
    error = None
    bench = None
    conn = get_db_connection()

    if request.method == 'POST':
        if conn:
            try:
                is_ok=False
                id_p=-1
                cursor = conn.cursor()

                if request.form.get('bench_id') is None:
                    args = (
                        request.form.get('db_slot1') or None,
                        request.form.get('db_slot2') or None,
                        request.form.get('db_slot3') or None,
                        request.form.get('db_slot4') or None,
                        id_p,
                        is_ok
                    )
                    if args[0] is None and args[1] is None and args[2] is None and args[3] is None:
                        raise Error("at least one daughterboard must be provided")               
                    status=cursor.callproc('new_benchtest', args)
                    print(status)
                    id_p=status[4]
    
                    args = (
                        id_p,
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') or None,
                        None,
                        request.form.get('test_op') or None,
                        1,
                        request.form.get('comment') or None,
                        is_ok
                    )
                    if args[3] is None or args[5] is None:
                        conn.rollback()
                        raise Error("OP initials and a comment must be provided")
                    status=cursor.callproc('update_benchtest', args)
                    print(status)
                else:
                    args = (
                        request.form.get('bench_id'),
                        None,
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') or None,
                        request.form.get('test_op') or None,
                        request.form.get('test_pass') or None,
                        request.form.get('comment') or None,
                        is_ok
                    )
                    status=cursor.callproc('update_benchtest', args)
                    print(status)

                conn.commit()
                mess = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"
            except Error as e:
                conn.rollback()
                error = "Error new benchtest: " + str(e)
            finally:
                cursor.close()
        else:
            error = "Database connection error."

    if not error:
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM benchtest WHERE test_stop is null limit 1')
                bench = cursor.fetchone()
                print(bench)
            except Error as e:
                error = "Error looking up assembly bench test: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template(new_test_template, mess=mess, error=error, bench=bench)

@app.route('/def_kintex', methods=['GET', 'POST'])
def def_kintex():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mess=None
    error = None
    conn = get_db_connection()

    if request.method == 'POST':
        if conn:
            try:
                is_ok=False
                id_p=-1
                cursor = conn.cursor()
                args = (
                    request.form.get('id') or None,
                    request.form.get('kintex_a') or None,
                    request.form.get('kintex_b') or None,
                    is_ok
                )
                if args[0] is None or args[1] is None or args[2] is None:
                    raise Error("all fields must be provided")
                status=cursor.callproc('define_kintex', args)
                print(status)
                conn.commit()
                mess = "Data submitted successfully "+datetime.datetime.now().ctime()+" (UTC)"
            except Error as e:
                error = "Error new benchtest: " + str(e)
            finally:
                cursor.close()
        else:
            error = "Database connection error."

    return render_template(def_kintex_template, mess=mess, error=error)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------
# Main Entry Point
# ------------------------

if __name__ == '__main__':
    app.run(host='127.0.0.1',debug=True)
