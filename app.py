import streamlit as st

st.set_page_config(page_title="CRM", page_icon="📇", layout="wide")

from crm import config, db, services  # noqa: E402
from crm.security import can  # noqa: E402
from views import accounts, activities, admin, contacts, dashboard, deals  # noqa: E402


@st.cache_resource
def _init_db() -> bool:
    db.configure(config.database_url())
    return True


def authenticate():
    if config.sso_configured():
        if not st.user.is_logged_in:
            st.title("📇 CRM")
            st.write("Sign in with your company account to continue.")
            st.button("Sign in with SSO", on_click=st.login, type="primary")
            st.stop()
        email = (st.user.email or "").lower()
        name = st.user.get("name") or email
        domains = config.allowed_domains()
        if domains and email.split("@")[-1] not in domains:
            st.error(f"{email} is not in an allowed domain.")
            st.button("Sign out", on_click=st.logout)
            st.stop()
    elif config.demo_mode():
        st.sidebar.warning("Demo mode: SSO not configured")
        email = st.sidebar.text_input("Demo email", "demo@example.com").lower()
        name = "Demo User"
    else:
        st.error("Authentication is not configured. Add an [auth] section to secrets (see README).")
        st.stop()

    user = services.get_or_create_user(email, name, config.admin_emails())
    if not user.active:
        st.error("Your account has been deactivated. Contact an administrator.")
        st.stop()
    return user


_init_db()
user = authenticate()

pages = [
    st.Page(lambda: dashboard.render(user), title="Dashboard", icon="📊", url_path="dashboard", default=True),
    st.Page(lambda: accounts.render(user), title="Accounts", icon="🏢", url_path="accounts"),
    st.Page(lambda: contacts.render(user), title="Contacts", icon="👤", url_path="contacts"),
    st.Page(lambda: deals.render(user), title="Deals", icon="💼", url_path="deals"),
    st.Page(lambda: activities.render(user), title="Activities", icon="✅", url_path="activities"),
]
if can(user, "admin"):
    pages.append(st.Page(lambda: admin.render(user), title="Admin", icon="🛡️", url_path="admin"))

st.sidebar.caption(f"{user.name} · {user.role}")
if config.sso_configured():
    st.sidebar.button("Sign out", on_click=st.logout)

st.navigation(pages).run()
