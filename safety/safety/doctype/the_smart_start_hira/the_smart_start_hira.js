const PPE_REQUIRED_IMAGE = "/files/PPE.jpeg";
const HAZARD_IDENTIFICATION_IMAGE = "/files/WhatsApp Image 2026-04-28 at 1.12.22 PM.jpeg";

frappe.ui.form.on("The Smart Start Hira", {
    refresh: function(frm) {
        render_smart_start_notice(frm);
        render_supervisor_note(frm);
        render_ppe_equipment_reference(frm);
        render_hazard_identification_picture(frm);

        if (frm.doc.company && !frm.doc.letter_head) {
            set_letter_head_from_company(frm);
        }
    },

    company: function(frm) {
        if (!frm.doc.company) {
            frm.set_value("letter_head", "");
            return;
        }

        set_letter_head_from_company(frm);
    }
});

function set_letter_head_from_company(frm) {
    frappe.db.get_value("Company", frm.doc.company, "default_letter_head")
        .then(r => {
            if (r && r.message) {
                frm.set_value("letter_head", r.message.default_letter_head || "");
            }
        });
}

function render_smart_start_notice(frm) {
    frm.get_field("smart_start_notice_html").$wrapper.html(`
        <div style="padding: 12px; background: #fff8e1; border: 1px solid #e2d39b; border-radius: 6px; font-weight: 600; line-height: 1.6;">
            <p style="margin: 0 0 8px 0;">
                NB: THE SMART START HIRA must be led by the most senior person in the team, but every team member must participate in the identification of hazards and controls.
            </p>
            <p style="margin: 0 0 8px 0;">
                The identified hazards and controls must be communicated by the person leading the team to all team members including anyone who come to the area after the HIRA is completed and was not part of the discussion.
            </p>
            <p style="margin: 0;">
                If anything changes during the shift apply the SLAM - STOP-LOOK-ASSESS-MANAGE
            </p>
        </div>
    `);
}

function render_supervisor_note(frm) {
    frm.get_field("supervisor_note_html").$wrapper.html(`
        <div style="margin-top: 8px; padding: 10px 12px; background: #fff8e1; border: 1px solid #d6c37a; border-radius: 6px; line-height: 1.5; font-weight: 600;">
            NB: All the HIRA's must be handed to the responsible Supervisor at the end of the shift. These shall be kept as part of the supervisor's compliance file.
        </div>
    `);
}


function render_ppe_equipment_reference(frm) {
    const field = frm.get_field("ppe_equipment_reference_html");

    if (!field || !field.$wrapper) {
        return;
    }

    field.$wrapper.html(`
        <div style="margin-top: 12px;">
            <img
                src="${PPE_REQUIRED_IMAGE}"
                alt="PPE Required for the task"
                style="display: block; width: 100%; max-width: 980px; height: auto; border: 1px solid #444; background: #fff;"
            />
        </div>
    `);
}

function equipmentItem(label) {
    return `
        <div style="display: flex; align-items: center; gap: 8px; min-height: 24px;">
            <span style="display: inline-block; width: 20px; height: 20px; border: 2px solid #444; background: #fff;"></span>
            <span style="font-size: 14px;">${label}</span>
        </div>
    `;
}

function ppeItem(label) {
    return `
        <div style="border: 1px solid #666; background: #efefef; text-align: center; min-height: 116px; display: flex; flex-direction: column; justify-content: flex-start;">
            <div style="padding: 6px 4px 2px 4px; font-size: 13px; min-height: 34px;">${label}</div>
            <div style="display: flex; justify-content: center; align-items: center; padding: 4px 0 10px 0;">
                <div style="width: 52px; height: 52px; border-radius: 50%; background: #1736d1; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; font-weight: 700;">
                    ✓
                </div>
            </div>
        </div>
    `;
}


function render_hazard_identification_picture(frm) {
    const field = frm.get_field("hazard_identification_picture_html");

    if (!field || !field.$wrapper) {
        return;
    }

    field.$wrapper.html(`
        <div style="margin-top: 12px; padding: 10px; border: 1px solid #9a9a9a; background: #f7f7f7;">
            <div style="font-weight: 700; font-size: 16px; margin-bottom: 8px;">
                Identify the hazards applicable to the task:
            </div>
            <img
                src="${HAZARD_IDENTIFICATION_IMAGE}"
                alt="Identify the hazards applicable to the task"
                style="display: block; width: 100%; max-width: 980px; height: auto; border: 1px solid #444; background: #fff;"
            />
        </div>
    `);
}

