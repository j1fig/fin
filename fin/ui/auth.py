import streamlit as st
from fin import config


def render_login_form():
    """Render the login form and handle authentication."""
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1>🔐 Fin Login</h1>
        <p>Please enter your credentials to access your personal finance tracker</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Login")
            
            username = st.text_input(
                "Username", 
                placeholder="Enter your username",
                help="Enter your username"
            )
            
            password = st.text_input(
                "Password", 
                type="password",
                placeholder="Enter your password",
                help="Enter your password"
            )
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
                    

def authenticate_user(username: str, password: str) -> bool:
    """Validate user credentials against config."""
    cfg = config.get_config()
    
    return (
        username.strip() == cfg["USERNAME"].strip() and 
        password.strip() == cfg["PASSWORD"].strip()
    )


def is_authenticated() -> bool:
    """Check if user is authenticated in the current session."""
    return st.session_state.get("authenticated", False)


def logout():
    """Clear authentication from session state."""
    if "authenticated" in st.session_state:
        del st.session_state["authenticated"]
    if "username" in st.session_state:
        del st.session_state["username"]


def render_logout_button():
    """Render logout button in sidebar."""
    if st.sidebar.button("🚪 Logout", help="Click to logout and return to login screen"):
        logout()
        st.rerun() 