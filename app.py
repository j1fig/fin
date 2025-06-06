"""
Main Streamlit application entry point.
"""
import streamlit as st
from fin.ui import components, charts, auth, analytics, categorization
from fin import config, service, db


def main():
    """Main application entry point."""
    db.migrate()

    # Configure page
    st.set_page_config(
        page_title="Fin - Personal Finance Tracker",
        page_icon="💰",
        layout="wide"
    )

    cfg = config.get_config()

    # Check authentication for non-dev environments
    if cfg["ENV"] != "dev" and not auth.is_authenticated():
        auth.render_login_form()
        return
    
    # Main application (only shown when authenticated or in dev mode)
    render_main_app()


def render_main_app():
    """Render the main application interface."""
    cfg = config.get_config()
    
    # Sidebar navigation
    st.sidebar.title("Fin")
    st.sidebar.subheader("your personal finance tracker")
    
    # Show current user and logout button (only in non-dev mode)
    if cfg["ENV"] != "dev":
        username = st.session_state.get("username", "Unknown")
        st.sidebar.write(f"👤 Logged in as: **{username}**")
        auth.render_logout_button()
        st.sidebar.divider()
    
    selected_tab = st.sidebar.selectbox(
        "Choose a section:",
        ["📊 Overview", "📈 Analytics", "📁 Import Data", "🏷️ Category Management"]
    )
    
    # Route to appropriate tab
    match selected_tab:
        case "📊 Overview":
            render_overview_tab()
        case "📈 Analytics":
            analytics.render_analytics_tab()
        case "📁 Import Data":
            render_import_tab()
        case "🏷️ Category Management":
            render_category_management_tab()


def render_overview_tab():
    """Render the main overview with transactions and charts."""
    st.header("Financial Overview")
    
    # Main data analysis section
    accounts_df = charts.render_accounts_table()
    if not accounts_df.empty:
        account_id, selected_category, category_options = components.render_filter_controls(accounts_df)
        query, params = charts.build_transaction_query(account_id, selected_category, category_options)
        
        # Two columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            charts.render_transactions_table(query, params)
        
        with col2:
            charts.render_expenses_income_chart(query, params)
    else:
        st.info("No accounts found. Please import data first.")


def render_import_tab():
    """Render the data import section."""
    st.header("📁 Import Transaction Data")
    
    # Create tabs for different import methods
    tab1, tab2, tab3 = st.tabs(["🏦 CGD Import", "💳 Moey Import", "✍️ Manual Entry"])
    
    with tab1:
        render_cgd_import()
    
    with tab2:
        render_moey_import()
    
    with tab3:
        render_manual_transaction_entry()


def render_cgd_import():
    """Render CGD import interface."""
    st.subheader("🏦 CGD Bank Statement Import")
    st.write("Upload your CGD transaction file to import your bank statements:")
    
    uploaded_file = st.file_uploader(
        "Choose a CGD transactions file", 
        type="tsv",
        help="Select a .tsv file exported from CGD bank",
        key="cgd_upload"
    )
    
    if uploaded_file:
        try:
            service.import_cgd_transactions(uploaded_file)
            st.success("CGD transactions imported successfully!")
        except ValueError as e:
            st.error(f"Error importing CGD transactions: {e}")
    
    # Instructions
    st.subheader("How to export from CGD")
    with st.expander("Click for instructions"):
        st.markdown("""
        1. Log into your CGD online banking
        2. Go to Account History/Movements
        3. Select your date range
        4. Export as TSV/Tab-separated format
        5. Upload the file here
        """)


def render_moey_import():
    """Render Moey import interface."""
    st.subheader("💳 Moey Statement Import")
    st.write("Upload your Moey PDF statement to import your transactions:")
    
    uploaded_files = st.file_uploader(
        "Choose a Moey PDF statement", 
        type="pdf",
        help="Select a PDF statement from Moey bank",
        key="moey_upload",
        accept_multiple_files=True,
    )
    
    for uploaded_file in uploaded_files:
        try:
            service.import_moey_transactions(uploaded_file)
            st.success("Moey transactions imported successfully!")
        except ValueError as e:
            st.error(f"Error importing Moey transactions: {e}")
    
    # Instructions
    st.subheader("How to download from Moey")
    with st.expander("Click for instructions"):
        st.markdown("""
        1. Log into your Moey app or website
        2. Go to Account Statements
        3. Select your desired month/period
        4. Download the PDF statement
        5. Upload the file here
        """)


def render_manual_transaction_entry():
    """Render manual transaction entry form."""
    st.subheader("✍️ Manual Transaction Entry")
    st.write("Add individual transactions manually:")
    
    # Get available accounts and categories
    try:
        accounts = service.get_all_accounts()
        categories = service.get_categories_for_management()
        
        if not accounts:
            st.warning("⚠️ No accounts found. Please import data first or contact support.")
            return
            
        with st.form("manual_transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_date = st.date_input(
                    "Transaction Date",
                    help="When did this transaction occur?"
                )
                
                description = st.text_input(
                    "Description",
                    placeholder="e.g., Coffee at Starbucks",
                    help="Brief description of the transaction"
                )
                
            with col2:
                amount = st.number_input(
                    "Amount (€)",
                    step=0.01,
                    format="%.2f",
                    help="Positive for income, negative for expenses"
                )
                
                account_name = st.selectbox(
                    "Account",
                    options=list(accounts.keys()),
                    help="Which account was used for this transaction?"
                )
            
            # Category selection (optional)
            category_names = ["None (Uncategorized)"] + list(categories.keys())
            selected_category = st.selectbox(
                "Category (Optional)",
                options=category_names,
                help="Categorize this transaction for better organization"
            )
            
            # Submit button
            submitted = st.form_submit_button("💾 Add Transaction", type="primary")
            
            if submitted:
                try:
                    # Validate inputs
                    if not description.strip():
                        st.error("Description is required")
                        return
                    
                    if amount == 0:
                        st.error("Amount cannot be zero")
                        return
                        
                    # Get account and category IDs
                    account_id = accounts[account_name]
                    category_id = categories.get(selected_category) if selected_category != "None (Uncategorized)" else None
                    
                    # Convert date to datetime for consistency with other transactions
                    from datetime import datetime, time
                    transaction_datetime = datetime.combine(transaction_date, time())
                    
                    # Create the transaction
                    tx = service.create_manual_transaction(
                        date=transaction_datetime,
                        description=description,
                        amount=amount,
                        account_id=account_id,
                        category_id=category_id
                    )
                    
                    if tx:
                        st.success(f"✅ Transaction added successfully! Amount: €{tx.amount_cents / 100:.2f}")
                    
                except Exception as e:
                    st.error(f"Failed to add transaction: {str(e)}")
                    
    except Exception as e:
        st.error(f"Error loading form data: {str(e)}")
        st.info("Please ensure you have imported some data first to create accounts and categories.")


def render_category_management_tab():
    """Render the category management section."""
    st.header("🏷️ Category Management")
    
    # Create tabs for different category functions
    tab1, tab2, tab3 = st.tabs(["➕ Manage Categories", "📊 Category Statistics", "🔄 Bulk Categorization"])
    
    with tab1:
        # Category management forms
        components.render_category_management()
        st.divider()
        components.render_category_pills()
    
    with tab2:
        render_category_statistics()
    
    with tab3:
        categorization.render_bulk_categorization_tab()


def render_category_statistics():
    """Render category statistics and usage information."""
    st.subheader("📊 Category Usage Statistics")
    
    categories = components.service.get_category_names_list()
    if categories:
        st.metric("Total Categories", len(categories))
        
        # Show categories in a more detailed view for management
        import sqlite3
        DATABASE_PATH = 'storage/fin.db'
        
        try:
            with sqlite3.connect(DATABASE_PATH) as con:
                # Get category usage statistics
                usage_df = con.execute("""
                    SELECT 
                        COALESCE(c.name, 'Uncategorized') as category,
                        COUNT(t.id) as transaction_count,
                        COALESCE(SUM(ABS(t.amount_cents)), 0) / 100.0 as total_amount,
                        COALESCE(AVG(ABS(t.amount_cents)), 0) / 100.0 as avg_amount
                    FROM "transaction" t
                    LEFT JOIN "category" c ON t.category_id = c.id
                    GROUP BY c.id, c.name
                    ORDER BY transaction_count DESC
                """).fetchdf()
                
                if not usage_df.empty:
                    st.dataframe(
                        usage_df,
                        column_config={
                            "category": "Category",
                            "transaction_count": st.column_config.NumberColumn("Transactions", format="%d"),
                            "total_amount": st.column_config.NumberColumn("Total Amount (€)", format="%.2f"),
                            "avg_amount": st.column_config.NumberColumn("Avg Amount (€)", format="%.2f")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Show uncategorized count prominently if any exist
                    uncategorized_count = usage_df[usage_df['category'] == 'Uncategorized']['transaction_count'].sum()
                    if uncategorized_count > 0:
                        st.warning(f"⚠️ {uncategorized_count} transactions are still uncategorized. Use the Bulk Categorization tab to assign categories quickly.")
                else:
                    st.info("No transaction data found.")
        except Exception as e:
            st.info("Category statistics will appear here after importing transactions.")
    else:
        st.info("No categories created yet. Use the 'Manage Categories' tab to add your first category.")


if __name__ == "__main__":
    main()