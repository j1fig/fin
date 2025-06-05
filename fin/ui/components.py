import streamlit as st
from fin import service

CATEGORY_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']


def render_category_management():
    """Render the category management section."""
    col1, col2 = st.columns(2)

    with col1:
        render_add_category_form()

    with col2:
        render_edit_category_form()


def render_add_category_form():
    """Render the add category form."""
    st.subheader("Add New Category")
    with st.form("add_category"):
        new_category_name = st.text_input("Category Name")
        submit_add = st.form_submit_button("Add Category")
        
        if submit_add and new_category_name:
            try:
                service.create_new_category(new_category_name)
                st.success(f"Category '{new_category_name}' added successfully!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def render_edit_category_form():
    """Render the edit category form."""
    st.subheader("Edit Category")
    category_options = service.get_categories_for_management()
    
    if category_options:
        with st.form("edit_category"):
            selected_category = st.selectbox("Select Category to Edit", options=list(category_options.keys()))
            new_name = st.text_input("New Name")
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                submit_edit = st.form_submit_button("Update Category")
            with col_delete:
                submit_delete = st.form_submit_button("Delete Category", type="secondary")
            
            if submit_edit and new_name and selected_category:
                try:
                    service.update_existing_category(selected_category, new_name)
                    st.success(f"Category updated to '{new_name}'!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            
            if submit_delete and selected_category:
                try:
                    service.delete_existing_category(selected_category)
                    st.success(f"Category '{selected_category}' deleted!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def render_category_pills():
    """Render category pills display."""
    st.subheader("Current Categories")
    categories = service.get_category_names_list()
    
    if categories:
        # Build all pills in a single HTML string for horizontal display
        pills_html = '<div style="line-height: 2.5;">'
        for i, category in enumerate(categories):
            color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            pills_html += f"""
            <span style="
                background-color: {color};
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                margin: 2px;
                display: inline-block;
                font-size: 12px;
                font-weight: bold;
            ">{category}</span>"""
        pills_html += '</div>'
        
        st.markdown(pills_html, unsafe_allow_html=True)
    else:
        st.info("No categories found. Add some categories above!")


def render_filter_controls(accounts_df):
    """Render filter controls and return selected values."""
    st.text("Transactions")
    
    # Account filter
    account_id = st.selectbox("Account", accounts_df['id'])
    
    # Category filter
    category_options = service.get_categories_for_management()
    category_names = ["All Categories"] + list(category_options.keys())
    selected_category = st.selectbox("Filter by Category", category_names)
    
    return account_id, selected_category, category_options 