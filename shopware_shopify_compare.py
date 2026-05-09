from flask import Flask, request, render_template_string, send_file
import pandas as pd
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("audit_downloads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HTML = """
<!doctype html>
<html>
<head>
<title>Shopware Newsletter Audit</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;background:#f3f4f6;margin:0;padding:0}
.page-shell{padding:20px}
.box{background:white;padding:25px;border-radius:16px;max-width:1400px;margin:auto;box-shadow:0 18px 50px rgba(15,23,42,0.08)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;margin:20px 0}
.card{background:#eef2ff;padding:18px;border-radius:16px;min-height:110px;display:flex;flex-direction:column;justify-content:center}
.card strong{display:block;font-size:28px;margin-top:10px}
.good{background:#dcfce7}.bad{background:#fee2e2}.warn{background:#fef3c7}
button, .button-link{background:#111827;color:white;border:0;border-radius:10px;padding:12px 18px;cursor:pointer;margin:5px 0;transition:background .2s;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
button:hover, .button-link:hover{background:#374151}
input{width:100%;padding:12px;margin:10px 0 15px 0;border:1px solid #d1d5db;border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #ddd;padding:8px;text-align:left;white-space:nowrap}
th{background:#f9fafb;position:sticky;top:0;z-index:2}
.wrap{overflow:auto;max-height:680px;border:1px solid #ddd;border-radius:12px;margin-bottom:25px;padding:10px;background:#fff}
.notice{padding:18px;border-radius:12px;margin:15px 0;background:#fef3c7;color:#92400e}
.topbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px;margin-bottom:24px}
.title-block{min-width:260px}
.title-block h1{margin:0;font-size:32px}
.page-actions{display:flex;flex-wrap:wrap;gap:10px}
.download-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:15px 0}
.tabs{display:flex;flex-wrap:wrap;gap:10px;margin:15px 0;padding-bottom:10px;border-bottom:1px solid #e5e7eb;position:sticky;top:0;background:#fff;z-index:5}
.tab-button{background:#e5e7eb;color:#111827;border:0;border-radius:10px;padding:10px 16px;cursor:pointer}
.tab-button.active{background:#2563eb;color:white}
.tab-content{display:none}
.tab-content.active{display:block}
.section-header{margin:0 0 10px}
.summary-block{background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:16px}
.section-title{margin:30px 0 10px}
.note-bar{background:#f8fafc;border:1px solid #e5e7eb;padding:16px;border-radius:12px;margin:20px 0}
</style>

<script>
function filterTable(inputId, tableId, countId) {
    let input = document.getElementById(inputId).value.toLowerCase();
    let table = document.getElementById(tableId);
    let rows = table.getElementsByTagName("tr");
    let visible = 0;

    for (let i = 1; i < rows.length; i++) {
        let text = rows[i].innerText.toLowerCase();
        if (text.includes(input)) {
            rows[i].style.display = "";
            visible++;
        } else {
            rows[i].style.display = "none";
        }
    }
    if (document.getElementById(countId)) {
        document.getElementById(countId).innerText = visible;
    }
}

function showTab(tabId, button) {
    document.querySelectorAll('.tab-content').forEach(function(section) {
        section.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(function(btn) {
        btn.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
    if (button) button.classList.add('active');
    window.scrollTo({top:document.getElementById(tabId).offsetTop - 90, behavior:'smooth'});
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('btn_group_breakdown')) {
        showTab('tab_group_breakdown', document.getElementById('btn_group_breakdown'));
    }
});
</script>
</head>

<body>
<div class="box">

<h1>Shopware & Shopify Newsletter Audit</h1>

<div class="notice">
This tool audits newsletter subscriptions from Shopware and Shopify CSVs. Compare customer bases, find overlaps, and identify new customers.
</div>

{% if not (result or compare_result) %}
<div class="note-bar">
<p><strong>Choose your analysis:</strong> Upload a single file for detailed audit, or compare two files to see customer overlaps and differences.</p>
</div>

<div class="compare-form">
<div>
<h3>Single File Audit</h3>
<p>Upload one CSV (Shopware or Shopify) for a complete audit.</p>
<form method=\"POST\" enctype=\"multipart/form-data\" action=\"/analyze\">
<input type=\"file\" name=\"shopware_file\" required>
<button type=\"submit\">Analyze Single File</button>
</form>
<a href=\"/analyze_shopify\"><button>Analyze Shopify Export (34,000 customers)</button></a>
</div>

<div>
<h3>Compare Shopware vs Shopify</h3>
<p>Upload both files to compare customer bases and find new customers.</p>
<form method=\"POST\" enctype=\"multipart/form-data\" action=\"/compare\">
<label>Shopware CSV:</label>
<input type=\"file\" name=\"shopware_file\" required>
<label>Shopify CSV:</label>
<input type=\"file\" name=\"shopify_file\" required>
<button type=\"submit\">Compare Files</button>
</form>
</div>
</div>
{% endif %}

<div class="topbar">
<div class="title-block">
<h1>Shopware Newsletter Audit</h1>
<p class="section-header">Analyze your CSV and get exact customer counts with quick download access.</p>
</div>
<div class="page-actions">
<button onclick="window.location='/'">Upload New File</button>
<a class="button-link" href="/download/{{ job_id }}/unique_customers_full_data.csv">Download Unique Customers</a>
<a class="button-link" href="/download/{{ job_id }}/duplicate_email_summary.csv">Download Duplicate Summary</a>
</div>
</div>

<div class="summary-block">
<h2 class="section-title">Exact customer counts</h2>
<div class="grid">
<div class="card warn">Total raw rows<strong>{{ result.total_rows }}</strong></div>
<div class="card good">Exact unique customers found<strong>{{ result.exact_customers_found }}</strong></div>
<div class="card bad">Repeated customer emails<strong>{{ result.repeated_email_customer_count }}</strong></div>
<div class="card bad">Rows belonging to repeated emails<strong>{{ result.repeated_row_count }}</strong></div>
<div class="card good">Unique subscribed customers<strong>{{ result.subscribed_unique }}</strong></div>
<div class="card warn">Unique unsubscribed customers<strong>{{ result.unsubscribed_unique }}</strong></div>
<div class="card good">Unique non-repeated customers<strong>{{ result.unique_non_repeated }}</strong></div>
<div class="card">Invalid email rows removed<strong>{{ result.invalid_emails }}</strong></div>
</div>

<h2 class="section-title">Basic data diagnostics</h2>
<div class="grid">
<div class="card">Newsletter column<strong>{{ result.newsletter_col }}</strong></div>
<div class="card">Group column<strong>{{ result.group_col }}</strong></div>
<div class="card">DOI column<strong>{{ result.doi_col }}</strong></div>
<div class="card good">Double opt-in confirmed<strong>{{ result.double_opt_in }}</strong></div>
<div class="card good">Emails in more than one group<strong>{{ result.repeated_across_groups }}</strong></div>
</div>
</div>

<div class="note-bar">
<p><strong>Quick actions:</strong> Use the tabs below to switch between reports without scrolling, and download any data set from the buttons above.</p>
</div>

<h2>Download Reports</h2>
<div class="download-grid">
<a class="button-link" href="/download/{{ job_id }}/unique_customers_full_data.csv">Unique Customers Full Data</a>
<a class="button-link" href="/download/{{ job_id }}/unique_non_repeated_customers.csv">Unique Non-Repeated Customers</a>
<a class="button-link" href="/download/{{ job_id }}/subscribed_unique_full_data.csv">Subscribed Unique Full Data</a>
<a class="button-link" href="/download/{{ job_id }}/unsubscribed_unique_full_data.csv">Unsubscribed Unique Full Data</a>
<a class="button-link" href="/download/{{ job_id }}/subscribed_unique_emails_only.csv">Emails Only</a>
<a class="button-link" href="/download/{{ job_id }}/duplicate_email_summary.csv">Duplicate Email Summary</a>
<a class="button-link" href="/download/{{ job_id }}/duplicate_rows_full_data.csv">Duplicate Rows Full Data</a>
<a class="button-link" href="/download/{{ job_id }}/top_duplicate_emails.csv">Top Duplicate Emails</a>
<a class="button-link" href="/download/{{ job_id }}/group_breakdown.csv">Group Breakdown</a>
<a class="button-link" href="/download/{{ job_id }}/emails_repeated_across_groups.csv">Emails Repeated Across Groups</a>
<a class="button-link" href="/download/{{ job_id }}/group_membership_matrix.csv">Group Membership Matrix</a>
</div>

<div class="tabs">
<button class="tab-button" id="btn_group_breakdown" onclick="showTab('tab_group_breakdown', this)">Group Breakdown</button>
<button class="tab-button" id="btn_group_repeat" onclick="showTab('tab_group_repeat', this)">Repeated Across Groups</button>
<button class="tab-button" id="btn_group_matrix" onclick="showTab('tab_group_matrix', this)">Group Matrix</button>
<button class="tab-button" id="btn_subscribed" onclick="showTab('tab_subscribed', this)">Subscribed</button>
<button class="tab-button" id="btn_unsubscribed" onclick="showTab('tab_unsubscribed', this)">Unsubscribed</button>
<button class="tab-button" id="btn_unique_non_repeated" onclick="showTab('tab_unique_non_repeated', this)">Non-Repeated</button>
<button class="tab-button" id="btn_email_only" onclick="showTab('tab_email_only', this)">Email Only</button>
<button class="tab-button" id="btn_top_duplicates" onclick="showTab('tab_top_duplicates', this)">Top Duplicates</button>
<button class="tab-button" id="btn_dup_summary" onclick="showTab('tab_dup_summary', this)">Duplicate Summary</button>
<button class="tab-button" id="btn_duplicates" onclick="showTab('tab_duplicates', this)">Duplicate Rows</button>
<button class="tab-button" id="btn_unique" onclick="showTab('tab_unique', this)">All Unique</button>
</div>

<div class="tab-section">
<div id="tab_group_breakdown" class="tab-content active">
<h3>Group Breakdown</h3>
<div class="wrap">{{ group_table|safe }}</div>
</div>

<div id="tab_group_repeat" class="tab-content">
<h3>Emails Repeated Across Groups</h3>
<p>Emails shown: <b id="count_group_repeat">{{ result.repeated_across_groups }}</b></p>
<input id="search_group_repeat" onkeyup="filterTable('search_group_repeat','table_group_repeat','count_group_repeat')" placeholder="Search repeated emails across groups...">
<div class="wrap">{{ group_repeat_table|safe }}</div>
</div>

<div id="tab_group_matrix" class="tab-content">
<h3>Group Membership Matrix</h3>
<p>This shows which email belongs to which newsletter group.</p>
<input id="search_matrix" onkeyup="filterTable('search_matrix','table_matrix','count_matrix')" placeholder="Search group matrix...">
<p>Total shown: <b id="count_matrix">{{ result.unique_emails }}</b></p>
<div class="wrap">{{ group_matrix_table|safe }}</div>
</div>

<div id="tab_subscribed" class="tab-content">
<h3>Unique Subscribed Customers</h3>
<p>Total shown: <b id="count_subscribed">{{ result.subscribed_unique }}</b></p>
<input id="search_subscribed" onkeyup="filterTable('search_subscribed','table_subscribed','count_subscribed')" placeholder="Search subscribed customers...">
<div class="wrap">{{ subscribed_table|safe }}</div>
</div>

<div id="tab_unsubscribed" class="tab-content">
<h3>Unsubscribed Unique Customers</h3>
<p>Total shown: <b id="count_unsubscribed">{{ result.unsubscribed_unique }}</b></p>
<input id="search_unsubscribed" onkeyup="filterTable('search_unsubscribed','table_unsubscribed','count_unsubscribed')" placeholder="Search unsubscribed customers...">
<div class="wrap">{{ unsubscribed_table|safe }}</div>
</div>

<div id="tab_unique_non_repeated" class="tab-content">
<h3>Unique Customers with No Repeats</h3>
<p>Total shown: <b id="count_unique_non_repeated">{{ result.unique_non_repeated }}</b></p>
<input id="search_unique_non_repeated" onkeyup="filterTable('search_unique_non_repeated','table_unique_non_repeated','count_unique_non_repeated')" placeholder="Search unique non-repeated customers...">
<div class="wrap">{{ unique_non_repeated_table|safe }}</div>
</div>

<div id="tab_email_only" class="tab-content">
<h3>Email-only List: Unique Subscribed Emails</h3>
<p>Total shown: <b id="count_email_only">{{ result.subscribed_unique }}</b></p>
<input id="search_email_only" onkeyup="filterTable('search_email_only','table_email_only','count_email_only')" placeholder="Search email...">
<div class="wrap">{{ email_only_table|safe }}</div>
</div>

<div id="tab_top_duplicates" class="tab-content">
<h3>Top Duplicate Email Addresses</h3>
<p>These addresses appear most often in the upload.</p>
<input id="search_top_duplicates" onkeyup="filterTable('search_top_duplicates','table_top_duplicates','count_top_duplicates')" placeholder="Search top duplicates...">
<p>Total shown: <b id="count_top_duplicates">{{ result.duplicate_email_count }}</b></p>
<div class="wrap">{{ top_duplicate_table|safe }}</div>
</div>

<div id="tab_dup_summary" class="tab-content">
<h3>Duplicate Email Addresses</h3>
<p>Total shown: <b id="count_dup_summary">{{ result.duplicate_email_count }}</b></p>
<input id="search_dup_summary" onkeyup="filterTable('search_dup_summary','table_dup_summary','count_dup_summary')" placeholder="Search duplicated email...">
<div class="wrap">{{ duplicate_summary_table|safe }}</div>
</div>

<div id="tab_duplicates" class="tab-content">
<h3>All Duplicate Rows</h3>
<p>Total shown: <b id="count_duplicates">{{ result.duplicate_rows }}</b></p>
<input id="search_duplicates" onkeyup="filterTable('search_duplicates','table_duplicates','count_duplicates')" placeholder="Search duplicate rows...">
<div class="wrap">{{ duplicate_rows_table|safe }}</div>
</div>

<div id="tab_unique" class="tab-content">
<h3>All Unique Customers</h3>
<p>Total shown: <b id="count_unique">{{ result.unique_emails }}</b></p>
<input id="search_unique" onkeyup="filterTable('search_unique','table_unique','count_unique')" placeholder="Search all unique customers...">
<div class="wrap">{{ unique_table|safe }}</div>
</div>
</div>

{% if compare_result %}

<div class=\"topbar\">
<div class=\"title-block\">
<h1>Shopware vs Shopify Comparison</h1>
<p class=\"section-header\">Customer overlap analysis between your Shopware and Shopify databases.</p>
</div>
<div class=\"page-actions\">
<button onclick=\"window.location='/'\">New Analysis</button>
<a class=\"button-link\" href=\"/download/{{ compare_job_id }}/shopware_only_customers.csv\">Download Shopware Only</a>
<a class=\"button-link\" href=\"/download/{{ compare_job_id }}/shopify_only_customers.csv\">Download Shopify Only</a>
<a class=\"button-link\" href=\"/download/{{ compare_job_id }}/overlap_customers.csv\">Download Overlap</a>
</div>
</div>

<div class=\"summary-block\">
<h2 class=\"section-title\">Customer Base Comparison</h2>
<div class=\"grid\">
<div class=\"card good\">Shopware Unique Customers<strong>{{ compare_result.shopware_unique }}</strong></div>
<div class=\"card good\">Shopify Unique Customers<strong>{{ compare_result.shopify_unique }}</strong></div>
<div class=\"card warn\">Customers in Both Systems<strong>{{ compare_result.overlap_count }}</strong></div>
<div class=\"card bad\">New Customers from Shopify<strong>{{ compare_result.shopify_only }}</strong></div>
<div class=\"card\">Shopware Subscribed<strong>{{ compare_result.shopware_subscribed }}</strong></div>
<div class=\"card\">Shopify Subscribed<strong>{{ compare_result.shopify_subscribed }}</strong></div>
<div class=\"card good\">Overlap Subscribed<strong>{{ compare_result.overlap_subscribed }}</strong></div>
<div class=\"card warn\">Total Unique Across Both<strong>{{ compare_result.total_unique }}</strong></div>
</div>
</div>

<div class=\"note-bar\">
<p><strong>Key Insights:</strong> {{ compare_result.total_unique }} total unique customers across both systems. {{ compare_result.shopify_only }} new customers from Shopify. {{ compare_result.overlap_count }} customers exist in both.</p>
</div>

<h2>Detailed Breakdown</h2>
<div class=\"tabs\">
<button class=\"tab-button\" id=\"btn_shopware_only\" onclick=\"showTab('tab_shopware_only', this)\">Shopware Only ({{ compare_result.shopware_only }})</button>
<button class=\"tab-button\" id=\"btn_shopify_only\" onclick=\"showTab('tab_shopify_only', this)\">Shopify Only ({{ compare_result.shopify_only }})</button>
<button class=\"tab-button\" id=\"btn_overlap\" onclick=\"showTab('tab_overlap', this)\">Overlap ({{ compare_result.overlap_count }})</button>
</div>

<div class=\"tab-section\">
<div id=\"tab_shopware_only\" class=\"tab-content active\">
<h3>Customers Only in Shopware</h3>
<p>These customers are in Shopware but not in Shopify.</p>
<input id=\"search_shopware_only\" onkeyup=\"filterTable('search_shopware_only','table_shopware_only','count_shopware_only')\" placeholder=\"Search Shopware only customers...\">
<p>Total shown: <b id=\"count_shopware_only\">{{ compare_result.shopware_only }}</b></p>
<div class=\"wrap\">{{ shopware_only_table|safe }}</div>
</div>

<div id=\"tab_shopify_only\" class=\"tab-content\">
<h3>Customers Only in Shopify</h3>
<p>These are new customers from Shopify not in Shopware.</p>
<input id=\"search_shopify_only\" onkeyup=\"filterTable('search_shopify_only','table_shopify_only','count_shopify_only')\" placeholder=\"Search Shopify only customers...\">
<p>Total shown: <b id=\"count_shopify_only\">{{ compare_result.shopify_only }}</b></p>
<div class=\"wrap\">{{ shopify_only_table|safe }}</div>
</div>

<div id=\"tab_overlap\" class=\"tab-content\">
<h3>Customers in Both Systems</h3>
<p>These customers exist in both Shopware and Shopify.</p>
<input id=\"search_overlap\" onkeyup=\"filterTable('search_overlap','table_overlap','count_overlap')\" placeholder=\"Search overlap customers...\">
<p>Total shown: <b id=\"count_overlap\">{{ compare_result.overlap_count }}</b></p>
<div class=\"wrap\">{{ overlap_table|safe }}</div>
</div>
</div>

{% endif %}</div>
</body>
</html>
"""


def read_csv_auto(path):
    for sep in [";", ",", "\t", "|"]:
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
    raise Exception("Could not read CSV file")


def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def normalize_email(value):
    if pd.isna(value):
        return None
    email = str(value).strip().lower()
    if email.startswith("'"):
        email = email[1:]
    return email if "@" in email else None


def truthy(value):
    if pd.isna(value):
        return False
    return str(value).strip().lower() in [
        "1", "yes", "true", "subscribed", "confirmed",
        "doi_confirmed", "opted_in", "ja"
    ]


def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def make_table(df, table_id, limit=30000):
    if df.empty:
        return f'<table id="{table_id}"><tr><th>No rows found</th></tr></table>'

    html = df.head(limit).fillna("").to_html(index=False, escape=True)
    return html.replace(
        '<table border="1" class="dataframe">',
        f'<table id="{table_id}">'
    )


def safe_group_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_newsletter_group(value):
    v = safe_group_value(value).lower()
    return (
        "newsletter" in v
        or "empfänger" in v
        or "empfanger" in v
    )


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML, result=None, compare_result=None)


@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_file = request.files.get("shopware_file")
    if not uploaded_file or uploaded_file.filename == "":
        return "No file uploaded"

    filename = secure_filename(uploaded_file.filename)
    path = UPLOAD_DIR / f"{uuid.uuid4()}_{filename}"
    uploaded_file.save(path)

    df = normalize_columns(read_csv_auto(path))

    if "email" not in df.columns:
        return "CSV missing required column: email"

    df["email_normalized"] = df["email"].apply(normalize_email)
    invalid_emails = int(df["email_normalized"].isna().sum())
    df = df[df["email_normalized"].notna()].copy()

    newsletter_col = find_col(df, [
        "newsletter",
        "subscribed",
        "email_subscription_status",
        "accepts email marketing",
        "accepts_email_marketing"
    ])

    group_col = find_col(df, ["group", "customer_group", "customergroup", "tags"])

    doi_col = find_col(df, [
        "double_opt-in",
        "double_opt_in",
        "double opt-in",
        "doi",
        "doi_confirmed",
        "double_opt_in_confirmed"
    ])

    if newsletter_col:
        df["subscribed_by_newsletter_col"] = df[newsletter_col].apply(truthy)
    else:
        df["subscribed_by_newsletter_col"] = False
        newsletter_col = "NOT FOUND"

    if group_col:
        df["group_clean"] = df[group_col].apply(safe_group_value)
        df["subscribed_by_group"] = df[group_col].apply(is_newsletter_group)
    else:
        df["group_clean"] = "NO GROUP COLUMN"
        df["subscribed_by_group"] = False
        group_col = "NOT FOUND"

    filename_lower = filename.lower()
    implicit_file_subscriber = any(x in filename_lower for x in [
        "newsletter", "empf", "subscriber", "subscribed"
    ])

    df["subscribed_by_file_name"] = implicit_file_subscriber

    df["is_subscribed"] = (
        df["subscribed_by_newsletter_col"]
        | df["subscribed_by_group"]
        | df["subscribed_by_file_name"]
    )

    if doi_col:
        df["is_double_opt_in"] = df[doi_col].apply(truthy)
    else:
        df["is_double_opt_in"] = False
        doi_col = "NOT FOUND"

    duplicate_rows = df[df.duplicated(subset=["email_normalized"], keep=False)].copy()

    duplicate_summary = (
        df.groupby("email_normalized")
        .size()
        .reset_index(name="times_found")
        .sort_values("times_found", ascending=False)
    )
    duplicate_summary = duplicate_summary[duplicate_summary["times_found"] > 1]

    unique_customers = df.drop_duplicates(subset=["email_normalized"], keep="first").copy()
    subscribed_unique = unique_customers[unique_customers["is_subscribed"] == True].copy()
    unsubscribed_unique = unique_customers[unique_customers["is_subscribed"] == False].copy()
    unique_non_repeated = unique_customers[~unique_customers["email_normalized"].isin(duplicate_summary["email_normalized"])].copy()
    doi_confirmed = unique_customers[unique_customers["is_double_opt_in"] == True].copy()

    email_only = subscribed_unique[["email_normalized"]].rename(columns={"email_normalized": "email"})
    top_duplicate_emails = duplicate_summary.head(100).copy()

    group_breakdown = (
        df.groupby("group_clean")
        .agg(
            raw_rows=("email_normalized", "size"),
            unique_emails=("email_normalized", "nunique")
        )
        .reset_index()
        .sort_values("unique_emails", ascending=False)
    )

    group_membership = (
        df.groupby("email_normalized")["group_clean"]
        .apply(lambda x: sorted(set([g for g in x if g])))
        .reset_index()
    )
    group_membership["groups_count"] = group_membership["group_clean"].apply(len)
    group_membership["groups_joined"] = group_membership["group_clean"].apply(lambda x: " | ".join(x))

    group_repeat = group_membership[group_membership["groups_count"] > 1].copy()
    group_repeat = group_repeat.sort_values("groups_count", ascending=False)

    all_groups = sorted(set(g for groups in group_membership["group_clean"] for g in groups if g))

    group_matrix = group_membership[["email_normalized", "groups_count", "groups_joined"]].copy()
    for g in all_groups:
        group_matrix[g] = group_membership["group_clean"].apply(lambda groups: "YES" if g in groups else "")

    display_cols_preferred = [
        "email",
        "email_normalized",
        "group",
        "group_clean",
        "salutation",
        "firstname",
        "lastname",
        "street",
        "zipcode",
        "city",
        "customernumber",
        "newsletter",
        "subscribed_by_group",
        "subscribed_by_file_name",
        "is_subscribed",
        "is_double_opt_in",
    ]

    def pick_cols(dataframe):
        cols = [c for c in display_cols_preferred if c in dataframe.columns]
        remaining = [c for c in dataframe.columns if c not in cols]
        return cols + remaining[:15]

    result = {
        "total_rows": int(len(df)),
        "unique_emails": int(unique_customers["email_normalized"].nunique()),
        "exact_customers_found": int(unique_customers["email_normalized"].nunique()),
        "unique_non_repeated": int(unique_non_repeated["email_normalized"].nunique()),
        "subscribed_unique": int(subscribed_unique["email_normalized"].nunique()),
        "unsubscribed_unique": int(unsubscribed_unique["email_normalized"].nunique()),
        "duplicate_rows": int(len(duplicate_rows)),
        "duplicate_email_count": int(duplicate_summary["email_normalized"].nunique()),
        "repeated_email_customer_count": int(duplicate_summary["email_normalized"].nunique()),
        "repeated_row_count": int(len(duplicate_rows)),
        "double_opt_in": int(doi_confirmed["email_normalized"].nunique()),
        "invalid_emails": invalid_emails,
        "newsletter_col": newsletter_col,
        "group_col": group_col,
        "doi_col": doi_col,
        "repeated_across_groups": int(group_repeat["email_normalized"].nunique()),
    }

    job_id = str(uuid.uuid4())
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    unique_customers.to_csv(job_dir / "unique_customers_full_data.csv", index=False, encoding="utf-8-sig")
    subscribed_unique.to_csv(job_dir / "subscribed_unique_full_data.csv", index=False, encoding="utf-8-sig")
    email_only.to_csv(job_dir / "subscribed_unique_emails_only.csv", index=False, encoding="utf-8-sig")
    duplicate_summary.to_csv(job_dir / "duplicate_email_summary.csv", index=False, encoding="utf-8-sig")
    duplicate_rows.to_csv(job_dir / "duplicate_rows_full_data.csv", index=False, encoding="utf-8-sig")
    unique_non_repeated.to_csv(job_dir / "unique_non_repeated_customers.csv", index=False, encoding="utf-8-sig")
    unsubscribed_unique.to_csv(job_dir / "unsubscribed_unique_full_data.csv", index=False, encoding="utf-8-sig")
    top_duplicate_emails.to_csv(job_dir / "top_duplicate_emails.csv", index=False, encoding="utf-8-sig")
    group_breakdown.to_csv(job_dir / "group_breakdown.csv", index=False, encoding="utf-8-sig")
    group_repeat.to_csv(job_dir / "emails_repeated_across_groups.csv", index=False, encoding="utf-8-sig")
    group_matrix.to_csv(job_dir / "group_membership_matrix.csv", index=False, encoding="utf-8-sig")

    return render_template_string(
        HTML,
        result=result,
        compare_result=None,
        job_id=job_id,
        group_table=make_table(group_breakdown, "table_group"),
        group_repeat_table=make_table(group_repeat, "table_group_repeat"),
        group_matrix_table=make_table(group_matrix, "table_matrix"),
        subscribed_table=make_table(subscribed_unique[pick_cols(subscribed_unique)], "table_subscribed"),
        unsubscribed_table=make_table(unsubscribed_unique[pick_cols(unsubscribed_unique)], "table_unsubscribed"),
        unique_non_repeated_table=make_table(unique_non_repeated[pick_cols(unique_non_repeated)], "table_unique_non_repeated"),
        email_only_table=make_table(email_only, "table_email_only"),
        top_duplicate_table=make_table(top_duplicate_emails, "table_top_duplicates"),
        duplicate_summary_table=make_table(duplicate_summary, "table_dup_summary"),
        duplicate_rows_table=make_table(duplicate_rows[pick_cols(duplicate_rows)], "table_duplicates"),
        unique_table=make_table(unique_customers[pick_cols(unique_customers)], "table_unique"),
    )


@app.route("/analyze_shopify")
def analyze_shopify():
    path = Path("/Users/hamza/Desktop/customers_export 4.csv")
    if not path.exists():
        return "Shopify export file not found at /Users/hamza/Desktop/customers_export 4.csv"

    df = normalize_columns(read_csv_auto(path))

    if "email" not in df.columns:
        return "CSV missing required column: email"

    df["email_normalized"] = df["email"].apply(normalize_email)
    invalid_emails = int(df["email_normalized"].isna().sum())
    df = df[df["email_normalized"].notna()].copy()

    newsletter_col = find_col(df, [
        "newsletter",
        "subscribed",
        "email_subscription_status",
        "accepts email marketing",
        "accepts_email_marketing"
    ])

    group_col = find_col(df, ["group", "customer_group", "customergroup", "tags"])

    doi_col = find_col(df, [
        "double_opt-in",
        "double_opt_in",
        "double opt-in",
        "doi",
        "doi_confirmed",
        "double_opt_in_confirmed"
    ])

    if newsletter_col:
        df["subscribed_by_newsletter_col"] = df[newsletter_col].apply(truthy)
    else:
        df["subscribed_by_newsletter_col"] = False
        newsletter_col = "NOT FOUND"

    if group_col:
        df["group_clean"] = df[group_col].apply(safe_group_value)
        df["subscribed_by_group"] = df[group_col].apply(is_newsletter_group)
    else:
        df["group_clean"] = "NO GROUP COLUMN"
        df["subscribed_by_group"] = False
        group_col = "NOT FOUND"

    filename_lower = "customers_export 4.csv".lower()
    implicit_file_subscriber = any(x in filename_lower for x in [
        "newsletter", "empf", "subscriber", "subscribed"
    ])

    df["subscribed_by_file_name"] = implicit_file_subscriber

    df["is_subscribed"] = (
        df["subscribed_by_newsletter_col"]
        | df["subscribed_by_group"]
        | df["subscribed_by_file_name"]
    )

    if doi_col:
        df["is_double_opt_in"] = df[doi_col].apply(truthy)
    else:
        df["is_double_opt_in"] = False
        doi_col = "NOT FOUND"

    duplicate_rows = df[df.duplicated(subset=["email_normalized"], keep=False)].copy()

    duplicate_summary = (
        df.groupby("email_normalized")
        .size()
        .reset_index(name="times_found")
        .sort_values("times_found", ascending=False)
    )
    duplicate_summary = duplicate_summary[duplicate_summary["times_found"] > 1]

    unique_customers = df.drop_duplicates(subset=["email_normalized"], keep="first").copy()
    subscribed_unique = unique_customers[unique_customers["is_subscribed"] == True].copy()
    unsubscribed_unique = unique_customers[unique_customers["is_subscribed"] == False].copy()
    unique_non_repeated = unique_customers[~unique_customers["email_normalized"].isin(duplicate_summary["email_normalized"])].copy()
    doi_confirmed = unique_customers[unique_customers["is_double_opt_in"] == True].copy()

    email_only = subscribed_unique[["email_normalized"]].rename(columns={"email_normalized": "email"})
    top_duplicate_emails = duplicate_summary.head(100).copy()

    group_breakdown = (
        df.groupby("group_clean")
        .agg(
            raw_rows=("email_normalized", "size"),
            unique_emails=("email_normalized", "nunique")
        )
        .reset_index()
        .sort_values("unique_emails", ascending=False)
    )

    group_membership = (
        df.groupby("email_normalized")["group_clean"]
        .apply(lambda x: sorted(set([g for g in x if g])))
        .reset_index()
    )
    group_membership["groups_count"] = group_membership["group_clean"].apply(len)
    group_membership["groups_joined"] = group_membership["group_clean"].apply(lambda x: " | ".join(x))

    group_repeat = group_membership[group_membership["groups_count"] > 1].copy()
    group_repeat = group_repeat.sort_values("groups_count", ascending=False)

    all_groups = sorted(set(g for groups in group_membership["group_clean"] for g in groups if g))

    group_matrix = group_membership[["email_normalized", "groups_count", "groups_joined"]].copy()
    for g in all_groups:
        group_matrix[g] = group_membership["group_clean"].apply(lambda groups: "YES" if g in groups else "")

    display_cols_preferred = [
        "email",
        "email_normalized",
        "group",
        "group_clean",
        "salutation",
        "firstname",
        "lastname",
        "street",
        "zipcode",
        "city",
        "customernumber",
        "newsletter",
        "subscribed_by_group",
        "subscribed_by_file_name",
        "is_subscribed",
        "is_double_opt_in",
    ]

    def pick_cols(dataframe):
        cols = [c for c in display_cols_preferred if c in dataframe.columns]
        remaining = [c for c in dataframe.columns if c not in cols]
        return cols + remaining[:15]

    result = {
        "total_rows": int(len(df)),
        "unique_emails": int(unique_customers["email_normalized"].nunique()),
        "exact_customers_found": int(unique_customers["email_normalized"].nunique()),
        "unique_non_repeated": int(unique_non_repeated["email_normalized"].nunique()),
        "subscribed_unique": int(subscribed_unique["email_normalized"].nunique()),
        "unsubscribed_unique": int(unsubscribed_unique["email_normalized"].nunique()),
        "duplicate_rows": int(len(duplicate_rows)),
        "duplicate_email_count": int(duplicate_summary["email_normalized"].nunique()),
        "repeated_email_customer_count": int(duplicate_summary["email_normalized"].nunique()),
        "repeated_row_count": int(len(duplicate_rows)),
        "double_opt_in": int(doi_confirmed["email_normalized"].nunique()),
        "invalid_emails": invalid_emails,
        "newsletter_col": newsletter_col,
        "group_col": group_col,
        "doi_col": doi_col,
        "repeated_across_groups": int(group_repeat["email_normalized"].nunique()),
    }

    job_id = str(uuid.uuid4())
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    unique_customers.to_csv(job_dir / "unique_customers_full_data.csv", index=False, encoding="utf-8-sig")
    subscribed_unique.to_csv(job_dir / "subscribed_unique_full_data.csv", index=False, encoding="utf-8-sig")
    email_only.to_csv(job_dir / "subscribed_unique_emails_only.csv", index=False, encoding="utf-8-sig")
    duplicate_summary.to_csv(job_dir / "duplicate_email_summary.csv", index=False, encoding="utf-8-sig")
    duplicate_rows.to_csv(job_dir / "duplicate_rows_full_data.csv", index=False, encoding="utf-8-sig")
    unique_non_repeated.to_csv(job_dir / "unique_non_repeated_customers.csv", index=False, encoding="utf-8-sig")
    unsubscribed_unique.to_csv(job_dir / "unsubscribed_unique_full_data.csv", index=False, encoding="utf-8-sig")
    top_duplicate_emails.to_csv(job_dir / "top_duplicate_emails.csv", index=False, encoding="utf-8-sig")
    group_breakdown.to_csv(job_dir / "group_breakdown.csv", index=False, encoding="utf-8-sig")
    group_repeat.to_csv(job_dir / "emails_repeated_across_groups.csv", index=False, encoding="utf-8-sig")
    group_matrix.to_csv(job_dir / "group_membership_matrix.csv", index=False, encoding="utf-8-sig")

    return render_template_string(
        HTML,
        result=result,
        compare_result=None,
        job_id=job_id,
        group_table=make_table(group_breakdown, "table_group"),
        group_repeat_table=make_table(group_repeat, "table_group_repeat"),
        group_matrix_table=make_table(group_matrix, "table_matrix"),
        subscribed_table=make_table(subscribed_unique[pick_cols(subscribed_unique)], "table_subscribed"),
        unsubscribed_table=make_table(unsubscribed_unique[pick_cols(unsubscribed_unique)], "table_unsubscribed"),
        unique_non_repeated_table=make_table(unique_non_repeated[pick_cols(unique_non_repeated)], "table_unique_non_repeated"),
        email_only_table=make_table(email_only, "table_email_only"),
        top_duplicate_table=make_table(top_duplicate_emails, "table_top_duplicates"),
        duplicate_summary_table=make_table(duplicate_summary, "table_dup_summary"),
        duplicate_rows_table=make_table(duplicate_rows[pick_cols(duplicate_rows)], "table_duplicates"),
        unique_table=make_table(unique_customers[pick_cols(unique_customers)], "table_unique"),
    )


@app.route("/compare", methods=["POST"])
def compare():
    shopware_file = request.files.get("shopware_file")
    shopify_file = request.files.get("shopify_file")

    if not shopware_file or not shopify_file or shopware_file.filename == "" or shopify_file.filename == "":
        return "Both Shopware and Shopify files are required"

    # Process Shopware
    shopware_filename = secure_filename(shopware_file.filename)
    shopware_path = UPLOAD_DIR / f"{uuid.uuid4()}_{shopware_filename}"
    shopware_file.save(shopware_path)

    df_shopware = normalize_columns(read_csv_auto(shopware_path))
    if "email" not in df_shopware.columns:
        return "Shopware CSV missing required column: email"
    df_shopware["email_normalized"] = df_shopware["email"].apply(normalize_email)
    df_shopware = df_shopware[df_shopware["email_normalized"].notna()].copy()
    shopware_unique_emails = set(df_shopware["email_normalized"].unique())

    # Determine subscribed for Shopware
    newsletter_col_shopware = find_col(df_shopware, [
        "newsletter", "subscribed", "email_subscription_status",
        "accepts email marketing", "accepts_email_marketing"
    ])
    if newsletter_col_shopware:
        df_shopware["is_subscribed"] = df_shopware[newsletter_col_shopware].apply(truthy)
    else:
        df_shopware["is_subscribed"] = False
    shopware_subscribed = df_shopware.drop_duplicates(subset=["email_normalized"], keep="first")
    shopware_subscribed_count = int(shopware_subscribed[shopware_subscribed["is_subscribed"] == True]["email_normalized"].nunique())

    # Process Shopify
    shopify_filename = secure_filename(shopify_file.filename)
    shopify_path = UPLOAD_DIR / f"{uuid.uuid4()}_{shopify_filename}"
    shopify_file.save(shopify_path)

    df_shopify = normalize_columns(read_csv_auto(shopify_path))
    if "email" not in df_shopify.columns:
        return "Shopify CSV missing required column: email"
    df_shopify["email_normalized"] = df_shopify["email"].apply(normalize_email)
    df_shopify = df_shopify[df_shopify["email_normalized"].notna()].copy()
    shopify_unique_emails = set(df_shopify["email_normalized"].unique())

    # Determine subscribed for Shopify
    newsletter_col_shopify = find_col(df_shopify, [
        "newsletter", "subscribed", "email_subscription_status",
        "accepts email marketing", "accepts_email_marketing"
    ])
    if newsletter_col_shopify:
        df_shopify["is_subscribed"] = df_shopify[newsletter_col_shopify].apply(truthy)
    else:
        df_shopify["is_subscribed"] = False
    shopify_subscribed = df_shopify.drop_duplicates(subset=["email_normalized"], keep="first")
    shopify_subscribed_count = int(shopify_subscribed[shopify_subscribed["is_subscribed"] == True]["email_normalized"].nunique())

    # Comparisons
    overlap_emails = shopware_unique_emails & shopify_unique_emails
    shopware_only_emails = shopware_unique_emails - shopify_unique_emails
    shopify_only_emails = shopify_unique_emails - shopware_unique_emails

    total_unique = len(shopware_unique_emails | shopify_unique_emails)

    # Overlap subscribed
    overlap_subscribed_count = len(overlap_emails & set(shopware_subscribed[shopware_subscribed["is_subscribed"] == True]["email_normalized"]) & set(shopify_subscribed[shopify_subscribed["is_subscribed"] == True]["email_normalized"]))

    # Tables
    shopware_only_df = df_shopware[df_shopware["email_normalized"].isin(shopware_only_emails)].drop_duplicates(subset=["email_normalized"], keep="first")
    shopify_only_df = df_shopify[df_shopify["email_normalized"].isin(shopify_only_emails)].drop_duplicates(subset=["email_normalized"], keep="first")
    overlap_df = df_shopware[df_shopware["email_normalized"].isin(overlap_emails)].drop_duplicates(subset=["email_normalized"], keep="first").copy()
    # Add Shopify data to overlap if available
    overlap_shopify = df_shopify[df_shopify["email_normalized"].isin(overlap_emails)].drop_duplicates(subset=["email_normalized"], keep="first")
    overlap_df = overlap_df.merge(overlap_shopify, on="email_normalized", how="left", suffixes=("_shopware", "_shopify"))

    compare_result = {
        "shopware_unique": len(shopware_unique_emails),
        "shopify_unique": len(shopify_unique_emails),
        "overlap_count": len(overlap_emails),
        "shopware_only": len(shopware_only_emails),
        "shopify_only": len(shopify_only_emails),
        "total_unique": total_unique,
        "shopware_subscribed": shopware_subscribed_count,
        "shopify_subscribed": shopify_subscribed_count,
        "overlap_subscribed": overlap_subscribed_count,
    }

    compare_job_id = str(uuid.uuid4())
    compare_job_dir = OUTPUT_DIR / compare_job_id
    compare_job_dir.mkdir(exist_ok=True)

    shopware_only_df.to_csv(compare_job_dir / "shopware_only_customers.csv", index=False, encoding="utf-8-sig")
    shopify_only_df.to_csv(compare_job_dir / "shopify_only_customers.csv", index=False, encoding="utf-8-sig")
    overlap_df.to_csv(compare_job_dir / "overlap_customers.csv", index=False, encoding="utf-8-sig")

    return render_template_string(
        HTML,
        result=None,
        compare_result=compare_result,
        compare_job_id=compare_job_id,
        shopware_only_table=make_table(shopware_only_df, "table_shopware_only"),
        shopify_only_table=make_table(shopify_only_df, "table_shopify_only"),
        overlap_table=make_table(overlap_df, "table_overlap"),
    )


@app.route("/download/<job_id>/<filename>")
def download_file(job_id, filename):
    file_path = OUTPUT_DIR / job_id / filename

    if not file_path.exists():
        return "File not found"

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        debug=False,
        host="127.0.0.1",
        port=port,
        use_reloader=False
    )