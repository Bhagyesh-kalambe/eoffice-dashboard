from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import pandas as pd
import os
import math
from flask import session
from flask import jsonify, request
import os
import pandas as pd


BASE_DIR = os.path.join(os.getcwd(), "data")
DATA_DIR = BASE_DIR  

app = Flask(__name__)

# ---------------- CONFIG ----------------

app.config['SECRET_KEY'] = 'eoffice_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# ---------------- DATABASE MODEL ----------------

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)

    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)


# ---------------- CREATE DB ----------------

with app.app_context():
    db.create_all()

#----------try---------------
# ================= DATA LOADER =================

# ================= DATA LOADER =================

def load_kpi_data():

    base_path = os.path.join(os.getcwd(), "data")

    # Read CSVs
    created_df = pd.read_csv(os.path.join(base_path, "filecreated.csv"))
    not_moved_df = pd.read_csv(os.path.join(base_path, "filecreatednotmoved.csv"))
    pending_df = pd.read_csv(os.path.join(base_path, "filepending.csv"))
    closed_df = pd.read_csv(os.path.join(base_path, "file_closed.csv"))
    active_df = pd.read_csv(os.path.join(base_path, "Total_Active_Users.csv"))


    # Convert numeric columns
    for df in [created_df, not_moved_df, pending_df, closed_df]:

        df['ElectronicFile'] = pd.to_numeric(df['ElectronicFile'], errors='coerce').fillna(0)
        df['PhysicalFile'] = pd.to_numeric(df['PhysicalFile'], errors='coerce').fillna(0)
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)


    # ---------------- CREATED ----------------

    created_total = int(created_df['Total'].sum())
    created_elec = int(created_df['ElectronicFile'].sum())
    created_phy = int(created_df['PhysicalFile'].sum())


    # ---------------- NOT MOVED ----------------

    not_moved_total = int(not_moved_df['Total'].sum())
    not_moved_elec = int(not_moved_df['ElectronicFile'].sum())
    not_moved_phy = int(not_moved_df['PhysicalFile'].sum())


    # ---------------- MOVED ----------------

    moved_total = created_total - not_moved_total
    moved_elec = created_elec - not_moved_elec
    moved_phy = created_phy - not_moved_phy


    # ---------------- PENDING ----------------

    pending_total = int(pending_df['Total'].sum())
    pending_elec = int(pending_df['ElectronicFile'].sum())
    pending_phy = int(pending_df['PhysicalFile'].sum())


    # ---------------- CLOSED ----------------

    closed_total = int(closed_df['Total'].sum())
    closed_elec = int(closed_df['ElectronicFile'].sum())
    closed_phy = int(closed_df['PhysicalFile'].sum())


    # ---------------- ACTIVE USERS ----------------
    active_df.columns = active_df.columns.str.strip()
    # Standardize active user calculation
    if "Active Users" in active_df.columns:
        active_users = int(active_df["Active Users"].sum())
    else:
        active_users = 0


    # ---------------- PERCENTAGES ----------------

    def calc_percent(part, total):
        if total == 0:
            return 0
        return round((part / total) * 100, 1)


    not_moved_percent = calc_percent(not_moved_total, created_total)
    pending_percent = calc_percent(pending_total, created_total)
    closed_percent = calc_percent(closed_total, created_total)


    # ---------------- RETURN ----------------

    return {

        "created": {
            "total": created_total,
            "electronic": created_elec,
            "physical": created_phy
        },

        "not_moved": {
    "total": not_moved_total,
    "electronic": not_moved_elec,
    "physical": not_moved_phy,
    "remaining": created_total - not_moved_total,
    "percent": not_moved_percent
},



        "moved": {
            "total": moved_total,
            "electronic": moved_elec,
            "physical": moved_phy
        },

        "pending": {
    "total": pending_total,
    "electronic": pending_elec,
    "physical": pending_phy,
    "remaining": created_total - pending_total,
    "percent": pending_percent
},



        "closed": {
    "total": closed_total,
    "electronic": closed_elec,
    "physical": closed_phy,
    "remaining": created_total - closed_total,
    "percent": closed_percent
},



        "active_users": active_users
    }

# ================= LOAD DEPARTMENTS =================

# ================= LOAD DEPARTMENTS =================

def load_departments():

    path = os.path.join(os.getcwd(), "data", "deptname_unique.csv")

    df = pd.read_csv(path)

    # If column name is DepartmentName
    if "DepartmentName" in df.columns:
        departments = df["DepartmentName"].dropna().tolist()
    else:
        # Take first column if name differs
        departments = df.iloc[:, 0].dropna().tolist()

    return sorted(departments)

def load_organizations():

    file_path = os.path.join("data", "filecreated.csv")

    df = pd.read_csv(file_path)

    # Get unique organization names
    orgs = df["OrgName"].dropna().unique().tolist()

    return sorted(orgs)


# ================= LOAD DETAIL TABLE =================

def load_detail_table():

    base = os.path.join(os.getcwd(), "data")

    # Load CSVs
    created = pd.read_csv(os.path.join(base, "filecreated.csv"))
    not_moved = pd.read_csv(os.path.join(base, "filecreatednotmoved.csv"))
    pending = pd.read_csv(os.path.join(base, "filepending.csv"))
    closed = pd.read_csv(os.path.join(base, "file_closed.csv"))


    # Select required columns
    cols = ["DepartmentName", "OrgName", "Total"]

    created = created[cols]
    not_moved = not_moved[cols]
    pending = pending[cols]
    closed = closed[cols]


    # Rename totals
    created = created.rename(columns={"Total": "created"})
    not_moved = not_moved.rename(columns={"Total": "not_moved"})
    pending = pending.rename(columns={"Total": "pending"})
    closed = closed.rename(columns={"Total": "closed"})


    # Group by Department + Org
    created = created.groupby(
        ["DepartmentName", "OrgName"], as_index=False
    ).sum()

    not_moved = not_moved.groupby(
        ["DepartmentName", "OrgName"], as_index=False
    ).sum()

    pending = pending.groupby(
        ["DepartmentName", "OrgName"], as_index=False
    ).sum()

    closed = closed.groupby(
        ["DepartmentName", "OrgName"], as_index=False
    ).sum()


    # Merge All
    df = created.merge(
        not_moved,
        on=["DepartmentName", "OrgName"],
        how="left"
    )

    df = df.merge(
        pending,
        on=["DepartmentName", "OrgName"],
        how="left"
    )

    df = df.merge(
        closed,
        on=["DepartmentName", "OrgName"],
        how="left"
    )


    # Fill NaN with 0
    df = df.fillna(0)


    # Convert to int
    for col in ["created", "not_moved", "pending", "closed"]:
        df[col] = df[col].astype(int)


    # ---------------- CALCULATIONS ----------------

    df["moved"] = df["created"] - df["not_moved"]


    def percent(a, b):
        if b == 0:
            return 0
        return round((a / b) * 100, 2)


    df["moved_pct"] = df.apply(
        lambda x: percent(x["moved"], x["created"]), axis=1
    )

    df["not_moved_pct"] = df.apply(
        lambda x: percent(x["not_moved"], x["created"]), axis=1
    )

    df["pending_pct"] = df.apply(
        lambda x: percent(x["pending"], x["created"]), axis=1
    )

    df["closed_pct"] = df.apply(
        lambda x: percent(x["closed"], x["created"]), axis=1
    )


    # ---------------- TOTAL ROW ----------------

    total = {

        "DepartmentName": "Total",
        "OrgName": "",

        "created": df["created"].sum(),
        "moved": df["moved"].sum(),
        "moved_pct": percent(
            df["moved"].sum(), df["created"].sum()
        ),

        "not_moved": df["not_moved"].sum(),
        "not_moved_pct": percent(
            df["not_moved"].sum(), df["created"].sum()
        ),

        "pending": df["pending"].sum(),
        "pending_pct": percent(
            df["pending"].sum(), df["created"].sum()
        ),

        "closed": df["closed"].sum(),
        "closed_pct": percent(
            df["closed"].sum(), df["created"].sum()
        ),
    }


    # Convert to list of dicts
    rows = df.to_dict(orient="records")

    rows.append(total)

    return rows

def get_last_refresh_time():

    path = os.path.join(DATA_DIR, "last_refresh.csv")

    try:
        df = pd.read_csv(path)

        if "last_refreshed" in df.columns:
            return df["last_refreshed"].iloc[0]

    except:
        pass

    return "Not Available"

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')


# ---------- SIGNUP ----------

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        full_name = request.form['full_name']
        department = request.form['department']

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check duplicate username
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists!", "danger")
            return redirect('/signup')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            full_name=full_name,
            department=department,
            username=username,
            email=email,
            password=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please Login", "success")

        return redirect('/login')

    return render_template('signup.html')


# ---------- LOGIN ----------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['username'] = user.username

            return redirect('/dashboard')

        else:
            flash("Invalid Username or Password!", "danger")

    return render_template('login.html')


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    kpi_data = load_kpi_data()
    departments = load_departments()
    organizations = load_organizations()

    table_data = load_detail_table()

    last_refresh = get_last_refresh_time()

    return render_template(
    'dashboard.html',
    data=kpi_data,
    departments=departments,
    organizations=organizations,
    table_data=table_data,
    last_refresh=last_refresh
)


@app.route("/api/filter/department", methods=["POST"])
def filter_by_department():

    data = request.get_json()
    departments = data.get("departments", [])

    # Load CSVs
    created = pd.read_csv(os.path.join(DATA_DIR,"filecreated.csv"))
    not_moved = pd.read_csv(os.path.join(DATA_DIR,"filecreatednotmoved.csv"))
    pending = pd.read_csv(os.path.join(DATA_DIR,"filepending.csv"))
    closed = pd.read_csv(os.path.join(DATA_DIR,"file_closed.csv"))

    # If department selected → filter
    if departments:

        created = created[created["DepartmentName"].isin(departments)]
        not_moved = not_moved[not_moved["DepartmentName"].isin(departments)]
        pending = pending[pending["DepartmentName"].isin(departments)]
        closed = closed[closed["DepartmentName"].isin(departments)]


    # Calculation function
    def calc(df):

        ele = df["ElectronicFile"].sum()
        phy = df["PhysicalFile"].sum()
        total = ele + phy

        return int(ele), int(phy), int(total)


    # Calculate all
    c_ele, c_phy, c_total = calc(created)
    nm_ele, nm_phy, nm_total = calc(not_moved)
    p_ele, p_phy, p_total = calc(pending)
    cl_ele, cl_phy, cl_total = calc(closed)


    # Moved = Created - Not Moved
    m_ele = c_ele - nm_ele
    m_phy = c_phy - nm_phy
    m_total = c_total - nm_total

    p_ele, p_phy, p_total = calc(pending)
    cl_ele, cl_phy, cl_total = calc(closed)

    # Total base (created)
    base = c_total if c_total != 0 else 1

    nm_pct = round((nm_total / base) * 100, 1)
    p_pct = round((p_total / base) * 100, 1)
    cl_pct = round((cl_total / base) * 100, 1)
    # ================= ACTIVE USERS =================

    users = pd.read_csv(os.path.join(DATA_DIR,"Total_Active_Users.csv"))

# Filter by department
    if departments:
        users = users[users["DepartmentName"].isin(departments)]

    active_users = int(users["Active Users"].sum())



    result = {

    "created": {
        "electronic": c_ele,
        "physical": c_phy,
        "total": c_total
    },

    "not_moved": {
        "electronic": nm_ele,
        "physical": nm_phy,
        "total": nm_total,
        "percent": nm_pct,
        "remaining": base - nm_total
    },

    "moved": {
        "electronic": m_ele,
        "physical": m_phy,
        "total": m_total
    },

    "pending": {
        "electronic": p_ele,
        "physical": p_phy,
        "total": p_total,
        "percent": p_pct,
        "remaining": base - p_total
    },

    "closed": {
        "electronic": cl_ele,
        "physical": cl_phy,
        "total": cl_total,
        "percent": cl_pct,
        "remaining": base - cl_total
    },

    "active_users": active_users



}



    return jsonify(result)

@app.route("/api/filter/table", methods=["POST"])
def filter_table():

    data = request.get_json()
    departments = data.get("departments", [])


    base = os.path.join(os.getcwd(), "data")

    # Load CSVs
    created = pd.read_csv(os.path.join(base, "filecreated.csv"))
    not_moved = pd.read_csv(os.path.join(base, "filecreatednotmoved.csv"))
    pending = pd.read_csv(os.path.join(base, "filepending.csv"))
    closed = pd.read_csv(os.path.join(base, "file_closed.csv"))


    # Filter
    if departments:

        created = created[created["DepartmentName"].isin(departments)]
        not_moved = not_moved[not_moved["DepartmentName"].isin(departments)]
        pending = pending[pending["DepartmentName"].isin(departments)]
        closed = closed[closed["DepartmentName"].isin(departments)]


    # Select columns
    cols = ["DepartmentName", "OrgName", "Total"]

    created = created[cols]
    not_moved = not_moved[cols]
    pending = pending[cols]
    closed = closed[cols]


    # Rename
    created = created.rename(columns={"Total": "created"})
    not_moved = not_moved.rename(columns={"Total": "not_moved"})
    pending = pending.rename(columns={"Total": "pending"})
    closed = closed.rename(columns={"Total": "closed"})


    # Group
    created = created.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    not_moved = not_moved.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    pending = pending.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    closed = closed.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()


    # Merge
    df = created.merge(
        not_moved,
        on=["DepartmentName","OrgName"],
        how="left"
    )

    df = df.merge(
        pending,
        on=["DepartmentName","OrgName"],
        how="left"
    )

    df = df.merge(
        closed,
        on=["DepartmentName","OrgName"],
        how="left"
    )


    df = df.fillna(0)


    # Int
    for c in ["created","not_moved","pending","closed"]:
        df[c] = df[c].astype(int)


    # Moved
    df["moved"] = df["created"] - df["not_moved"]


    # Percent
    def pct(a,b):
        return round((a/b)*100,2) if b else 0


    df["moved_pct"] = df.apply(
        lambda x: pct(x["moved"],x["created"]), axis=1
    )

    df["not_moved_pct"] = df.apply(
        lambda x: pct(x["not_moved"],x["created"]), axis=1
    )

    df["pending_pct"] = df.apply(
        lambda x: pct(x["pending"],x["created"]), axis=1
    )

    df["closed_pct"] = df.apply(
        lambda x: pct(x["closed"],x["created"]), axis=1
    )


    # Total row
    total = {

        "DepartmentName":"Total",
        "OrgName":"",

        "created":int(df["created"].sum()),
        "moved":int(df["moved"].sum()),
        "moved_pct":pct(df["moved"].sum(),df["created"].sum()),

        "not_moved":int(df["not_moved"].sum()),
        "not_moved_pct":pct(df["not_moved"].sum(),df["created"].sum()),

        "pending":int(df["pending"].sum()),
        "pending_pct":pct(df["pending"].sum(),df["created"].sum()),

        "closed":int(df["closed"].sum()),
        "closed_pct":pct(df["closed"].sum(),df["created"].sum())
    }


    rows = df.to_dict(orient="records")
    rows.append(total)

    return jsonify(rows)

@app.route("/api/filter/table-by-org", methods=["POST"])
def filter_table_by_org():

    data = request.get_json()
    org = data.get("organization")


    base = os.path.join(os.getcwd(), "data")

    # Load CSVs
    created = pd.read_csv(os.path.join(base, "filecreated.csv"))
    not_moved = pd.read_csv(os.path.join(base, "filecreatednotmoved.csv"))
    pending = pd.read_csv(os.path.join(base, "filepending.csv"))
    closed = pd.read_csv(os.path.join(base, "file_closed.csv"))


    # ================= FILTER BY ORGANIZATION =================

    if org:

        created = created[created["OrgName"] == org]
        not_moved = not_moved[not_moved["OrgName"] == org]
        pending = pending[pending["OrgName"] == org]
        closed = closed[closed["OrgName"] == org]


    # Select columns
    cols = ["DepartmentName", "OrgName", "Total"]

    created = created[cols]
    not_moved = not_moved[cols]
    pending = pending[cols]
    closed = closed[cols]


    # Rename
    created = created.rename(columns={"Total": "created"})
    not_moved = not_moved.rename(columns={"Total": "not_moved"})
    pending = pending.rename(columns={"Total": "pending"})
    closed = closed.rename(columns={"Total": "closed"})


    # Group
    created = created.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    not_moved = not_moved.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    pending = pending.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()

    closed = closed.groupby(
        ["DepartmentName","OrgName"], as_index=False
    ).sum()


    # Merge
    df = created.merge(
        not_moved,
        on=["DepartmentName","OrgName"],
        how="left"
    )

    df = df.merge(
        pending,
        on=["DepartmentName","OrgName"],
        how="left"
    )

    df = df.merge(
        closed,
        on=["DepartmentName","OrgName"],
        how="left"
    )


    df = df.fillna(0)


    # Int
    for c in ["created","not_moved","pending","closed"]:
        df[c] = df[c].astype(int)


    # Moved
    df["moved"] = df["created"] - df["not_moved"]


    # Percent
    def pct(a,b):
        return round((a/b)*100,2) if b else 0


    df["moved_pct"] = df.apply(
        lambda x: pct(x["moved"],x["created"]), axis=1
    )

    df["not_moved_pct"] = df.apply(
        lambda x: pct(x["not_moved"],x["created"]), axis=1
    )

    df["pending_pct"] = df.apply(
        lambda x: pct(x["pending"],x["created"]), axis=1
    )

    df["closed_pct"] = df.apply(
        lambda x: pct(x["closed"],x["created"]), axis=1
    )


    # NO TOTAL ROW for org filter (optional)
    rows = df.to_dict(orient="records")

    return jsonify(rows)

@app.route("/api/filter/org-by-dept", methods=["POST"])
def org_by_department():

    data = request.get_json()
    departments = data.get("departments", [])

    df = pd.read_csv(os.path.join(DATA_DIR, "filecreated.csv"))

    # If departments selected → filter
    if departments:
        df = df[df["DepartmentName"].isin(departments)]

    # Get unique orgs
    orgs = sorted(df["OrgName"].dropna().unique().tolist())

    return jsonify(orgs)



# ---------- LOGOUT ----------

@app.route('/logout')
def logout():

    session.clear()
    return redirect('/login')


# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)
