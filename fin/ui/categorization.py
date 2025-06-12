import streamlit as st
import pandas as pd
from fin import service


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
        transactions_list = service.get_uncategorized_transactions()
        transactions_df = pd.DataFrame(transactions_list)
        filter_desc = "uncategorized"
    else:
        transactions_list = service.get_all_transactions_for_ui(selected_filter_category)
        transactions_df = pd.DataFrame(transactions_list)
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
            is_selected = st.checkbox("Select", label_visibility="hidden", key=f"tx_{row['id']}", value=select_all)
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
                    service.update_transactions_category(selected_transactions, selected_category)
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
    
    merchant_groups_list = service.get_merchant_groups(uncategorized_only=show_uncategorized_only)
    merchant_groups = pd.DataFrame(merchant_groups_list)
    
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
                samples_list = service.get_sample_transactions_for_merchant(row['merchant'])
                for sample in samples_list:
                    st.write(f"• {sample['date']}: €{sample['amount']:.2f}")
            
            with col2:
                selected_category = st.selectbox(
                    "Assign Category",
                    ["-- Select Category --"] + categories,
                    key=f"merchant_{idx}",
                    help=f"Category for all {row['transaction_count']} transactions from this merchant"
                )
                
                # Check if a real category was selected (not the placeholder)
                if selected_category == "-- Select Category --":
                    selected_category = None
                
                if selected_category and st.button(
                    f"Assign to {row['transaction_count']} transactions", 
                    key=f"assign_merchant_{idx}"
                ):
                    try:
                        service.update_merchant_transactions(row['merchant'], selected_category)
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
                    matching_count = service.count_pattern_matches(pattern, case_sensitive, apply_to_all)
                    
                    if matching_count > 0:
                        filter_desc = "transactions" if apply_to_all else "uncategorized transactions"
                        st.info(f"This rule would affect {matching_count} {filter_desc}.")
                        
                        if st.button("Apply Rule", type="primary"):
                            try:
                                applied_count = service.apply_pattern_rule(pattern, category, case_sensitive, apply_to_all)
                                st.success(f"Applied rule! Categorized {applied_count} transactions as '{category}'.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error applying rule: {e}")
                    else:
                        filter_desc = "transactions" if apply_to_all else "uncategorized transactions"
                        st.warning(f"No {filter_desc} match this pattern.")
    
    with col2:
        st.write("**Quick Pattern Suggestions**")
        
        # Show common patterns that could be categorized
        common_patterns_list = service.get_common_uncategorized_patterns()
        
        if common_patterns_list:
            st.write("Frequently appearing merchants/patterns:")
            for pattern_info in common_patterns_list:
                st.write(f"• **{pattern_info['pattern']}** ({pattern_info['count']} transactions)")
        else:
            st.info("No common patterns found in uncategorized transactions.")


# Helper functions

# All SQL-based functions have been moved to the service layer for better separation of concerns 