import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from fin import service


def render_analytics_tab():
    """Render the analytics section with category spending analysis."""
    st.header("📊 Financial Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", 
            value=datetime.now() - timedelta(days=365),
            help="Select the start date for analysis"
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=datetime.now(),
            help="Select the end date for analysis"
        )
    
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    # Get analytics data
    spending_data_list = service.get_category_spending_data(start_date, end_date)
    spending_data = pd.DataFrame(spending_data_list)
    
    if spending_data.empty:
        st.info("No transaction data found for the selected date range.")
        return
    
    # Main analytics sections
    render_spending_overview(spending_data)
    st.divider()
    render_category_analysis(spending_data, start_date, end_date)
    st.divider()
    render_monthly_trends(start_date, end_date)


# Removed - now using service.get_category_spending_data()


def render_spending_overview(spending_data):
    """Render high-level spending overview metrics."""
    st.subheader("💰 Spending Overview")
    
    total_expenses = spending_data['expenses'].sum()
    total_income = spending_data['income'].sum()
    net_amount = total_income - total_expenses
    avg_transaction = spending_data['transaction_count'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Expenses", 
            f"€{total_expenses:,.2f}",
            help="Total amount spent in the selected period"
        )
    
    with col2:
        st.metric(
            "Total Income", 
            f"€{total_income:,.2f}",
            help="Total income in the selected period"
        )
    
    with col3:
        net_color = "normal" if net_amount >= 0 else "inverse"
        st.metric(
            "Net Amount", 
            f"€{net_amount:,.2f}",
            help="Income minus expenses"
        )
    
    with col4:
        st.metric(
            "Transactions", 
            f"{avg_transaction:,}",
            help="Total number of transactions"
        )


def render_category_analysis(spending_data, start_date, end_date):
    """Render category spending analysis with pie chart and table."""
    st.subheader("🏷️ Category Analysis")
    
    # Filter out categories with no expenses for the pie chart
    expense_data = spending_data[spending_data['expenses'] > 0].copy()
    
    if expense_data.empty:
        st.info("No expense data found for the selected period.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**Expense Distribution**")
        
        # Create pie chart
        fig = px.pie(
            expense_data,
            values='expenses',
            names='category',
            title=f"Spending by Category ({start_date} to {end_date})"
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>' +
                         'Amount: €%{value:,.2f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Category Breakdown**")
        
        # Prepare data for display
        display_data = expense_data.copy()
        display_data['percentage'] = (display_data['expenses'] / display_data['expenses'].sum() * 100)
        display_data['avg_per_transaction'] = display_data['expenses'] / display_data['transaction_count']
        
        # Format for display
        formatted_data = display_data[['category', 'expenses', 'percentage', 'transaction_count', 'avg_per_transaction']].copy()
        formatted_data.columns = ['Category', 'Total (€)', 'Share (%)', 'Transactions', 'Avg per Transaction (€)']
        
        st.dataframe(
            formatted_data,
            column_config={
                "Total (€)": st.column_config.NumberColumn(format="€%.2f"),
                "Share (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Transactions": st.column_config.NumberColumn(format="%d"),
                "Avg per Transaction (€)": st.column_config.NumberColumn(format="€%.2f")
            },
            hide_index=True,
            use_container_width=True
        )


def render_monthly_trends(start_date, end_date):
    """Render monthly spending trends by category."""
    st.subheader("📈 Monthly Trends")
    
    trends_data_list = service.get_monthly_spending_trends(start_date, end_date)
    trends_df = pd.DataFrame(trends_data_list)
    
    if trends_df.empty:
        st.info("No expense trend data found for the selected period.")
        return
    
    # Get top 5 categories by total spending
    top_categories = (trends_df.groupby('category')['expenses']
                     .sum()
                     .sort_values(ascending=False)
                     .head(5)
                     .index.tolist())
    
    # Filter data to top categories
    filtered_trends = trends_df[trends_df['category'].isin(top_categories)]
    
    if filtered_trends.empty:
        st.info("Not enough data for trend analysis.")
        return
    
    # Create stacked bar chart
    fig = px.bar(
        filtered_trends,
        x='month',
        y='expenses',
        color='category',
        title="Monthly Spending by Category (Top 5 Categories)",
        text='expenses'
    )
    
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Total Expenses (€)",
        hovermode='x unified',
        height=400,
        barmode='stack'
    )
    
    fig.update_traces(
        texttemplate='€%{text:,.0f}',
        textposition='inside',
        textfont_size=10,
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Month: %{x}<br>' +
                     'Amount: €%{y:,.2f}<br>' +
                     '<extra></extra>'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show monthly summary table
    with st.expander("📊 Monthly Summary Data"):
        pivot_data = filtered_trends.pivot(index='month', columns='category', values='expenses')
        pivot_data = pivot_data.fillna(0)
        pivot_data['Total'] = pivot_data.sum(axis=1)
        
        st.dataframe(
            pivot_data,
            column_config={col: st.column_config.NumberColumn(format="€%.2f") 
                          for col in pivot_data.columns},
            use_container_width=True
        ) 