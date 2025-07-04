def email_crm_gmail_run():
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    import time
    from dotenv import load_dotenv
    from pathlib import Path


    def personalize_text(template: str, row: pd.Series, sender_name: str) -> str:
        text = template.replace("[Sender Name]", sender_name)
        for col in row.index:
            placeholder = f"[{col}]"
            if placeholder in text:
                text = text.replace(placeholder, str(row[col]))
        return text

    # ----------------- PAGE CONFIG -----------------
    st.set_page_config(layout="wide", page_title="📧 Inline Email CRM")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXCEL_PATH = os.path.join(BASE_DIR, "All_Contacts_Updated.xlsx")
    GMAIL_PASS_PATH = os.path.join(BASE_DIR, "gmail_passkey.txt")
    
    # st.write("Excel Path:", EXCEL_PATH)
    # st.write("File Exists:", os.path.exists(EXCEL_PATH))

    # ----------------- LOAD CONTACTS -----------------
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Excel file not found at:\n{EXCEL_PATH}")
        st.stop()

    try:
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()


    # ----------------- AGGRID SETUP -----------------
    with st.expander("Select Contacts", expanded=False):
    #    st.subheader("📝 Edit Contacts")

        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_default_column(
            filter=True,
            editable=True,
            resizable=True,
            sortable=True,
            suppressMovable=False,
            hide = True
        )
        gb.configure_selection("multiple", use_checkbox=True)
        gb.configure_grid_options(
            domLayout='normal',
            rowHeight=40,
            sideBar=True,
            suppressMovableColumns=False,
            rowSelection='multiple',
        )

        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            height=500,
            enable_enterprise_modules=True
        )

        edited_df = grid_response["data"]
        selected_rows = pd.DataFrame(grid_response["selected_rows"])

        # ----------------- SELECT ALL BUTTON -----------------
        if st.button("🔘 Select All (Filtered Rows)"):
            st.session_state["select_all"] = edited_df.to_dict("records")
            st.success("All filtered rows selected!")

        if not selected_rows.empty:
            st.subheader("✅ Selected Contacts")
            st.dataframe(selected_rows)
        elif "select_all" in st.session_state:
            selected_rows = pd.DataFrame(st.session_state["select_all"])
            st.subheader("✅ All Filtered Contacts Selected")
            st.dataframe(selected_rows)

        # ----------------- SAVE CHANGES BUTTON -----------------
        if st.button("💾 Save Changes to Excel"):
            try:
                edited_df.to_excel(EXCEL_PATH, index=False)
                st.success("✅ Changes saved successfully.")
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

        # ----------------- EMAIL CONFIG -----------------
    # st.subheader("✉️ Email Configuration")

    with st.expander("Email Settings"):
        sender_name = st.text_input("Sender Name", placeholder="Chintan Thakkar")
        env_path = Path(__file__).resolve().parent.parent / '.env'
        # Step 2: Load the .env file
        load_dotenv(dotenv_path=env_path)

        # Define senders with correct SMTP & password file
        smtp_settings = {
            "Gmail": {
                "email": "professionalbuzz@gmail.com",
                "smtp_server": "smtp.gmail.com",
                "port": 587,
                "pass":os.getenv("GMAIL")
            },
            "Fintellect": {
                "email": "hello@fintellect.co.in",
                "smtp_server": "smtpout.secureserver.net",
                "port": 587,
                "pass":os.getenv("GODADDY")
            },
            "Outreach": {
                "email": "info@chintanthakkar.com",
                "smtp_server": "mail.chintanthakkar.com",
                "port": 587,
                "pass":os.getenv("CPANEL")
            }
        }

        # Select sender
        sender_choice = st.selectbox("Select Sender Email", list(smtp_settings.keys()))
        sender_config = smtp_settings[sender_choice]

        sender_email = sender_config["email"]
        smtp_server = sender_config["smtp_server"]
        smtp_port = sender_config["port"]
        sender_password = sender_config["pass"]

        st.info(f"Using sender: {sender_email}")

        # Load password
        if not sender_password:
            sender_password = st.text_input("Enter Email Password", type="password")

        # Email content
        subject = st.text_input("Subject (use [Name], [Sender Name])")
        body = st.text_area("Email Body (use [Name], [Sender Name])", height=200)

        # File attachment
        st.subheader("📎 Attachment (Optional)")
        attachment = st.file_uploader("Upload a file to attach", type=None)

        # Send button
        send_button = st.button("📨 Send Email to Selected Contacts")

    # ----------------- SEND EMAIL -----------------
    if send_button:
        if selected_rows.empty:
            st.warning("⚠️ No contacts selected.")
        elif not sender_email or not sender_password or not subject or not body:
            st.warning("⚠️ Please fill in all required fields.")
        else:
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, sender_password)
                

                progress = st.progress(0)
                total = len(selected_rows)
                email_log_entries = []

                for i, row in enumerate(selected_rows.itertuples(index=False)):
                    recipient_email = getattr(row, 'Email', '')
                    recipient_name = getattr(row, 'Name', 'there')

                    if not recipient_email:
                        st.error(f"❌ Missing email for {recipient_name}")
                        continue

                    # personalized_subject = subject.replace("[Name]", recipient_name).replace("[Sender Name]", sender_name)
                    # personalized_body = body.replace("[Name]", recipient_name).replace("[Sender Name]", sender_name)
                    # replaced above two lines with below three lines
                    row_data = pd.Series(row._asdict())
                    personalized_subject = personalize_text(subject, row_data, sender_name)
                    personalized_body = personalize_text(body, row_data, sender_name)
                    
                    msg = MIMEMultipart()
                    msg['From'] = f"{sender_name} <{sender_email}>"
                    msg['To'] = recipient_email
                    msg['Subject'] = personalized_subject
                    msg.attach(MIMEText(personalized_body, 'plain'))

                    attachment_name = ""
                    if attachment:
                        attachment_name = attachment.name
                        msg.attach(MIMEText(attachment.read(), "base64", "utf-8"))
                        msg.get_payload()[-1].add_header(
                            'Content-Disposition',
                            f'attachment; filename="{attachment.name}"'
                        )

                    try:
                        server.sendmail(sender_email, recipient_email, msg.as_string())
                        st.success(f"✅ Email sent to {recipient_name} ({recipient_email})")

                        # --- Update "Last emailed" ---
                        timestamp = pd.Timestamp.now().strftime("%d %b %Y %H:%M:%S")

                        # Find the matching row in edited_df using Email
                        match_index = edited_df[edited_df['Email'] == recipient_email].index

                        if not match_index.empty:
                            edited_df.at[match_index[0], 'Last emailed'] = timestamp
                        # --- Sanitized Log entry ---
                        sanitized_body = personalized_body.replace("\n", " ").replace("\r", " ").strip()
                        email_log_entries.append({
                            "timestamp": timestamp,
                            "recipient_name": recipient_name,
                            "recipient_email": recipient_email,
                            "subject": personalized_subject,
                            "body": sanitized_body,
                            "attachment": attachment_name if attachment_name else None
                        })
                    except Exception as e:
                        st.error(f"❌ Failed for {recipient_name} ({recipient_email}): {e}")

                    progress.progress((i + 1) / total)
                    time.sleep(1)

                server.quit()

                # --- Save updated sheet ---
                edited_df.to_excel(EXCEL_PATH, index=False)
                if email_log_entries:
                    with open(r"D:\Streamlit multi-app setup\EmailCrm\email_log.txt", "a", encoding="utf-8") as f:
                        for entry in email_log_entries:
                            log_entry = (
                                f"[{entry['timestamp']}]\n"
                                f"To: {entry['recipient_name']} <{entry['recipient_email']}>\n"
                                f"Subject: {entry['subject']}\n"
                                f"Body: {entry['body']}\n"
                                f"Attachment: {entry['attachment'] if entry['attachment'] else 'None'}\n"
                                + "-" * 60 + "\n"
                            )
                            f.write(log_entry)
                else:
                    st.info("ℹ️ No email log entries to write.")
                st.balloons()
                st.success("📬 All emails processed and logged.")

            except smtplib.SMTPAuthenticationError:
                st.error("❌ SMTP login failed. Check email and app password.")
            except Exception as e:
                st.error(f"❌ Error: {e}")