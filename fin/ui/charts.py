import sqlite3
import streamlit as st
import pandas as pd
from fin import service

DATABASE_PATH = 'storage/fin.db'


def render_accounts_table():
    """Render the accounts table."""
    with sqlite3.connect(DATABASE_PATH) as con:
        st.text("Accounts")
        df = pd.read_sql('SELECT * from "account"', con)
        st.table(df)
        return df


def build_transaction_query(account_id, selected_category, category_options):
    """Build SQL query and parameters based on filters."""
    if selected_category == "All Categories":
        query = '''
        SELECT t.*, c.name as category_name 
        FROM "transaction" t 
        LEFT JOIN "category" c ON t.category_id = c.id 
        WHERE t.account_id = ?
        '''
        params = (account_id,)
    else:
        category_id = category_options[selected_category]
        query = '''
        SELECT t.*, c.name as category_name 
        FROM "transaction" t 
        LEFT JOIN "category" c ON t.category_id = c.id 
        WHERE t.account_id = ? AND t.category_id = ?
        '''
        params = (account_id, category_id)
    
    return query, params


def render_transactions_table(query, params):
    """Render the editable transactions table with inline category editing."""
    with sqlite3.connect(DATABASE_PATH) as con:
        df = pd.read_sql(query, con, params=params)
        
        if df.empty:
            st.info("No transactions found for the selected filters.")
            return
            
        # Prepare data for display
        df['amount'] = df['amount_cents'] / 100
        df['date'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
        
        # Get all available categories for the dropdown
        all_categories = service.get_category_names_list()
        
        # Prepare display dataframe
        display_df = df[['id', 'date', 'description', 'amount', 'category_name']].copy()
        display_df.columns = ['ID', 'Date', 'Description', 'Amount (€)', 'Category']
        
        # Fill null categories
        display_df['Category'] = display_df['Category'].fillna('Uncategorized')
        
        st.text("Transactions")
        
        # Add live search filter
        search_term = st.text_input(
            "🔍 Search transactions", 
            placeholder="Type to search by description...",
            help="Search by transaction description (case insensitive)"
        )
        
        # Apply search filter
        if search_term:
            mask = display_df['Description'].str.contains(search_term, case=False, na=False)
            filtered_df = display_df[mask].reset_index(drop=True)
            
            if filtered_df.empty:
                st.info(f"No transactions found matching '{search_term}'")
                return
        else:
            filtered_df = display_df
        
        # Configure the data editor
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "Date": st.column_config.TextColumn(
                    "Date",
                    disabled=True,
                    width="small"
                ),
                "Description": st.column_config.TextColumn(
                    "Description", 
                    disabled=True,
                    width="large"
                ),
                "Amount (€)": st.column_config.NumberColumn(
                    "Amount (€)",
                    disabled=True,
                    format="%.2f",
                    width="small"
                ),
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=all_categories + ['Uncategorized'],
                    required=True,
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True,
            key="transactions_editor"
        )
        
        # Handle category changes
        _handle_category_changes(filtered_df, edited_df)
        
        # Show stats for filtered results
        total_amount = filtered_df['Amount (€)'].sum()
        average_amount = total_amount / len(filtered_df)
        p90_amount = filtered_df['Amount (€)'].quantile(0.9)
        if search_term:
            st.text(f"Filtered total: {total_amount:.2f} (showing {len(filtered_df)} of {len(display_df)} transactions)")
            st.text(f"Average amount: {average_amount:.2f}")
            st.text(f"90th percentile: {p90_amount:.2f}")
        else:
            st.text(f"Total transacted: {total_amount:.2f}")
            st.text(f"Average amount: {average_amount:.2f}")
            st.text(f"90th percentile: {p90_amount:.2f}")


def _handle_category_changes(original_df, edited_df):
    """Handle category changes made in the data editor."""
    if not original_df.equals(edited_df):
        # Find changed rows
        changes = []
        for idx in range(len(original_df)):
            if (idx < len(edited_df) and 
                original_df.iloc[idx]['Category'] != edited_df.iloc[idx]['Category']):
                changes.append({
                    'transaction_id': int(edited_df.iloc[idx]['ID']),
                    'old_category': original_df.iloc[idx]['Category'],
                    'new_category': edited_df.iloc[idx]['Category']
                })
        
        # Apply changes to database
        if changes:
            try:
                for change in changes:
                    _update_transaction_category(
                        change['transaction_id'], 
                        change['new_category']
                    )
                st.success(f"Updated {len(changes)} transaction(s)")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating categories: {str(e)}")


def _update_transaction_category(transaction_id: int, category_name: str):
    """Update a transaction's category in the database."""
    with sqlite3.connect(DATABASE_PATH) as con:
        if category_name == 'Uncategorized':
            # Set category_id to NULL
            con.execute(
                'UPDATE "transaction" SET category_id = NULL WHERE id = ?',
                (transaction_id,)
            )
        else:
            # Get category ID and update
            category_result = con.execute(
                'SELECT id FROM "category" WHERE name = ?',
                (category_name,)
            ).fetchone()
            
            if category_result:
                category_id = category_result[0]
                con.execute(
                    'UPDATE "transaction" SET category_id = ? WHERE id = ?',
                    (category_id, transaction_id)
                )
            else:
                raise ValueError(f"Category '{category_name}' not found")
        
        con.commit()


def render_expenses_income_chart(query, params):
    """Render the expenses vs income chart."""
    st.text("Expenses VS Income (monthly)")
    
    with sqlite3.connect(DATABASE_PATH) as con:
        chart_df = pd.read_sql(query, con, params=params)
        
        if chart_df.empty:
            st.info("No data to display for the selected filters.")
            return
            
        chart_df['amount'] = chart_df['amount_cents'] / 100
        chart_df['created_at'] = pd.to_datetime(chart_df['created_at'])
        chart_df['month'] = chart_df['created_at'].dt.to_period('M')
        chart_df['expenses'] = -chart_df['amount'].where(chart_df['amount'] < 0, 0)
        chart_df['income'] = chart_df['amount'].where(chart_df['amount'] > 0, 0)
        chart_df = chart_df.drop(columns=['amount'])
        chart_df = chart_df.groupby('month').agg({'expenses': 'sum', 'income': 'sum'})
        
        if not chart_df.empty:
            st.line_chart(chart_df)
        else:
            st.info("No data to display for the selected filters.") 