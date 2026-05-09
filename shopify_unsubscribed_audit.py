from flask import Flask, request, render_template_string, send_file
import pandas as pd
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
REPORT_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

HTML = """
<!doctype html>
<html>
<head>
<title>Shopify Unsubscribe Audit</title>
<style>
body{font-family:Arial;background:#f5f5f5;padding:30px}
.box{background:white;padding:25px;border-radius:12px;max-width:1450px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px;margin:20px 0}
.card{background:#eef2ff;padding:16px;border-radius:10px}
.card strong{display:block;font-size:28px;margin-top:6px}
.bad{background:#fee2e2}.good{background:#dcfce7}.warn{background:#fff3cd}
button,.btn{background:#111;color:white;border:0;border-radius:8px;padding:12px 18px;margin:5px;text-decoration:none;display:inline-block;cursor:pointer}
input{width:100%;padding:10px;margin:10px 0 20px;border:1px solid #ccc;border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #ddd;padding:8px;text-align:left;white-space:nowrap}
th{background:#eee;position:sticky;top:0}
.wrap{overflow:auto;max-height:650px;border:1px solid #ddd;border-radius:10px;margin-bottom:30px}
.notice{background:#fff3cd;padding:15px;border-radius:10px;margin:15px 0}
</style>

<script>
function filterTable(inputId, tableId, countId){
    let input=document.getElementById(inputId).value.toLowerCase();
    let table=document.getElementById(tableId);
    let rows=table.getElementsByTagName("tr");
    let visible=0;

    for(let i=1;i<rows.length;i++){
        let text=rows[i].innerText.toLowerCase();
        if(text.includes(input)){
            rows[i].style.display="";
            visible++;
        } else {
            rows[i].style.display="none";
        }
    }
    document.getElementById(countId).innerText=visible;
}
</script>
</head>

<body>
<div class="box">
<h1>Shopify Unsubscribe Audit</h1>

<div class="notice">
Upload two Shopify CSV exports:
<br><br>
<b>1.</b> OLD file: customers who were subscribed before
<br>
<b>2.</b> CURRENT file: latest Shopify customers export
<br><br>
The tool will find customers who were subscribed before but are now unsubscribed/not subscribed.
</div>

{% if not result %}
<form method="POST" enctype="multipart/form-data">
<h3>Upload OLD Shopify subscribed CSV</h3>
<input type="file" name="old_file" required>

<h3>Upload CURRENT Shopify customers CSV</h3>
<input type="file" name="current_file" required>

<button type="submit">Find Unsubscribed Customers</button>
</form>
{% else %}

<h2>Summary</h2>

<div class="grid">
<div class="card good">Old subscribed customers<strong>{{ result.old_subscribed }}</strong></div>
<div class="card">Current customers<strong>{{ result.current_total }}</strong></div>
<div class="card good">Still subscribed<strong>{{ result.still_subscribed }}</strong></div>
<div class="card bad">Now unsubscribed / not subscribed<strong>{{ result.now_unsubscribed }}</strong></div>
<div class="card warn">Missing in current file<strong>{{ result.missing_current }}</strong></div>
</div>

<h2>Downloads</h2>
<a class="btn" href="/download/{{ job_id }}/now_unsubscribed.csv">Download Now Unsubscribed</a>
<a class="btn" href="/download/{{ job_id }}/still_subscribed.csv">Download Still Subscribed</a>
<a class="btn" href="/download/{{ job_id }}/missing_in_current.csv">Download Missing In Current</a>
<a class="btn" href="/download/{{ job_id }}/full_comparison.csv">Download Full Comparison</a>
<a class="btn" href="/">Analyze Again</a>

<h2>1. Customers subscribed before but NOW unsubscribed / not subscribed</h2>
<p>Total shown: <b id="count_unsub">{{ result.now_unsubscribed }}</b></p>
<input id="search_unsub" onkeyup="filterTable('search_unsub','table_unsub','count_unsub')" placeholder="Search email/name...">
<div class="wrap">{{ unsubscribed_table|safe }}</div>

<h2>2. Customers still subscribed</h2>
<p>Total shown: <b id="count_still">{{ result.still_subscribed }}</b></p>
<input id="search_still" onkeyup="filterTable('search_still','table_still','count_still')" placeholder="Search email/name...">
<div class="wrap">{{ still_table|safe }}</div>

<h2>3. Customers missing in current file</h2>
<p>Total shown: <b id="count_missing">{{ result.missing_current }}</b></p>
<input id="search_missing" onkeyup="filterTable('search_missing','table_missing','count_missing')" placeholder="Search email/name...">
<div class="wrap">{{ missing_table|safe }}</div>

{% endif %}
</div>
</body>
</html>
"""


def read_csv_auto(path):
    for sep in [",", ";", "\t", "|"]:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                encoding="utf-8-sig",
                engine="python",
                on_bad_lines="skip"
            )
            if len(df.columns) > 1:
                return df
        except Exception:
            pass

    raise Exception("Could not read CSV. Please check delimiter/format.")


def norm_cols(df):
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace("\ufeff", "").replace("_", " ")
        for c in df.columns
    ]
    return df


def norm_email(value):
    if pd.isna(value):
        return None

    email = str(value).strip().lower()

    if email.startswith("'"):
        email = email[1:]

    return email if "@" in email else None


def is_subscribed(value):
    if pd.isna(value):
        return False

    v = str(value).strip().lower()

    return v in [
        "yes",
        "true",
        "1",
        "subscribed",
        "opted_in",
        "opted in",
        "active"
    ]


def find_subscription_col(df):
    candidates = [
        "email subscription status",
        "email_subscription_status",
        "accepts email marketing",
        "accepts_email_marketing",
        "accepts marketing",
        "marketing status",
        "subscribed"
    ]

    normalized_columns = {c: c for c in df.columns}

    for candidate in candidates:
        candidate_norm = candidate.lower().replace("_", " ")
        if candidate_norm in normalized_columns:
            return normalized_columns[candidate_norm]

    return None


def make_table(df, table_id):
    if df.empty:
        return f'<table id="{table_id}"><tr><th>No rows found</th></tr></table>'

    html = df.fillna("").head(30000).to_html(index=False, escape=True)

    return html.replace(
        '<table border="1" class="dataframe">',
        f'<table id="{table_id}">'
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML, result=None)

    job_id = str(uuid.uuid4())
    job_dir = REPORT_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    old_file = request.files.get("old_file")
    current_file = request.files.get("current_file")

    if not old_file or old_file.filename == "":
        return "Old Shopify subscribed file is missing."

    if not current_file or current_file.filename == "":
        return "Current Shopify customer file is missing."

    old_path = UPLOAD_DIR / f"{job_id}_old_{secure_filename(old_file.filename)}"
    current_path = UPLOAD_DIR / f"{job_id}_current_{secure_filename(current_file.filename)}"

    old_file.save(old_path)
    current_file.save(current_path)

    old_df = norm_cols(read_csv_auto(old_path))
    current_df = norm_cols(read_csv_auto(current_path))

    if "email" not in old_df.columns:
        return f"Old file missing Email column. Found columns: {list(old_df.columns)}"

    if "email" not in current_df.columns:
        return f"Current file missing Email column. Found columns: {list(current_df.columns)}"

    old_sub_col = find_subscription_col(old_df)
    current_sub_col = find_subscription_col(current_df)

    if not old_sub_col:
        return f"Old file missing subscription column. Need Accepts Email Marketing or Email Subscription Status. Found: {list(old_df.columns)}"

    if not current_sub_col:
        return f"Current file missing subscription column. Need Accepts Email Marketing or Email Subscription Status. Found: {list(current_df.columns)}"

    old_df["email_normalized"] = old_df["email"].apply(norm_email)
    current_df["email_normalized"] = current_df["email"].apply(norm_email)

    old_df = old_df[old_df["email_normalized"].notna()].copy()
    current_df = current_df[current_df["email_normalized"].notna()].copy()

    old_df["old_subscribed"] = old_df[old_sub_col].apply(is_subscribed)
    current_df["current_subscribed"] = current_df[current_sub_col].apply(is_subscribed)

    old_subscribed = old_df[old_df["old_subscribed"]].drop_duplicates("email_normalized").copy()
    current_unique = current_df.drop_duplicates("email_normalized").copy()

    merged = old_subscribed.merge(
        current_unique,
        on="email_normalized",
        how="left",
        suffixes=("_old", "_current"),
        indicator=True
    )

    now_unsubscribed = merged[
        (merged["_merge"] == "both") &
        (merged["current_subscribed"] == False)
    ].copy()

    still_subscribed = merged[
        (merged["_merge"] == "both") &
        (merged["current_subscribed"] == True)
    ].copy()

    missing_current = merged[
        merged["_merge"] == "left_only"
    ].copy()

    full_comparison = merged.copy()
    full_comparison["audit_status"] = full_comparison.apply(
        lambda r:
            "NOW_UNSUBSCRIBED_OR_NOT_SUBSCRIBED"
            if r["_merge"] == "both" and r["current_subscribed"] == False
            else "STILL_SUBSCRIBED"
            if r["_merge"] == "both" and r["current_subscribed"] == True
            else "MISSING_IN_CURRENT_FILE",
        axis=1
    )

    now_unsubscribed.to_csv(job_dir / "now_unsubscribed.csv", index=False, encoding="utf-8-sig")
    still_subscribed.to_csv(job_dir / "still_subscribed.csv", index=False, encoding="utf-8-sig")
    missing_current.to_csv(job_dir / "missing_in_current.csv", index=False, encoding="utf-8-sig")
    full_comparison.to_csv(job_dir / "full_comparison.csv", index=False, encoding="utf-8-sig")

    result = {
        "old_subscribed": int(old_subscribed["email_normalized"].nunique()),
        "current_total": int(current_unique["email_normalized"].nunique()),
        "still_subscribed": int(still_subscribed["email_normalized"].nunique()),
        "now_unsubscribed": int(now_unsubscribed["email_normalized"].nunique()),
        "missing_current": int(missing_current["email_normalized"].nunique()),
    }

    return render_template_string(
        HTML,
        result=result,
        job_id=job_id,
        unsubscribed_table=make_table(now_unsubscribed, "table_unsub"),
        still_table=make_table(still_subscribed, "table_still"),
        missing_table=make_table(missing_current, "table_missing"),
    )


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    path = REPORT_DIR / job_id / filename

    if not path.exists():
        return "File not found."

    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        debug=False,
        host="127.0.0.1",
        port=port,
        use_reloader=False
    )