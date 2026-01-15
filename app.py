# --- All imports and setup ---
import streamlit as st
import pandas as pd
import smtplib, os, json
from email.message import EmailMessage
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib.parse

st.set_page_config("📧 Email Campaign App", layout="wide")

# --- Folders ---
os.makedirs("campaign_results", exist_ok=True)

# --- Email HTML Generator ---
def generate_email_html(
    full_name,
    recipient_email=None,
    subject=None,
    custom_html=None,
    cta_text="🎟️ Book My Ticket Now",
    cta_url="#"
):
    email_for_tracking = recipient_email or "unknown@example.com"
    encoded_subject = urllib.parse.quote(subject or "No Subject", safe="")
    encoded_cta_url = urllib.parse.quote(cta_url, safe="")

    tracking_link = (
        f"https://tracking-enfw.onrender.com/track/click"
        f"?email={email_for_tracking}&url={encoded_cta_url}&subject={encoded_subject}"
    )

    tracking_pixel = (
        f'<img src="https://tracking-enfw.onrender.com/track/open'
        f'?email={email_for_tracking}&subject={encoded_subject}" '
        f'width="1" height="1" '
        f'style="display:none!important;opacity:0;max-height:0;overflow:hidden;" '
        f'alt="" />'
    )

    unsubscribe_link = (
        f"https://unsubscribe-uofn.onrender.com/unsubscribe?email={email_for_tracking}"
    )

    custom_html_rendered = custom_html.replace("{name}", full_name or "")

    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f9f9f9;font-family:Arial;">
    {tracking_pixel}

    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding:30px">
          <table width="100%" style="max-width:700px;background:#fff;
            border-radius:10px;box-shadow:0 4px 14px rgba(0,0,0,.07)">
            <tr>
              <td style="padding:30px">

                {custom_html_rendered}

                <!-- LEFT ALIGNED CTA -->
                <table style="margin-top:30px">
                  <tr>
                    <td bgcolor="#D7262F" style="border-radius:6px">
                      <a href="{tracking_link}" target="_blank"
                        style="display:inline-block;padding:16px 28px;
                        font-size:15px;color:#fff;text-decoration:none;
                        font-weight:bold;border-radius:6px;">
                        {cta_text}
                      </a>
                    </td>
                  </tr>
                </table>

                <p style="margin-top:25px;font-weight:bold">
                  Regards<br/>
                  Customer Success Team<br/>
                  Corporate Wellbeing Expo</br>
                  3–4 March 2026 | London Olympia<br/>
                  <br/>
                  On Behalf of<br/>
                  Andrew<br/>
                  Show Director<br/>
                  <a href="mailto:andrew@corporatewellbeingexpo.com"
                     style="color:#D7262F">andrew@corporatewellbeingexpo.com</a><br/>
                  
                </p>

                <p style="font-size:11px;color:#888;margin-top:30px">
                  <a href="{unsubscribe_link}" style="color:#D7262F">Unsubscribe</a>
                </p>

              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    </body>
    </html>
    """

# --- Send Email ---
def send_email(sender_email, sender_password, row, subject, custom_html, cta_text, cta_url):
    try:
        server = smtplib.SMTP("mail.corporatewellbeingexpo.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = row["email"]
        msg["Subject"] = subject

        html = generate_email_html(
            row["full_name"],
            row["email"],
            subject,
            custom_html,
            cta_text,
            cta_url
        )

        msg.set_content(html, subtype="html")
        server.send_message(msg)
        server.quit()

        return (row["email"], "✅ Delivered")
    except Exception as e:
        return (row["email"], f"❌ Failed: {e}")

# --- Send Delivery Report ---
def send_delivery_report(sender_email, sender_password, report_file):
    msg = EmailMessage()
    msg["Subject"] = "Delivery Report – Email Campaign"
    msg["From"] = sender_email
    msg["To"] = "b2bgrowthexpo@gmail.com"
    msg.set_content("Attached is the delivery report for the email campaign.")

    with open(report_file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="octet-stream",
            filename=os.path.basename(report_file)
        )

    server = smtplib.SMTP("mail.corporatewellbeingexpo.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()

# --- UI ---
st.title("📨 Automated Email Campaign Manager")

sender_email = st.text_input("Sender Email", value="andrew@corporatewellbeingexpo.com")
sender_password = st.text_input("Password", type="password")
subject = st.text_input("Email Subject")

st.subheader("🔘 CTA Button Settings")
cta_text = st.text_input("Button Text", value="🎟️ Book My Ticket Now")
cta_url = st.text_input("Button URL", value="https://www.eventbrite.com/")

from streamlit_quill import st_quill
st.subheader("📝 Email Content")
custom_html = st_quill(html=True)

campaign_name = st.text_input("Campaign Name")
file = st.file_uploader("Upload CSV (`email`, `full name`)")

st.subheader("📧 Preview")
st.components.v1.html(
    generate_email_html(
        "Sarah Johnson",
        subject=subject,
        custom_html=custom_html,
        cta_text=cta_text,
        cta_url=cta_url
    ),
    height=600,
    scrolling=True
)

# --- Campaign Run ---
if st.button("🚀 Start Campaign"):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower().str.strip()
    df.rename(columns={"full name": "full_name"}, inplace=True)

    delivery_report = []
    delivered, failed = 0, 0
    progress = st.progress(0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(
                send_email,
                sender_email,
                sender_password,
                row,
                subject,
                custom_html,
                cta_text,
                cta_url
            )
            for _, row in df.iterrows()
        ]

        for i, future in enumerate(futures):
            email, result = future.result()
            delivery_report.append({"email": email, "status": result})
            delivered += "✅" in result
            failed += "❌" in result
            progress.progress((i + 1) / len(df))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_df = pd.DataFrame(delivery_report)
    report_file = f"campaign_results/report_{campaign_name}_{timestamp}.csv"
    report_df.to_csv(report_file, index=False)

    st.success("✅ Campaign Completed")
    st.metric("Delivered", delivered)
    st.metric("Failed", failed)

    st.download_button(
        "📥 Download Delivery Report",
        data=report_df.to_csv(index=False),
        file_name=os.path.basename(report_file),
        mime="text/csv"
    )

    send_delivery_report(sender_email, sender_password, report_file)
