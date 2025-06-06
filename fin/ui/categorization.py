import sqlite3
import streamlit as st
import pandas as pd
from fin import service

DATABASE_PATH = 'storage/fin.db'


def render_bulk_categorization_tab():
    """Render the bulk categorization tools."""
    st.subheader("🔄 Bulk Categorization Tools")
    st.write("Efficiently categorize or re-categorize multiple transactions at once using various methods.")
    
    # Tabs for different bulk methods
    tab1, tab2, tab3 = st.tabs(["📋 Select & Assign", "🏪 By Merchant", "🎯 Pattern Rules"])
    
    with tab1:
        render_bulk_selection_tool()
    
    with tab2:
        render_merchant_based_tool()
    
    with tab3:
        render_pattern_rules_tool()


def render_bulk_selection_tool():
    """Render tool for selecting transactions and bulk assigning categories."""
    st.subheader("Select Multiple Transactions")
    st.write("Choose transactions from the table below and assign them all to the same category.")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_uncategorized_only = st.checkbox("Show only uncategorized transactions", value=True)
    with col2:
        if not show_uncategorized_only:
            categories = ["All Categories"] + service.get_category_names_list()
            selected_filter_category = st.selectbox("Filter by current category", categories)
        else:
            selected_filter_category = None
    
    # Get transactions based on filter
    if show_uncategorized_only:
        transactions_df = get_uncategorized_transactions()
        filter_desc = "uncategorized"
    else:
        transactions_df = get_all_transactions(selected_filter_category)
        filter_desc = "all" if selected_filter_category == "All Categories" else f"'{selected_filter_category}'"
    
    if transactions_df.empty:
        if show_uncategorized_only:
            st.success("🎉 All transactions are categorized!")
        else:
            st.info("No transactions found matching your filter.")
        return
    
    st.info(f"Found {len(transactions_df)} {filter_desc} transactions")
    
    # Search filter for bulk selection
    search_term = st.text_input(
        "🔍 Filter transactions", 
        placeholder="Type to filter by description...",
        key="bulk_search"
    )
    
    if search_term:
        mask = transactions_df['description'].str.contains(search_term, case=False, na=False)
        filtered_df = transactions_df[mask]
    else:
        filtered_df = transactions_df
    
    if filtered_df.empty:
        st.info("No transactions match your search.")
        return
    
    # Display selectable transactions
    st.write(f"**Showing {len(filtered_df)} transactions:**")
    
    # Create selection interface
    selected_transactions = []
    
    # Add "Select All" checkbox
    select_all = st.checkbox("Select All Visible Transactions")
    
    # Display transactions with checkboxes
    for idx, row in filtered_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1, 1, 1])
        
        with col1:
            is_selected = st.checkbox("", key=f"tx_{row['id']}", value=select_all)
            if is_selected:
                selected_transactions.append(row['id'])
        
        with col2:
            st.write(row['description'])
        
        with col3:
            st.write(f"€{row['amount']:.2f}")
        
        with col4:
            st.write(row['date'])
        
        with col5:
            current_category = row.get('current_category', 'Uncategorized')
            st.write(f"*{current_category}*")
    
    # Bulk categorization form
    if selected_transactions:
        st.divider()
        st.write(f"**Selected {len(selected_transactions)} transactions**")
        
        categories = service.get_category_names_list()
        if categories:
            selected_category = st.selectbox(
                "Assign Category", 
                categories,
                key="bulk_assign_category"
            )
            
            if st.button("Assign Category to Selected Transactions", type="primary"):
                try:
                    update_transactions_category(selected_transactions, selected_category)
                    st.success(f"Successfully assigned {len(selected_transactions)} transactions to '{selected_category}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating transactions: {e}")
        else:
            st.warning("No categories available. Create some categories first.")


def render_merchant_based_tool():
    """Render tool for categorizing by merchant/description patterns."""
    st.subheader("Categorize by Merchant")
    st.write("Group similar transactions by merchant name and assign categories in bulk.")
    
    # Filter option
    show_uncategorized_only = st.checkbox("Show only uncategorized merchants", value=True, key="merchant_filter")
    
    merchant_groups = get_merchant_groups(uncategorized_only=show_uncategorized_only)
    
    if merchant_groups.empty:
        filter_text = "uncategorized" if show_uncategorized_only else ""
        st.info(f"No {filter_text} merchant groups found.")
        return
    
    filter_text = "uncategorized" if show_uncategorized_only else ""
    st.write(f"**Found {len(merchant_groups)} unique {filter_text} merchants:**")
    
    categories = service.get_category_names_list()
    if not categories:
        st.warning("No categories available. Create some categories first.")
        return
    
    # Display merchant groups
    for idx, row in merchant_groups.iterrows():
        current_cat = row.get('current_category', 'Uncategorized')
        with st.expander(f"🏪 {row['merchant']} ({row['transaction_count']} transactions, €{row['total_amount']:.2f}) - *{current_cat}*"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Sample transactions:**")
                # Show a few sample transactions
                samples = get_sample_transactions_for_merchant(row['merchant'])
                for sample in samples.itertuples():
                    st.write(f"• {sample.date}: €{sample.amount:.2f}")
            
            with col2:
                selected_category = st.selectbox(
                    "Assign Category",
                    [""] + categories,
                    key=f"merchant_{idx}",
                    help=f"Category for all {row['transaction_count']} transactions from this merchant"
                )
                
                if selected_category and st.button(
                    f"Assign to {row['transaction_count']} transactions", 
                    key=f"assign_merchant_{idx}"
                ):
                    try:
                        update_merchant_transactions(row['merchant'], selected_category)
                        st.success(f"Assigned all '{row['merchant']}' transactions to '{selected_category}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def render_pattern_rules_tool():
    """Render tool for creating pattern-based categorization rules."""
    st.subheader("Pattern-Based Rules")
    st.write("Create rules to automatically categorize transactions based on description patterns.")
    
    # Filter option
    apply_to_all = st.checkbox("Apply to ALL transactions (not just uncategorized)", key="pattern_filter")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Create New Rule**")
        
        with st.form("pattern_rule"):
            pattern = st.text_input(
                "Text Pattern", 
                placeholder="e.g., 'STARBUCKS', 'UBER', 'GROCERY'",
                help="Transactions containing this text will be categorized"
            )
            
            categories = service.get_category_names_list()
            if categories:
                category = st.selectbox("Assign Category", categories)
                case_sensitive = st.checkbox("Case sensitive matching")
                
                submitted = st.form_submit_button("Preview Rule")
                
                if submitted and pattern and category:
                    # Preview matching transactions
                    matching_count = count_pattern_matches(pattern, case_sensitive, apply_to_all)
                    
                    if matching_count > 0:
                        filter_desc = "transactions" if apply_to_all else "uncategorized transactions"
                        st.info(f"This rule would affect {matching_count} {filter_desc}.")
                        
                        if st.button("Apply Rule", type="primary"):
                            try:
                                apply_pattern_rule(pattern, category, case_sensitive, apply_to_all)
                                st.success(f"Applied rule! Categorized {matching_count} transactions as '{category}'.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error applying rule: {e}")
                    else:
                        filter_desc = "transactions" if apply_to_all else "uncategorized transactions"
                        st.warning(f"No {filter_desc} match this pattern.")
    
    with col2:
        st.write("**Quick Pattern Suggestions**")
        
        # Show common patterns that could be categorized
        common_patterns = get_common_uncategorized_patterns()
        
        if not common_patterns.empty:
            st.write("Frequently appearing merchants/patterns:")
            for pattern in common_patterns.itertuples():
                st.write(f"• **{pattern.pattern}** ({pattern.count} transactions)")
        else:
            st.info("No common patterns found in uncategorized transactions.")


# Helper functions

def get_uncategorized_transactions():
    """Get all uncategorized transactions."""
    with sqlite3.connect(DATABASE_PATH) as con:
        query = """
        SELECT 
            t.id,
            t.description,
            t.amount_cents / 100.0 as amount,
            DATE(t.created_at) as date,
            'Uncategorized' as current_category
        FROM "transaction" t
        WHERE t.category_id IS NULL
        ORDER BY t.created_at DESC
        """
        return pd.read_sql(query, con)


def get_all_transactions(category_filter=None):
    """Get all transactions, optionally filtered by category."""
    with sqlite3.connect(DATABASE_PATH) as con:
        if category_filter == "All Categories" or category_filter is None:
            query = """
            SELECT 
                t.id,
                t.description,
                t.amount_cents / 100.0 as amount,
                DATE(t.created_at) as date,
                COALESCE(c.name, 'Uncategorized') as current_category
            FROM "transaction" t
            LEFT JOIN "category" c ON t.category_id = c.id
            ORDER BY t.created_at DESC
            """
            return pd.read_sql(query, con)
        else:
            query = """
            SELECT 
                t.id,
                t.description,
                t.amount_cents / 100.0 as amount,
                DATE(t.created_at) as date,
                c.name as current_category
            FROM "transaction" t
            JOIN "category" c ON t.category_id = c.id
            WHERE c.name = ?
            ORDER BY t.created_at DESC
            """
            return pd.read_sql(query, con, params=(category_filter,))


def get_merchant_groups(uncategorized_only=True):
    """Get groups of transactions by merchant/description pattern."""
    with sqlite3.connect(DATABASE_PATH) as con:
        if uncategorized_only:
            query = """
            SELECT 
                t.description as merchant,
                COUNT(*) as transaction_count,
                SUM(ABS(t.amount_cents)) / 100.0 as total_amount,
                'Uncategorized' as current_category
            FROM "transaction" t
            WHERE t.category_id IS NULL
            GROUP BY t.description
            HAVING COUNT(*) >= 2
            ORDER BY transaction_count DESC
            """
        else:
            query = """
            SELECT 
                t.description as merchant,
                COUNT(*) as transaction_count,
                SUM(ABS(t.amount_cents)) / 100.0 as total_amount,
                COALESCE(c.name, 'Uncategorized') as current_category
            FROM "transaction" t
            LEFT JOIN "category" c ON t.category_id = c.id
            GROUP BY t.description, c.name
            HAVING COUNT(*) >= 2
            ORDER BY transaction_count DESC
            """
        return pd.read_sql(query, con)


def get_sample_transactions_for_merchant(merchant):
    """Get sample transactions for a specific merchant."""
    with sqlite3.connect(DATABASE_PATH) as con:
        query = """
        SELECT 
            t.amount_cents / 100.0 as amount,
            DATE(t.created_at) as date
        FROM "transaction" t
        WHERE t.description = ? AND t.category_id IS NULL
        ORDER BY t.created_at DESC
        LIMIT 3
        """
        return pd.read_sql(query, con, params=(merchant,))


def update_transactions_category(transaction_ids, category_name):
    """Update multiple transactions to a specific category."""
    with sqlite3.connect(DATABASE_PATH) as con:
        # Get category ID
        category_result = con.execute(
            'SELECT id FROM "category" WHERE name = ?',
            (category_name,)
        ).fetchone()
        
        if not category_result:
            raise ValueError(f"Category '{category_name}' not found")
        
        category_id = category_result[0]
        
        # Update all transactions
        placeholders = ','.join('?' * len(transaction_ids))
        con.execute(
            f'UPDATE "transaction" SET category_id = ? WHERE id IN ({placeholders})',
            [category_id] + transaction_ids
        )
        con.commit()


def update_merchant_transactions(merchant, category_name):
    """Update all transactions from a specific merchant."""
    with sqlite3.connect(DATABASE_PATH) as con:
        # Get category ID
        category_result = con.execute(
            'SELECT id FROM "category" WHERE name = ?',
            (category_name,)
        ).fetchone()
        
        if not category_result:
            raise ValueError(f"Category '{category_name}' not found")
        
        category_id = category_result[0]
        
        # Update all transactions for this merchant
        con.execute(
            'UPDATE "transaction" SET category_id = ? WHERE description = ? AND category_id IS NULL',
            (category_id, merchant)
        )
        con.commit()


def count_pattern_matches(pattern, case_sensitive=False, apply_to_all=False):
    """Count how many transactions match a pattern."""
    with sqlite3.connect(DATABASE_PATH) as con:
        if case_sensitive:
            if apply_to_all:
                query = """
                SELECT COUNT(*) as count
                FROM "transaction" t
                WHERE t.description LIKE ?
                """
            else:
                query = """
                SELECT COUNT(*) as count
                FROM "transaction" t
                WHERE t.description LIKE ? AND t.category_id IS NULL
                """
            pattern_param = f'%{pattern}%'
        else:
            if apply_to_all:
                query = """
                SELECT COUNT(*) as count
                FROM "transaction" t
                WHERE LOWER(t.description) LIKE LOWER(?)
                """
            else:
                query = """
                SELECT COUNT(*) as count
                FROM "transaction" t
                WHERE LOWER(t.description) LIKE LOWER(?) AND t.category_id IS NULL
                """
            pattern_param = f'%{pattern}%'
        
        result = con.execute(query, (pattern_param,)).fetchone()
        return result[0] if result else 0


def apply_pattern_rule(pattern, category_name, case_sensitive=False, apply_to_all=False):
    """Apply a pattern rule to categorize matching transactions."""
    with sqlite3.connect(DATABASE_PATH) as con:
        # Get category ID
        category_result = con.execute(
            'SELECT id FROM "category" WHERE name = ?',
            (category_name,)
        ).fetchone()
        
        if not category_result:
            raise ValueError(f"Category '{category_name}' not found")
        
        category_id = category_result[0]
        
        # Update matching transactions
        if case_sensitive:
            if apply_to_all:
                query = """
                UPDATE "transaction" 
                SET category_id = ? 
                WHERE description LIKE ?
                """
            else:
                query = """
                UPDATE "transaction" 
                SET category_id = ? 
                WHERE description LIKE ? AND category_id IS NULL
                """
            pattern_param = f'%{pattern}%'
        else:
            if apply_to_all:
                query = """
                UPDATE "transaction" 
                SET category_id = ? 
                WHERE LOWER(description) LIKE LOWER(?)
                """
            else:
                query = """
                UPDATE "transaction" 
                SET category_id = ? 
                WHERE LOWER(description) LIKE LOWER(?) AND category_id IS NULL
                """
            pattern_param = f'%{pattern}%'
        
        con.execute(query, (category_id, pattern_param))
        con.commit()


def get_common_uncategorized_patterns():
    """Get common words/patterns in uncategorized transaction descriptions."""
    with sqlite3.connect(DATABASE_PATH) as con:
        query = """
        SELECT 
            CASE 
                WHEN description LIKE '%AMAZON%' THEN 'AMAZON'
                WHEN description LIKE '%STARBUCKS%' THEN 'STARBUCKS'
                WHEN description LIKE '%UBER%' THEN 'UBER'
                WHEN description LIKE '%GROCERY%' OR description LIKE '%MARKET%' THEN 'GROCERY/MARKET'
                WHEN description LIKE '%RESTAURANT%' OR description LIKE '%CAFE%' THEN 'RESTAURANTS'
                WHEN description LIKE '%GAS%' OR description LIKE '%FUEL%' THEN 'GAS/FUEL'
                ELSE SUBSTR(description, 1, 10)
            END as pattern,
            COUNT(*) as count
        FROM "transaction" t
        WHERE t.category_id IS NULL
        GROUP BY pattern
        HAVING count >= 2
        ORDER BY count DESC
        LIMIT 8
        """
        return pd.read_sql(query, con) 