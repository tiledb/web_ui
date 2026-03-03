from flask import Flask, render_template_string, request, redirect, url_for, session, flash
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

# Login Page Template
login_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 300px; margin: 100px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"], input[type="password"] { width: 94%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 100%; background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        ul { list-style-type: none; padding: 0; }
        li { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <h2>TileDB</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <form method="POST" action="{{ url_for('login') }}">
            <label>Username</label>
            <input type="text" name="username" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <input type="checkbox" name="development" id=development value=True>
            <label for="dev">Development</label><br><br>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

# Menu Page Template
menu_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Menu</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 400px; margin: 100px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; }
        a { display: block; margin: 10px 0; text-decoration: none; color: #4CAF50; font-weight: bold; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        .tab {display: inline-block;}
    </style>
</head>
<body>
    <div class="container">
        <h2>Choose operation</h2>
        <div class="tab"><a href="{{ url_for('new_lot') }}"><u>Create</u></a></div>
        <div class="tab"><a href="{{ url_for('list_lot') }}"> or <u>list/update</u> component lot</a></div>
        <br>
        <div class="tab"><a href="{{ url_for('new_batch') }}"><u>Create</u></a></div>
        <div class="tab"><a href="{{ url_for('list_batch') }}"> or <u>list/update</u> assembly batch</a></div>
        <br>
        <div class="tab"><a href="{{ url_for('def_kintex') }}"><u>Define</u> daughterboard kintex ID</a></div>
        <br>
        <div class="tab"><a href="{{ url_for('new_test') }}"><u>Start/stop</u></a></div>
        <div class="tab"><a href="{{ url_for('list_bench') }}"> or <u>list</u> bench test </a></div>
        <br><br>
        <form method="GET" action="{{ url_for('logout') }}">
            <button type="submit">Logout</button>
        </form>
    </div>
</body>
</html>
"""

# Create component lot
new_lot_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Create component lot</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 400px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"], input[type="number"] { width: 96%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>Create component lot:</h2>
        {% if message %}
          <p>{{ message }}</p>
        {% endif %}
        <form method="POST" action="{{ url_for('new_lot') }}">
            <label>Type</label><br>
            <select name="text1" id="text1" required>
                <option value="KIN">KIN</option>
                <option value="PRO">PRO</option>
                <option value="GBT">GBT</option>
                <option value="INA">INA</option>
                <option value="LTM">LTM</option>
                <option value="MOS">MOS</option>
                <option value="OP4">OP4</option>
                <option value="OK4">OK4</option>
                <option value="OK1">OK1</option>
                <option value="MEM">MEM</option>
                <option value="SFP">SFP</option>
            </select><br>
            <label>Date received (YYYY-MM-DD)</label>
            <input type="text" name="text2" required>
            <label>Manufacture date code</label>
            <input type="text" name="text3" required>
            <label>Quantity</label>
            <input type="number" name="int1" required>
            <button type="submit">Create new</button>
        </form>
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

# Create assemby batch
new_batch_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Create assembly batch</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 400px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"], input[type="number"] { width: 96%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>Create assembly batch</h2>
        {% if message %}
          <p>{{ message }}</p>
        {% endif %}
        <form method="POST" action="{{ url_for('new_batch') }}">
            <label>Date received (YYYY-MM-DD)</label>
            <input type="text" name="text1" required>
            <label>Received by (name initals)</label>
            <input type="text" name="text2" required>
            <label>Version</label>
            <input type="text" name="text3" required>
            <label>Quantity</label>
            <input type="number" name="int1" required>
            <button type="submit">Create new</button>
        </form>
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

# List component lot
list_lot_template = """
<!DOCTYPE html>
<html>
<head>
    <title>List component lot</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 600px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 0px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f2f2f2; }
        p { color: red; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>List component lot</h2>
        <form method="POST" action="{{ url_for('list_lot') }}">
            <label>Please provide type</label><br>
            <select name="filter" id="filter" required>
                <option value="KIN">KIN</option>
                <option value="PRO">PRO</option>
                <option value="GBT">GBT</option>
                <option value="INA">INA</option>
                <option value="LTM">LTM</option>
                <option value="MOS">MOS</option>
                <option value="OP4">OP4</option>
                <option value="OK4">OK4</option>
                <option value="OK1">OK1</option>
                <option value="MEM">MEM</option>
                <option value="SFP">SFP</option>
            </select><br>
            <button type="submit">Search</button>
        </form>
        {% if error %}
            <p>{{ error }}</p>
        {% endif %}
        {% if results %}
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Manufacture date code</th>
                        <th>Quantity</th>
                        <th>Received date</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in results %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td><a href="{{ url_for('edit_lot',lot_mdc=row[1]) }}">{{ row[1] }}</a></td>
                            <td>{{ row[2] }}</td>
                            <td>{{ row[3] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        <br>
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

lot_update_template= """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Edit component lot: {{ lot.manuf_date_code }}</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 670px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="number"] { width: 90px; padding: 2px; margin: 3px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        textarea { resize: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Edit component lot: {{ lot.manuf_date_code }}</h2>
        {% if error %}
            <p style="color:red;">{{ error }}</p>
        {% else %}
            {% if mess %}
                <p>{{ mess }}</p>
            {% endif %}
            <form method="post">
                <label>Type: {{ lot.typ }}</label><br>
                <label>Received CERN: {{ lot.received_cern }}</label><br>
                <label>Manufacturing Date Code: {{ lot.manuf_date_code }}</label><br>
                <label>Quantity: {{ lot.quantity }}</label><br><br>
                <table style="border: 1px solid black; padding: 5px"><tbody>
                <tr><td>Pre N Tested</td>
                <td><input type="number" name="pre_ntested" value="{{ lot.pre_ntested }}"></td>
                <td width="5%"></td>
                <td>Comment</td><td style="vertical-align:top" rowspan="3">
                <textarea name="comment" cols="30" rows="3" placeholder="please leave a note"></textarea></td>
                </tr>
                <tr><td>Pre N Pass</td>
                <td><input type="number" name="pre_npass" value="{{ lot.pre_npass }}"></td>
                </tr>
                <tr><td>TID N Tested</td>
                <td><input type="number" name="tid_ntested" value="{{ lot.tid_ntested }}"></td></tr>
                <tr><td><label>TID Max [Gy]</td>
                <td><input type="number" name="tid_max" step="any" min=0 value="{{ lot.tid_max }}"></td>
                <td></td>
                <td>Operator:</td><td>
                <textarea name="op" rows="1" cols="30" placeholder="please provide your initials"></textarea></td>
                </tr>
                <tr><td><label>TID N Pass</td>
                <td><input type="number" name="tid_npass" value="{{ lot.tid_npass }}"></td>
                </tr>
                <tr><td><label>NIEL N Tested</td>
                <td><input type="number" name="niel_ntested" value="{{ lot.niel_ntested }}"></td>
                <td></td><td>History</td>
                <td rowspan="3" style="vertical-align:top">
                <div>
                    <select name="comments" id="comments" style="width: 210px;">
                    {% for row in history %}
                        <option> {{ row.item }} </option>
                    {% endfor %}
                    </select>
                </div>
                </td>                
                </tr>                
                <tr><td><label>NIEL Max [E12 cm-2]</td>
                <td><input type="number" step="any" min=0 name="niel_max" value="{{ lot.niel_max }}"></td></tr>
                <tr><td><label>NIEL N Pass</td>
                <td><input type="number" name="niel_npass" value="{{ lot.niel_npass }}"></td></tr>
                <tr><td><label>SEL N Tested</td>
                <td><input type="number" name="sel_ntested" value="{{ lot.sel_ntested }}"></td></tr>
                <tr><td><label>SEL Max [E11 cm-2]</td>
                <td><input type="number" step="any" min=0 name="sel_max" value="{{ lot.sel_max }}"></td></tr>
                <tr><td><label>SEL N Pass</td>
                <td><input type="number" name="sel_npass" value="{{ lot.sel_npass }}"></td></tr>
                </tbody></table>
                <button type="submit">Save</button>
            </form>
        {% endif %}
        <a href="{{ url_for('list_lot') }}">Return to Lots</a>
        <a href="{{ url_for('menu') }}"> or Menu</a>
    </div>
</body>
</html>
"""

# List assembly batch
list_assembly_template = """
<!DOCTYPE html>
<html>
<head>
    <title>List assembly batch</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 600px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 0px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f2f2f2; }
        p { color: red; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>List assembly batch</h2>
        <form method="POST" action="{{ url_for('list_batch') }}">
            <label>Please provide status:</label><br>
            <select name="filter" id="filter" required>
                <option value="0">Not started</option>
                <option value="1">Progress</option>
                <option value="2">Done</option>
            </select><br>
            <button type="submit">Search</button>
        </form>
        {% if error %}
            <p>{{ error }}</p>
        {% endif %}
        {% if results %}
            <table>
                <thead>
                    <tr>
                        <th>Received date</th>
                        <th>ID</th>
                        <th>Version</th>
                        <th>In ATLAS lab</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in results %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td><a href="{{ url_for('edit_batch',batch_id=row[1]) }}">{{ row[1] }}</a></td>
                            <td>{{ row[2] }}</td>
                            <td>{{ row[3] }}</td>
                            <td>{{ row[4] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        <br>
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

batch_update_template= """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Edit assembly batch: {{ batch.id }}</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 670px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="number"] { width: 95px; padding: 2px; margin: 3px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        a.button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        textarea { resize: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Edit assembly batch: {{ batch.id }}</h2>
        {% if error %}
            <p style="color:red;">{{ error }}</p>
        {% else %}
            {% if mess %}
                <p>{{ mess }}</p>
            {% endif %}
            <form method="post">
                <label>Received: {{ batch.received }}</label><br>
                <label>Received by: {{ batch.received_by }}</label><br>
                <label>Version: {{ batch.version }}</label><br><br>
                <table style="border: 1px solid black; padding: 5px"><tbody>
                <tr><td>In ATLAS lab</td>
                <td><select name="atlas_lab" id="atlas_lab" required>
                    <option value="0" {{ "selected" if batch.atlas_lab==0 else "" }}>No</option>
                    <option value="1" {{ "selected" if batch.atlas_lab==1 else "" }}>Yes</option>
                </select></td>
                <td width="5%"></td>
                <td>Comment</td><td style="vertical-align:top" rowspan="3">
                <textarea name="comment" cols="30" rows="3" placeholder="please leave a note"></textarea></td>
                </tr>

                <tr>
                <td>Status</td>
                <td><select name="status" id="status" required>
                    <option value="0" {{ "selected" if batch.status==0 else "" }}>Not started</option>
                    <option value="1" {{ "selected" if batch.status==1 else "" }}>Progress</option>
                    <option value="2" {{ "selected" if batch.status==2 else "" }}>Done</option>
                </select></td>
                </tr>

                <tr>
                <td><label>Quantity</label></td>
                <td><input type="number" name="quantity" value={{ batch.quantity }}></td>
                </tr>
                
                <tr>
                <td colspan="3"><a class=button href="{{ url_for('list_dboard',batch_id=batch.id) }}">List daughterboards</a></td>
                <td>Operator</td>
                <td><textarea name="op" rows="1" cols="30" placeholder="please provide your initials"></textarea></td>
                </tr>
                
                <tr>
                <td></td>
                <td></td>
                </tr>

                <tr>
                <td colspan="3"><a class=button href="{{ url_for('new_dboard',batch_id=batch.id) }}">Define daughterboard</a></td>
                <td>History</td>
                <td rowspan="3"><div>
                    <select name="comments" id="comments" style="width: 210px;">
                    {% for row in history %}
                        <option> {{ row.item }} </option>
                    {% endfor %}
                    </select>
                </div></td>
                </tr>

                </tbody></table>
                <button type="submit">Save</button>
            </form>
        {% endif %}
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

new_dboard_template= """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Define new daughterboard from batch {{ batch_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 670px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="number"] { width: 80%; padding: 2px; margin: 3px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        a.button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        textarea { resize: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Define new dautherboard from batch {{ batch_id }}</h2>
        {% if error %}
            <p style="color:red;">{{ error }}</p>
        {% else %}
            {% if mess %}
                <p>{{ mess }}</p>
            {% endif %}
            <form method="post">
                <table style="border: 1px solid black; padding: 5px"><tbody>

                <tr>
                <td width="180px"><label>Serialno:</label></td>
                <!--
                <td><label>Kintex A:</label></td>
                <td><label>Kintex B:</label></td>
                -->
                <td width="180px"></td>
                <td width="180px"></td>
                </tr>

                <tr>
                <td><input type="number" name="serial" value={{ dboard.serial }}></td>
                <!--
                <td><input type="text" name="kintex_a" value={{ dboard.kintex_a }}></td>
                <td><input type="text" name="kintex_b" value={{ dboard.kintex_b }}></td>
                -->
                </tr>

                <tr><td>KIN</td><td>PRO:</td><td>GBT:</td></tr>
                <tr>
                <td><select name="kin" id="kin">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['KIN'] %}<option {{"selected" if state[4]==row.item else ""}}>{{ row.item }}</option>{% endfor %}
                </select></td>
                <td><select name="pro" id="pro">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['PRO'] %}<option {{"selected" if state[5]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="gbt" id="gbt">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['GBT'] %}<option {{"selected" if state[6]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                </tr>

                <tr><td>INA</td><td>LTM:</td><td>MOS:</td></tr>
                <tr>
                <td><select name="ina" id="ina">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['INA'] %}<option {{"selected" if state[7]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="ltm" id="ltm">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['LTM'] %}<option {{"selected" if state[8]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="mos" id="mos">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['MOS'] %}<option {{"selected" if state[9]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                </tr>
                
                <tr><td>OP4</td><td>OK4:</td><td>OK1:</td></tr>
                <tr>
                <td><select name="op4" id="op4">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['OP4'] %}<option {{"selected" if state[10]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="ok4" id="ok4">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['OK4'] %}<option {{"selected" if state[11]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="ok1" id="ok1">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['OK1'] %}<option {{"selected" if state[12]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                </tr>

                <tr><td>MEM</td><td>SFP:</td></tr>
                <tr>
                <td><select name="mem" id="mem">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['MEM'] %}<option {{"selected" if state[13]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                <td><select name="sfp" id="sfp">
                    <option hidden value=''>Choose one</option>
                    {% for row in lot['SFP'] %}<option {{"selected" if state[14]==row.item else ""}}> {{ row.item }} </option>{% endfor %}
                </select></td>
                </tr>                

                </tbody></table>
                <button type="submit">Create new</button>
            </form>
        {% endif %}
        <a href="{{ url_for('edit_batch',batch_id=batch_id) }}">Return to Batch</a>
        <a href="{{ url_for('menu') }}"> or Menu</a>
    </div>
</body>
</html>
"""

# List daughterboard
list_dboard_template = """
<!DOCTYPE html>
<html>
<head>
    <title>List component lot</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 600px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 0px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f2f2f2; }
        p { color: red; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>List daughterboard for batch {{ batch_id }}</h2>
        {% if error %}
            <p>{{ error }}</p>
        {% endif %}
        {% if results %}
            <table>
                <thead>
                    <tr>
                        <th>Board serial#</th>
                        <th>Kintex A ID</th>
                        <th>Kintex B ID</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in results %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td>{{ row[2] }}</td>
                            <td>{{ row[3] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        <br>
        <a href="{{ url_for('edit_batch',batch_id=batch_id) }}">Return to Batch</a>
        <a href="{{ url_for('menu') }}"> or Menu</a>
    </div>
</body>
</html>
"""

new_test_template= """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Define new daughterboard from batch {{ batch_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 550px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="number"] { width: 80%; padding: 2px; margin: 3px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }

        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        a.button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        textarea { resize: none; }
    </style>
</head>
<body>
    <div class="container">
        {% if bench %}
            <h2>Stop bench test</h2>
        {% else %}
            <h2>Start bench test</h2>
        {% endif %}
        {% if error %}
            <p style="color:red;">{{ error }}</p>
        {% else %}
            {% if mess %}
                <p>{{ mess }}</p>
            {% endif %}
            <form method="post">
                <table style="border: 1px solid black; padding: 5px"><tbody>
                {% if bench %}
                <tr>
                <td><label>Test started (UTC)</label></td>
                </tr>
                <tr>
                <td><input type="text" name="test_start" value="{{ bench.test_start.strftime('%Y-%m-%d %H:%M:%S') }}" disabled></td>
                </tr>
                {% endif %}
                <tr>
                <td><label>Operator</label></td>
                {% if bench %}
                <td><label>Test pass</label></td>
                {% endif %}
                </tr>
                <tr>
                <td><input type="text" name="test_op" value="{{ bench.test_op }}" placeholder="please provide your initials"></td>
                {% if bench %}
                <td><select name="test_pass" id="test_pass" required>
                    <option value="0" {{ "selected" if bench.test_pass==0 else "" }}>No</option>
                    <option value="1" {{ "selected" if bench.test_pass==1 else "" }}>Yes</option>
                </select></td>
                {% endif %}
                </tr><td>Comment</td></tr>
                <tr>
                <td><textarea name="comment" cols="30" rows="3" placeholder="please leave a note"></textarea></td>
                </tr>
                <tr><td>&nbsp;</td></tr>
                <tr>
                <td><label>Board serial# MD 1</label></td>
                <td><label>Board serial# MD 2</label></td>
                </tr>
                <tr>
                <td><input type="number" name="db_slot1" value="{{ bench.db_slot1 }}" {% if bench %} disabled {% endif %}></td>
                <td><input type="number" name="db_slot2" value="{{ bench.db_slot2 }}" {% if bench %} disabled {% endif %}></td>
                </tr>
                <tr>
                <td><label>Board serial# MD 3</label></td>
                <td><label>Board serial# MD 4</label></td>
                </tr>
                <tr>
                <td><input type="number" name="db_slot3" value="{{ bench.db_slot3 }}" {% if bench %} disabled {% endif %}></td>
                <td><input type="number" name="db_slot4" value="{{ bench.db_slot4 }}" {% if bench %} disabled {% endif %}></td>
                </tr>

                </tbody></table>
                {% if bench %}
                    <input id="stop-submit" type="submit" name="submit" value="Stop">
                    <input type="hidden" name="bench_id" value={{ bench.id }}>
                {% else %}
                    <input id="start-submit" type="submit" name="submit" value="Start">
                {% endif %}
            </form>
        {% endif %}
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

# List bench test 
list_bench_template = """
<!DOCTYPE html>
<html>
<head>
    <title>List bench test</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 800px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 0px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f2f2f2; }
        p { color: red; }
        select {width: 100%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>List last 100 passed bench tests</h2>
        {% if error %}
            <p>{{ error }}</p>
        {% endif %}
        {% if results %}
            <table>
                <thead>
                    <tr>
                        <th>Test start (UTC)</th>
                        <th>Test stop (UTC)</th>
                        <th>OP</th>
                        <th>db_slot1</th>
                        <th>db_slot2</th>
                        <th>db_slot3</th>
                        <th>db_slot4</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in results %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td>{{ row[2] }}</td>
                            <td>{{ row[3] }}</td>
                            <td>{{ row[4] }}</td>
                            <td>{{ row[5] }}</td>
                            <td>{{ row[6] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        <br>
        <a href="{{ url_for('menu') }}"> Return to Menu</a>
    </div>
</body>
</html>
"""

def_kintex_template= """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Define kintex ID</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { width: 550px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 8px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="number"] { width: 80%; padding: 2px; margin: 3px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #45a049; }
        a { text-decoration: none; color: #4CAF50; display: inline-block; margin-top: 10px; }
        p { color: green; }
        a.button { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        textarea { resize: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Define kintex ID</h2>
        {% if error %}
            <p style="color:red;">{{ error }}</p>
        {% else %}
            {% if mess %}
                <p>{{ mess }}</p>
            {% endif %}
            <form method="post">
                <table style="border: 1px solid black;  padding: 5px"><tbody>
                <tr>
                <td><label>Board serial#</label></td>
                <td><label>Kintex A ID</label></td>
                <td><label>Kintex B ID</label></td>
                </tr>
                <tr>
                <td><input type="number" name="id"></td>
                <td><input type="text" name="kintex_a"></td>
                <td><input type="text" name="kintex_b"></td>
                </tr>
                </tbody></table>
                <button type="submit">Save</button>
            </form>
        {% endif %}
        <a href="{{ url_for('menu') }}">Return to Menu</a>
    </div>
</body>
</html>
"""

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
            return render_template_string(login_template)
    return render_template_string(login_template)

# Menu Route
@app.route('/menu')
def menu():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(menu_template)

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
            return render_template_string(new_lot_template, message=message)
        
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
    return render_template_string(new_lot_template, message=message)

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
            return render_template_string(new_batch_template, message=message)
        
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
    return render_template_string(new_batch_template, message=message)

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
                        return render_template_string(list_lot_template, error=error)
                except Error as e:
                    error = "Error executing query: " + str(e)
                finally:
                    cursor.close()
                    conn.close()
            else:
                error = "Database connection error."
    return render_template_string(list_lot_template, error=error, results=results)

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
                    return render_template_string(lot_update_template, error=error)
                query = "SELECT concat(tstamp,' (UTC), ',op,': ',note) as item FROM comment WHERE foreign_typ=1 and foreign_id=%s"
                cursor.execute(query, (lot['id'],))
                history = cursor.fetchall()
            except Error as e:
                error = "Error looking up lot: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template_string(lot_update_template, mess=mess, error=error,
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
                        return render_template_string(list_assembly_template, error=error)
                except Error as e:
                    error = "Error executing query: " + str(e)
                finally:
                    cursor.close()
                    conn.close()
            else:
                error = "Database connection error."
    return render_template_string(list_assembly_template, error=error, results=results)

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
                    return render_template_string(batch_update_template, error=error)
                query = "SELECT concat(tstamp,' (UTC), ',op,': ',note) as item FROM comment WHERE foreign_typ=2 and foreign_id=%s"
                cursor.execute(query, (batch['id'],))
                history = cursor.fetchall()
            except Error as e:
                error = "Error looking up assembly batch: " + str(e)
            finally:
                cursor.close()
                conn.close()

    return render_template_string(batch_update_template, mess=mess, error=error,
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

    return render_template_string(new_dboard_template, mess=mess, error=error,state=state,
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
                return render_template_string(list_dboard_template, error=error,
                                              batch_id=batch_id)
        except Error as e:
            error = "Error executing query: " + str(e)
        finally:
            cursor.close()
            conn.close()
    else:
        error = "Database connection error."
    return render_template_string(list_dboard_template, error=error, results=results,
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
                return render_template_string(list_bench_template, error=error)
        except Error as e:
            error = "Error executing query: " + str(e)
        finally:
            cursor.close()
            conn.close()
    else:
        error = "Database connection error."
    return render_template_string(list_bench_template, error=error, results=results)

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

    return render_template_string(new_test_template, mess=mess, error=error, bench=bench)

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

    return render_template_string(def_kintex_template, mess=mess, error=error)

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
