import frappe

PRINT_FORMAT_NAME = "The Smart Start Hira Print"

HTML = r'''
{% set lh_doc = frappe.get_doc("Letter Head", doc.letter_head) if doc.letter_head else None %}
{% set lh_content = lh_doc.content if lh_doc and lh_doc.content else "" %}

<style>
    @media screen {
        .print-format {
            font-family: Arial, sans-serif;
            font-size: 11px;
            color: #000;
        }
    }

    @media print {
        @page {
            size: A4;
            margin-top: 12mm;
            margin-right: 10mm;
            margin-bottom: 35mm;
            margin-left: 10mm;
        }
    }

    .print-format {
        font-family: Arial, sans-serif;
        font-size: 11px;
        color: #000;
        line-height: 1.35;
    }

    .main-content {
        padding-bottom: 140px;
    }

    .letter-head-wrap {
        margin-bottom: 10px;
    }

    .notice-box {
        border: 1px solid #000;
        padding: 8px 10px;
        margin-bottom: 12px;
        font-weight: bold;
    }

    .section-title {
        font-weight: bold;
        margin: 10px 0 6px 0;
        font-size: 12px;
    }

    .meta-table,
    .hira-table,
    .sign-table,
    .footer-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    .meta-table td,
    .meta-table th,
    .hira-table td,
    .hira-table th,
    .sign-table td,
    .sign-table th,
    .footer-table td,
    .footer-table th {
        border: 1px solid #000;
        padding: 4px 6px;
        vertical-align: top;
        word-wrap: break-word;
    }

    .meta-table th,
    .hira-table th,
    .sign-table th,
    .footer-table th {
        text-align: center;
        font-weight: bold;
    }

    .large-box {
        min-height: 60px;
    }

    .footer-wrap {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100%;
        padding: 0 10mm 0 10mm;
        box-sizing: border-box;
        background: #fff;
    }

    .footer-table th,
    .footer-table td {
        text-align: center;
        padding: 3px 6px;
    }

    .footer-note {
        margin-top: 4px;
        font-size: 10px;
        line-height: 1.25;
        text-transform: uppercase;
    }

    .small-text {
        font-size: 10px;
    }

    .center {
        text-align: center;
    }
</style>

<div class="print-format">

    <div class="main-content">

        {% if lh_content %}
        <div class="letter-head-wrap">
            {{ lh_content }}
        </div>
        {% endif %}

        <div class="notice-box">
            NB: THE SMART START HIRA must be led by the most senior person in the team, but every team member must participate in the identification of hazards and controls. The identified hazards and controls must be communicated by the person leading the team to all team members including anyone who come to the area after the HIRA is completed and was not part of the discussion.<br><br>
            If anything changes during the shift apply the SLAM - STOP-LOOK-ASSESS-MANAGE
        </div>

        <table class="meta-table">
            <tr>
                <td style="width: 18%;"><b>Company</b></td>
                <td style="width: 32%;">{{ doc.company or "" }}</td>
                <td style="width: 18%;"><b>Date</b></td>
                <td style="width: 32%;">{{ frappe.utils.formatdate(doc.date) if doc.date else "" }}</td>
            </tr>
            <tr>
                <td><b>Time</b></td>
                <td>{{ doc.time or "" }}</td>
                <td><b>Site</b></td>
                <td>{{ doc.site or "" }}</td>
            </tr>
            <tr>
                <td><b>Working Area</b></td>
                <td>{{ doc.working_area or "" }}</td>
                <td><b>Letter Head</b></td>
                <td>{{ doc.letter_head or "" }}</td>
            </tr>
            <tr>
                <td><b>Job Description</b></td>
                <td colspan="3">{{ doc.job_description or "" }}</td>
            </tr>
            <tr>
                <td><b>Name of Person Leading the HIRA</b></td>
                <td>{{ doc.person_leading_hira or "" }}</td>
                <td><b>Occupation</b></td>
                <td>{{ doc.occupation or "" }}</td>
            </tr>
            <tr>
                <td><b>Signature</b></td>
                <td colspan="3">
                    {% if doc.leader_signature %}
                        <img src="{{ doc.leader_signature }}" style="max-height:40px;">
                    {% endif %}
                </td>
            </tr>
        </table>

        <div class="section-title">
            List all the relevant hazards and risks applicable to the task you are going to perform and identify controls and verify that it is safe before commencing work.
        </div>

        <table class="hira-table">
            <tr>
                <th style="width: 33%;">HAZARD<br><span class="small-text">(What is Unsafe?)</span></th>
                <th style="width: 27%;">Risk<br><span class="small-text">(What can go wrong?)</span></th>
                <th style="width: 40%;">Controls</th>
            </tr>
            {% if doc.hazards_and_controls and doc.hazards_and_controls|length > 0 %}
                {% for row in doc.hazards_and_controls %}
                <tr>
                    <td>{{ row.hazard or "" }}</td>
                    <td>{{ row.risk or "" }}</td>
                    <td>{{ row.controls or "" }}</td>
                </tr>
                {% endfor %}
            {% else %}
                {% for i in range(10) %}
                <tr>
                    <td style="height: 28px;"></td>
                    <td></td>
                    <td></td>
                </tr>
                {% endfor %}
            {% endif %}
        </table>

        <div class="section-title">Team Members</div>

        <table class="sign-table">
            <tr>
                <th>Name &amp; Surname</th>
                <th>Occupation</th>
                <th>Signature</th>
                <th>Name &amp; Surname</th>
                <th>Occupation</th>
                <th>Signature</th>
            </tr>

            {% set members = doc.team_members or [] %}
            {% for i in range(0, 10, 2) %}
            <tr>
                <td>
                    {% if members|length > i %}
                        {{ members[i].full_name or "" }}
                    {% endif %}
                </td>
                <td>
                    {% if members|length > i %}
                        {{ members[i].occupation or "" }}
                    {% endif %}
                </td>
                <td class="center">
                    {% if members|length > i and members[i].signature %}
                        <img src="{{ members[i].signature }}" style="max-height:35px; max-width:100%;">
                    {% endif %}
                </td>
                <td>
                    {% if members|length > i + 1 %}
                        {{ members[i + 1].full_name or "" }}
                    {% endif %}
                </td>
                <td>
                    {% if members|length > i + 1 %}
                        {{ members[i + 1].occupation or "" }}
                    {% endif %}
                </td>
                <td class="center">
                    {% if members|length > i + 1 and members[i + 1].signature %}
                        <img src="{{ members[i + 1].signature }}" style="max-height:35px; max-width:100%;">
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>

        <div class="section-title">Counter Signing by Supervisor</div>

        <table class="meta-table">
            <tr>
                <td style="width: 16%;"><b>Name</b></td>
                <td style="width: 34%;">{{ doc.supervisor_name or "" }}</td>
                <td style="width: 16%;"><b>Occupation</b></td>
                <td style="width: 34%;">{{ doc.supervisor_occupation or "" }}</td>
            </tr>
            <tr>
                <td><b>Date</b></td>
                <td>{{ frappe.utils.formatdate(doc.supervisor_date) if doc.supervisor_date else "" }}</td>
                <td><b>Signature</b></td>
                <td>
                    {% if doc.supervisor_signature %}
                        <img src="{{ doc.supervisor_signature }}" style="max-height:40px;">
                    {% endif %}
                </td>
            </tr>
        </table>

        <div style="margin-top:10px;" class="small-text">
            <b>NB:</b> All the HIRA's must be handed to the responsible Supervisor at the end of the shift. These shall be kept as part of the supervisor's compliance file.
        </div>

        <div class="section-title">List the PPE if it is not contained above</div>
        <table class="meta-table">
            <tr>
                <td class="large-box">{{ doc.additional_ppe or "" }}</td>
            </tr>
        </table>

        <div class="section-title">Write down the hazard if it is not listed above</div>
        <table class="meta-table">
            <tr>
                <td class="large-box">{{ doc.additional_hazards or "" }}</td>
            </tr>
        </table>

    </div>

    <div class="footer-wrap">
        <table class="footer-table">
            <tr>
                <th>DOCUMENT NO.</th>
                <th>REVISION</th>
                <th>EFFECTIVE DATE</th>
                <th>PAGE</th>
            </tr>
            <tr>
                <td>{{ doc.document_no or "IS-SHEQ-DT-SMART-068" }}</td>
                <td>{{ doc.revision or "1.0" }}</td>
                <td>
                    {% if doc.effective_date %}
                        {{ frappe.utils.formatdate(doc.effective_date, "dd.MM.yyyy") }}
                    {% else %}
                        31.03.2026
                    {% endif %}
                </td>
                <td>Page <span class="page"></span> of <span class="topage"></span></td>
            </tr>
        </table>

        <div class="footer-note">
            THIS DOCUMENT IS THE PROPERTY OF ISAMBANE MINING AND IS CONFIDENTIAL. IT MAY NOT BE COPIED OR DIVULGED TO 3RD PARTIES WITHOUT PERMISSION.
        </div>
    </div>

</div>
'''

def run():
    if not frappe.db.exists("DocType", "The Smart Start Hira"):
        raise Exception("DocType 'The Smart Start Hira' does not exist yet.")

    existing_name = frappe.db.exists("Print Format", PRINT_FORMAT_NAME)

    if existing_name:
        pf = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
    else:
        pf = frappe.new_doc("Print Format")
        pf.name = PRINT_FORMAT_NAME

    pf.doc_type = "The Smart Start Hira"
    pf.module = "Safety"
    pf.print_format_type = "Jinja"
    pf.custom_format = 1
    pf.raw_printing = 0
    pf.disabled = 0
    pf.html = HTML

    if existing_name:
        pf.save(ignore_permissions=True)
        message = f"Updated Print Format: {PRINT_FORMAT_NAME}"
    else:
        pf.insert(ignore_permissions=True)
        message = f"Created Print Format: {PRINT_FORMAT_NAME}"

    frappe.db.commit()
    print(message)