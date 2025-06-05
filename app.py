"""
Main Streamlit application entry point.
"""
import streamlit as st
from fin.ui import components, charts


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(
        page_title="Fin - Personal Finance Tracker",
        page_icon="💰",
        layout="wide"
    )
    
    # Sidebar navigation
    st.sidebar.title("Fin")
    st.sidebar.subheader("your personal finance tracker")
    selected_tab = st.sidebar.selectbox(
        "Choose a section:",
        ["📊 Overview", "📁 Import Data", "🏷️ Category Management"]
    )
    
    # Route to appropriate tab
    if selected_tab == "📊 Overview":
        render_overview_tab()
    elif selected_tab == "📁 Import Data":
        render_import_tab()
    elif selected_tab == "🏷️ Category Management":
        render_category_management_tab()


def render_overview_tab():
    """Render the main overview with transactions and charts."""
    st.header("Financial Overview")
    
    # Display current categories as pills at the top
    components.render_category_pills()
    
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
    st.header("Import Transaction Data")
    
    st.write("Upload your CGD transaction file to get started:")
    
    uploaded_file = st.file_uploader(
        "Choose a CGD transactions file", 
        type="tsv",
        help="Select a .tsv file exported from CGD bank"
    )
    
    if uploaded_file:
        service.import_cgd_transactions(uploaded_file)
        st.success("Transactions imported successfully!")
    
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


def render_category_management_tab():
    """Render the category management section."""
    st.header("Category Management")
    
    # Category management forms
    components.render_category_management()
    
    st.divider()
    
    # Display current categories
    components.render_category_pills()
    
    # Category statistics
    st.subheader("Category Statistics")
    with st.container():
        # This could be expanded with category usage stats
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
                            c.name as category,
                            COUNT(t.id) as transaction_count,
                            COALESCE(SUM(t.amount_cents), 0) / 100.0 as total_amount
                        FROM category c
                        LEFT JOIN "transaction" t ON c.id = t.category_id
                        GROUP BY c.id, c.name
                        ORDER BY transaction_count DESC
                    """).fetchdf()
                    
                    if not usage_df.empty:
                        st.subheader("Category Usage")
                        st.dataframe(
                            usage_df,
                            column_config={
                                "category": "Category",
                                "transaction_count": st.column_config.NumberColumn("Transactions", format="%d"),
                                "total_amount": st.column_config.NumberColumn("Total Amount (€)", format="%.2f")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
            except Exception as e:
                st.info("Category statistics will appear here after importing transactions.")
        else:
            st.info("No categories created yet. Use the forms above to add your first category.")


if __name__ == "__main__":
    main()