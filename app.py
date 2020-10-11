from flask import Flask, render_template, redirect, url_for, jsonify, session, request
from itsdangerous import URLSafeTimedSerializer, BadData, SignatureExpired
import requests, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'

sToken = URLSafeTimedSerializer('thisissecret')

# Custom Function


def islogin():
    if "islogin" in session:
        return True

def isadmin():
    if islogin():
        if 'admin' in session:
            return True

def isnormal():
    if islogin():
        if 'regular' in session:
            return True

# API URL
url_menu = "https://seghoku-api.herokuapp.com/api/menu/"
url_tenant = "https://seghoku-api.herokuapp.com/api/tenant/"
url_location = "https://seghoku-api.herokuapp.com/api/locations/"
url_auth = "https://seghoku-api.herokuapp.com/api/auth/"
url_user = "https://seghoku-api.herokuapp.com/api/users/"
url_level_user = "https://seghoku-api.herokuapp.com/api/level_user/"



@app.route('/')
def index():
    data_menu = []

    # request menu
    req_menu = requests.get(url_menu)
    req_menu = req_menu.json()['data']

    # Shuffle data
    req_menu = random.sample(req_menu,len(req_menu))

    for i in req_menu:
        data = {}
        data['id'] = sToken.dumps(i['id'], salt="id_menu"),
        data['nama_menu'] = i['nama_menu']
        data['harga_menu'] = i['harga_menu']
        data['foto_menu'] = i['foto_menu']

        # get tenant
        tenant = {}
        tenant['id'] = sToken.dumps(i["tenant"]['id'], salt="id_tenant")
        tenant['nama_toko'] = i["tenant"]['nama_toko']
        tenant['no_hp'] = i["tenant"]['no_hp']

        # get location
        location = {}
        location['id'] = sToken.dumps(i["tenant"]["location"]['id'], salt="id_location")
        location['nama_location'] = i["tenant"]["location"]['nama_location']

        tenant['location'] = location
        data['tenant'] = tenant

        data_menu.append(data)
    # return jsonify(data_menu)
    return render_template("index.html", data_menu=data_menu)


@app.route('/area/<place>')
def area(place):
    try:
        tempat = sToken.loads(place, salt="id_location", max_age=3600)
        data_menu = []

        # request menu
        req_menu = requests.get(url_menu, params={"id_location":tempat})
        req_menu = req_menu.json()['data']

        # Shuffle data
        req_menu = random.sample(req_menu,len(req_menu))
        for i in req_menu:
            data = {}
            data['id'] = sToken.dumps(i['id'], salt="id_menu"),
            data['nama_menu'] = i['nama_menu']
            data['harga_menu'] = i['harga_menu']
            data['foto_menu'] = i['foto_menu']

            # get tenant
            tenant = {}
            tenant['id'] = sToken.dumps(i["tenant"]['id'], salt="id_tenant")
            tenant['nama_toko'] = i["tenant"]['nama_toko']
            tenant['no_hp'] = i["tenant"]['no_hp']

            # get location
            location = {}
            location['id'] = sToken.dumps(i["tenant"]["location"]['id'], salt="id_location")
            location['nama_location'] = i["tenant"]["location"]['nama_location']

            # set place
            place = i["tenant"]["location"]['nama_location']

            tenant['location'] = location
            data['tenant'] = tenant

            data_menu.append(data)
        return render_template("area.html", data_menu=data_menu, place=place)
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))

@app.route('/mitra/<id_tenant>')
def mitra(id_tenant):
    try:
        id_tenant = sToken.loads(id_tenant, salt="id_tenant", max_age=3600)

        data_menu = []

        # get tenant
        req_tenant = requests.get(url_menu, params={'id_tenant': id_tenant})
        req_tenant = req_tenant.json()
        if req_tenant['status'] == "error":
            return redirect(url_for('index'))
        else:
            req_tenant = req_tenant['data']
            tenant = {
                "id":sToken.dumps(req_tenant['id'],salt="id_tenant"),
                "nama_toko":req_tenant['nama_toko'],
                "no_hp": req_tenant['no_hp'],
                "location":{
                    "id":sToken.dumps(req_tenant['location']['id'], salt='id_location'),
                    "nama_location":req_tenant['location']['nama_location']
                }
            }
            for j in req_tenant['menu']:
                data = {}
                data['tenant'] = tenant
                data['id'] = sToken.dumps(j['id'], salt="id_menu"),
                data['nama_menu'] = j['nama_menu']
                data['harga_menu'] = j['harga_menu']
                data['foto_menu'] = j['foto_menu']
                data_menu.append(data)
            return render_template("mitra.html", data_menu=data_menu, mitra=req_tenant['nama_toko'])
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == 'GET':
            return render_template('login.html')
        else:
            email = request.form['email']
            password = request.form['password']

            json = {
                "email":email,
                "password":password
            }

            req = requests.post(url_auth, json=json)

            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    session['islogin'] = True,
                    session['id_user'] = True,
                    session['nama_user'] = res['data']['nama']

                    id_level = res['data']['id_level']

                    req_level_user = requests.get(url_level_user,params={"id_level":id_level})
                    nama_level = req_level_user.json()['data']['nama_level']

                    if nama_level == 'Admin':
                        session['admin'] = True
                    if nama_level == 'Regular':
                        session['regular'] = True

                    return redirect(url_for('index'))
                return redirect(url_user("login"))
            return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == "GET":
            return render_template("register.html")
        else:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            json = {
                'id_level':"5f48d40db863173baa5be801",
                'nama': name,
                'email': email,
                "password": password
            }

            req = requests.post(url_user, json=json)
            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    return redirect(url_for('login'))
                else:
                    return redirect(url_for('register'))
            else:
                return redirect(url_for('register'))

@app.route('/join-partner', methods=['GET', 'POST'])
def joinparter():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == "GET":
            return render_template("registerpartner.html")
        else:
            name = request.form['namepartner']
            email = request.form['emailpartner']
            password = request.form['passwordpartner']

            json = {
                'id_level':"5f48b92ca69c2f203b82b533",
                'nama': name,
                'email': email,
                "password": password
            }

            req = requests.post(url_user, json=json)
            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    return redirect(url_for('login'))
                else:
                    return redirect(url_for('joinparter'))
            else:
                return redirect(url_for('joinparter'))


@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
