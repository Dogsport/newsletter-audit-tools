from flask import Flask, request, render_template_string, send_file
import pandas as pd
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
REPORT_DIR = Path("audit_downloads")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

HTML = """
<!doctype html>
<html>
<head>
<title>Shopware Marketing Campaign Audit</title>
<style>
body{font-family:Arial;background:#f3f4f6;margin:0;padding:25px}
.box{background:white;border-radius:14px;padding:25px;max-width:1500px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px;margin:20px 0}
.card{background:#eef2ff;padding:18px;border-radius:12px}
.card strong{display:block;font-size:28px;margin-top:8px}
.good{background:#dcfce7}.bad{background:#fee2e2}.warn{background:#fef3c7}
button,.btn{background:#111827;color:white;border:0;border-radius:8px;padding:12px 18px;margin:5px;cursor:pointer;text-decoration:none;display:inline-block}
input{width:100%;padding:12px;margin:10px 0 20px;border:1px solid #ddd;border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #ddd;padding:8px;text-align:left;white-space:nowrap}
th{background:#f3f4f6;position:sticky;top:0}
.wrap{overflow:auto;max-height:600px;border:1px solid #ddd;border-radius:10px;margin-bottom:30px}
.notice{background:#fff3cd;padding:15px;border-radius:10px;margin:15px 0}
</style>

<script>
function filterTable(inputId, tableId, countId){
    let input=document.getElementById(inputId).value.toLowerCase();
    let rows=document.getElementById(tableId).getElementsByTagName("tr");
    let visible=0;
    for(let i=1;i<rows.length;i++){
        let text=rows[i].innerText.toLowerCase();
        if(text.includes(input)){rows[i].style.display="";visible++;}
        else{rows[i].style.display="none";}
    }
    document.getElementById(countId).innerText=visible;
}
</script>
</head>

<body>
<div class="box">
<h1>Shopware Marketing Campaign Audit</h1>

<div class="notice">
Upload your Shopware newsletter export. This tool finds unique subscribers, duplicates, repeated groups, DOI fields, and campaign candidate emails.
<br><br>
Important: This tool does not prove full GDPR-valid consent unless the file contains DOI, consent timestamp, and consent source.
</div>

{% if not result %}
<form method="POST" enctype="multipart/form-data">
<h3>Upload Shopware Newsletter CSV</h3>
<input type="file" name="shopware_file" required>
<button type="submit">Analyze File</button>
</form>
{% else %}

<h2>Summary</h2>
<div class="grid">
<div class="card warn">Total raw rows<strong>{{ result.total_rows }}</strong></div>
<div class="card good">Exact unique customers found<strong>{{ result.unique_customers }}</strong></div>
<div class="card good">Unique subscribed customers<strong>{{ result.subscribed_unique }}</strong></div>
<div class="card warn">Unique unsubscribed customers<strong>{{ result.unsubscribed_unique }}</strong></div>
<div class="card bad">Repeated customer emails<strong>{{ result.repeated_email_count }}</strong></div>
<div class="card bad">Rows belonging to repeated emails<strong>{{ result.repeated_rows }}</strong></div>
<div class="card good">Unique non-repeated customers<strong>{{ result.unique_non_repeated }}</strong></div>
<div class="card">Invalid email rows removed<strong>{{ result.invalid_emails }}</strong></div>
<div class="card">Groups found<strong>{{ result.group_count }}</strong></div>
<div class="card">Emails in more than one group<strong>{{ result.repeated_across_groups }}</strong></div>
<div class="card good">Double opt-in confirmed<strong>{{ result.double_opt_in }}</strong></div>
<div class="card bad">Missing DOI proof<strong>{{ result.missing_doi }}</strong></div>
</div>

<h2>Detected Columns</h2>
<div class="grid">
<div class="card">Newsletter column<strong>{{ result.newsletter_col }}</strong></div>
<div class="card">Group column<strong>{{ result.group_col }}</strong></div>
<div class="card">DOI column<strong>{{ result.doi_col }}</strong></div>
<div class="card">Consent timestamp<strong>{{ result.consent_time_col }}</strong></div>
<div class="card">Consent source<strong>{{ result.consent_source_col }}</strong></div>
</div>

<div class="notice">
For Brevo campaign sending, use only verified subscribers and still check: blocklist, unsubscribe, bounce, complaint, DOI, consent timestamp, and consent source.
</div>

<h2>Download Reports</h2>
<a class="btn" href="/download/{{ job_id }}/summary.csv">Summary</a>
<a class="btn" href="/download/{{ job_id }}/campaign_candidates_full_data.csv">Campaign Candidates Full Data</a>
<a class="btn" href="/download/{{ job_id }}/campaign_candidates_emails_only.csv">Campaign Emails Only</a>
<a class="btn" href="/download/{{ job_id }}/unique_customers_full_data.csv">Unique Customers Full Data</a>
<a class="btn" href="/download/{{ job_id }}/unique_non_repeated_customers.csv">Unique Non-Repeated Customers</a>
<a class="btn" href="/download/{{ job_id }}/duplicate_email_summary.csv">Duplicate Email Summary</a>
<a class="btn" href="/download/{{ job_id }}/duplicate_rows_full_data.csv">Duplicate Rows Full Data</a>
<a class="btn" href="/download/{{ job_id }}/group_breakdown.csv">Group Breakdown</a>
<a class="btn" href="/download/{{ job_id }}/emails_repeated_across_groups.csv">Emails Repeated Across Groups</a>
<a class="btn" href="/download/{{ job_id }}/group_membership_matrix.csv">Group Membership Matrix</a>
<a class="btn" href="/download/{{ job_id }}/missing_doi_or_consent_proof.csv">Missing DOI / Consent Proof</a>
<a class="btn" href="/">Analyze Again</a>

<h2>1. Group Breakdown</h2>
<div class="wrap">{{ group_table|safe }}</div>

<h2>2. Campaign Candidate Contacts</h2>
<p>Total shown: <b id="count_candidates">{{ result.subscribed_unique }}</b></p>
<input id="search_candidates" onkeyup="filterTable('search_candidates','table_candidates','count_candidates')" placeholder="Search candidates...">
<div class="wrap">{{ candidates_table|safe }}</div>

<h2>3. Campaign Emails Only</h2>
<p>Total shown: <b id="count_email_only">{{ result.subscribed_unique }}</b></p>
<input id="search_email_only" onkeyup="filterTable('search_email_only','table_email_only','count_email_only')" placeholder="Search email...">
<div class="wrap">{{ email_only_table|safe }}</div>

<h2>4. Duplicate Email Summary</h2>
<p>Total shown: <b id="count_dup">{{ result.repeated_email_count }}</b></p>
<input id="search_dup" onkeyup="filterTable('search_dup','table_dup','count_dup')" placeholder="Search duplicate email...">
<div class="wrap">{{ duplicate_summary_table|safe }}</div>

<h2>5. All Duplicate Rows</h2>
<p>Total shown: <b id="count_dup_rows">{{ result.repeated_rows }}</b></p>
<input id="search_dup_rows" onkeyup="filterTable('search_dup_rows','table_dup_rows','count_dup_rows')" placeholder="Search duplicate rows...">
<div class="wrap">{{ duplicate_rows_table|safe }}</div>

<h2>6. Emails Repeated Across Groups</h2>
<p>Total shown: <b id="count_group_repeat">{{ result.repeated_across_groups }}</b></p>
<input id="search_group_repeat" onkeyup="filterTable('search_group_repeat','table_group_repeat','count_group_repeat')" placeholder="Search repeated across groups...">
<div class="wrap">{{ group_repeat_table|safe }}</div>

<h2>7. Group Membership Matrix</h2>
<p>Total shown: <b id="count_matrix">{{ result.unique_customers }}</b></p>
<input id="search_matrix" onkeyup="filterTable('search_matrix','table_matrix','count_matrix')" placeholder="Search matrix...">
<div class="wrap">{{ group_matrix_table|safe }}</div>

<h2>8. Missing DOI / Consent Proof</h2>
<p>Total shown: <b id="count_missing_proof">{{ result.missing_doi }}</b></p>
<input id="search_missing_proof" onkeyup="filterTable('search_missing_proof','table_missing_proof','count_missing_proof')" placeholder="Search missing proof...">
<div class="wrap">{{ missing_proof_table|safe }}</div>

<h2>9. All Unique Customers</h2>
<p>Total shown: <b id="count_unique">{{ result.unique_customers }}</b></p>
<input id="search_unique" onkeyup="filterTable('search_unique','table_unique','count_unique')" placeholder="Search all unique customers...">
<div class="wrap">{{ unique_table|safe }}</div>

{% endif %}
</div>
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
    df.columns = [
        str(c).strip().lower().replace("\ufeff", "").replace("_", " ")
        for c in df.columns
    ]
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
        "doi confirmed", "doi_confirmed", "opted in", "opted_in", "ja", "y"
    ]


def has_value(value):
    return not (pd.isna(value) or str(value).strip() == "")


def find_col(df, candidates):
    normalized_candidates = [c.lower().replace("_", " ") for c in candidates]
    for c in df.columns:
        if c in normalized_candidates:
            return c
    return None


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
        or "subscriber" in v
        or "subscribed" in v
    )


def make_table(df, table_id, limit=30000):
    if df.empty:
        return f'<table id="{table_id}"><tr><th>No rows found</th></tr></table>'
    html = df.head(limit).fillna("").to_html(index=False, escape=True)
    return html.replace(
        '<table border="1" class="dataframe">',
        f'<table id="{table_id}">'
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML, result=None)

    uploaded_file = request.files.get("shopware_file")
    if not uploaded_file or uploaded_file.filename == "":
        return "No file uploaded"

    job_id = str(uuid.uuid4())
    job_dir = REPORT_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    filename = secure_filename(uploaded_file.filename)
    filename_lower = filename.lower()

    upload_path = UPLOAD_DIR / f"{job_id}_{filename}"
    uploaded_file.save(upload_path)

    df = normalize_columns(read_csv_auto(upload_path))

    if "email" not in df.columns:
        return f"CSV missing required column: email. Found columns: {list(df.columns)}"

    df["email_normalized"] = df["email"].apply(normalize_email)
    invalid_emails = int(df["email_normalized"].isna().sum())
    df = df[df["email_normalized"].notna()].copy()

    newsletter_col = find_col(df, [
        "newsletter",
        "subscribed",
        "email subscription status",
        "accepts email marketing",
        "accepts_email_marketing"
    ])

    group_col = find_col(df, [
        "group",
        "customer group",
        "customergroup",
        "tags"
    ])

    doi_col = find_col(df, [
        "doubleoptinconfirmed",
        "double optin confirmed",
        "double opt in confirmed",
        "double opt-in",
        "double opt in",
        "double_opt_in",
        "doi",
        "doi confirmed",
        "doi_confirmed"
    ])

    consent_time_col = find_col(df, [
        "consent timestamp",
        "consent time",
        "consent date",
        "opt in date",
        "optin date",
        "created at",
        "added"
    ])

    consent_source_col = find_col(df, [
        "consent source",
        "source",
        "opt in source",
        "optin source",
        "signup source"
    ])

    if newsletter_col:
        df["subscribed_by_newsletter_col"] = df[newsletter_col].apply(truthy)
        newsletter_label = newsletter_col
    else:
        df["subscribed_by_newsletter_col"] = False
        newsletter_label = "NOT FOUND"

    if group_col:
        df["group_clean"] = df[group_col].apply(safe_group_value)
        df["subscribed_by_group"] = df[group_col].apply(is_newsletter_group)
        group_label = group_col
    else:
        df["group_clean"] = "NO GROUP COLUMN"
        df["subscribed_by_group"] = False
        group_label = "NOT FOUND"

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
        doi_label = doi_col
    else:
        df["is_double_opt_in"] = False
        doi_label = "NOT FOUND"

    if consent_time_col:
        df["consent_timestamp_exists"] = df[consent_time_col].apply(has_value)
        consent_time_label = consent_time_col
    else:
        df["consent_timestamp_exists"] = False
        consent_time_label = "NOT FOUND"

    if consent_source_col:
        df["consent_source_exists"] = df[consent_source_col].apply(has_value)
        consent_source_label = consent_source_col
    else:
        df["consent_source_exists"] = False
        consent_source_label = "NOT FOUND"

    duplicate_rows = df[df.duplicated(subset=["email_normalized"], keep=False)].copy()

    duplicate_summary = (
        df.groupby("email_normalized")
        .agg(
            times_found=("email_normalized", "size"),
            groups=("group_clean", lambda x: " | ".join(sorted(set([g for g in x if g]))))
        )
        .reset_index()
        .sort_values("times_found", ascending=False)
    )
    duplicate_summary = duplicate_summary[duplicate_summary["times_found"] > 1]

    unique_customers = df.drop_duplicates(subset=["email_normalized"], keep="first").copy()
    unique_non_repeated = unique_customers[
        ~unique_customers["email_normalized"].isin(duplicate_summary["email_normalized"])
    ].copy()

    campaign_candidates = unique_customers[unique_customers["is_subscribed"] == True].copy()
    unsubscribed_unique = unique_customers[unique_customers["is_subscribed"] == False].copy()
    doi_confirmed = unique_customers[unique_customers["is_double_opt_in"] == True].copy()

    missing_doi_or_consent = campaign_candidates[
        (
            campaign_candidates["is_double_opt_in"] == False
        )
        | (
            campaign_candidates["consent_timestamp_exists"] == False
        )
        | (
            campaign_candidates["consent_source_exists"] == False
        )
    ].copy()

    email_only = campaign_candidates[["email_normalized"]].rename(
        columns={"email_normalized": "email"}
    )

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
    group_membership["groups_joined"] = group_membership["group_clean"].apply(
        lambda x: " | ".join(x)
    )

    group_repeat = group_membership[group_membership["groups_count"] > 1].copy()
    group_repeat = group_repeat.sort_values("groups_count", ascending=False)

    all_groups = sorted(
        set(g for groups in group_membership["group_clean"] for g in groups if g)
    )

    group_matrix = group_membership[
        ["email_normalized", "groups_count", "groups_joined"]
    ].copy()

    for g in all_groups:
        group_matrix[g] = group_membership["group_clean"].apply(
            lambda groups: "YES" if g in groups else ""
        )

    display_cols_preferred = [
        "email",
        "email_normalized",
        "group",
        "group_clean",
        "firstname",
        "lastname",
        "salutation",
        "street",
        "zipcode",
        "city",
        "customernumber",
        "newsletter",
        "doubleoptinconfirmed",
        "subscribed_by_newsletter_col",
        "subscribed_by_group",
        "subscribed_by_file_name",
        "is_subscribed",
        "is_double_opt_in",
        "consent_timestamp_exists",
        "consent_source_exists",
    ]

    def pick_cols(dataframe):
        cols = [c for c in display_cols_preferred if c in dataframe.columns]
        remaining = [c for c in dataframe.columns if c not in cols]
        return cols + remaining[:20]

    result = {
        "total_rows": int(len(df)),
        "unique_customers": int(unique_customers["email_normalized"].nunique()),
        "subscribed_unique": int(campaign_candidates["email_normalized"].nunique()),
        "unsubscribed_unique": int(unsubscribed_unique["email_normalized"].nunique()),
        "repeated_email_count": int(duplicate_summary["email_normalized"].nunique()),
        "repeated_rows": int(len(duplicate_rows)),
        "unique_non_repeated": int(unique_non_repeated["email_normalized"].nunique()),
        "invalid_emails": invalid_emails,
        "group_count": int(group_breakdown["group_clean"].nunique()),
        "repeated_across_groups": int(group_repeat["email_normalized"].nunique()),
        "double_opt_in": int(doi_confirmed["email_normalized"].nunique()),
        "missing_doi": int(missing_doi_or_consent["email_normalized"].nunique()),
        "newsletter_col": newsletter_label,
        "group_col": group_label,
        "doi_col": doi_label,
        "consent_time_col": consent_time_label,
        "consent_source_col": consent_source_label,
    }

    pd.DataFrame([result]).to_csv(job_dir / "summary.csv", index=False, encoding="utf-8-sig")
    unique_customers.to_csv(job_dir / "unique_customers_full_data.csv", index=False, encoding="utf-8-sig")
    unique_non_repeated.to_csv(job_dir / "unique_non_repeated_customers.csv", index=False, encoding="utf-8-sig")
    campaign_candidates.to_csv(job_dir / "campaign_candidates_full_data.csv", index=False, encoding="utf-8-sig")
    email_only.to_csv(job_dir / "campaign_candidates_emails_only.csv", index=False, encoding="utf-8-sig")
    duplicate_summary.to_csv(job_dir / "duplicate_email_summary.csv", index=False, encoding="utf-8-sig")
    duplicate_rows.to_csv(job_dir / "duplicate_rows_full_data.csv", index=False, encoding="utf-8-sig")
    group_breakdown.to_csv(job_dir / "group_breakdown.csv", index=False, encoding="utf-8-sig")
    group_repeat.to_csv(job_dir / "emails_repeated_across_groups.csv", index=False, encoding="utf-8-sig")
    group_matrix.to_csv(job_dir / "group_membership_matrix.csv", index=False, encoding="utf-8-sig")
    missing_doi_or_consent.to_csv(job_dir / "missing_doi_or_consent_proof.csv", index=False, encoding="utf-8-sig")

    return render_template_string(
        HTML,
        result=result,
        job_id=job_id,
        group_table=make_table(group_breakdown, "table_group"),
        candidates_table=make_table(campaign_candidates[pick_cols(campaign_candidates)], "table_candidates"),
        email_only_table=make_table(email_only, "table_email_only"),
        duplicate_summary_table=make_table(duplicate_summary, "table_dup"),
        duplicate_rows_table=make_table(duplicate_rows[pick_cols(duplicate_rows)], "table_dup_rows"),
        group_repeat_table=make_table(group_repeat, "table_group_repeat"),
        group_matrix_table=make_table(group_matrix, "table_matrix"),
        missing_proof_table=make_table(
            missing_doi_or_consent[pick_cols(missing_doi_or_consent)],
            "table_missing_proof"
        ),
        unique_table=make_table(unique_customers[pick_cols(unique_customers)], "table_unique"),
    )


@app.route("/download/<job_id>/<filename>")
def download_file(job_id, filename):
    file_path = REPORT_DIR / job_id / filename

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