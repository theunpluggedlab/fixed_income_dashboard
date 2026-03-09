import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Set page config
st.set_page_config(page_title='Bond Analytics Dashboard', layout='wide')


# Load data from Parquet files
@st.cache_data
def load_data(series_id):
    file_path = f'data/{series_id.lower()}.parquet'
    if os.path.exists(file_path):
        return pd.read_parquet(file_path)
    else:
        st.error(f'Data file for {series_id} not found!')
        return pd.DataFrame()


# Yield curve data
treasury_series = [
    'DGS1MO',
    'DGS3MO',
    'DGS6MO',
    'DGS1',
    'DGS2',
    'DGS5',
    'DGS7',
    'DGS10',
    'DGS20',
    'DGS30',
]
corporate_series = ['TLT', 'LQD']
trend_series = ['DGS10', 'T10Y2Y']
portfolio_series = ['DGS1', 'DGS5', 'DGS10', 'LQD']

# Tab layout
tab1, tab2, tab3, tab4 = st.tabs(
    ['Yield Curves', 'Historical Trends', 'Portfolio Stats', 'Bond Explanation']
)

# Tab 1: Yield Curves
with tab1:
    st.header('Yield Curves')
    col1, col2 = st.columns(2)

    # Get today's date as the absolute limit for the slider/select
    today = pd.to_datetime(datetime.now().date())
    
    # Define the last 365 days ending today, then reverse so the latest is first
    date_options = pd.date_range(end=today, periods=365, freq='D')[::-1]
    
    # Find the best default: the latest date that actually has data (DGS10)
    data_max_date = load_data('DGS10').index.max()
    
    # Calculate initial index: find where data_max_date is in date_options
    try:
        # Since it's reversed, index 0 is today, and later indices are older dates
        initial_index = date_options.get_loc(data_max_date)
    except (KeyError, ValueError):
        initial_index = 0 # Default to the first item (today) if data is missing

    selected_date = st.sidebar.selectbox(
        'Select Date (for Treasury Yield Curve)',
        options=date_options,
        index=int(initial_index),
        format_func=lambda x: x.strftime('%Y-%m-%d'),
    )

    # Treasury Yield Curve
    with col1:
        st.subheader('Treasury Yield Curve')
        treasury_yields = {}
        for series in treasury_series:
            df = load_data(series)  # Replace with your actual data loading function
            if selected_date in df.index:
                treasury_yields[series] = df.loc[selected_date, 'yield']

        if treasury_yields:
            # Create figure with consistent size (width, height)
            fig, ax = plt.subplots(figsize=(8, 6))  # Set width=8, height=6
            maturities = [1 / 12, 3 / 12, 6 / 12, 1, 2, 5, 7, 10, 20, 30]
            yields = [treasury_yields[s] for s in treasury_series]
            ax.plot(maturities, yields, marker='o')
            ax.set_xlabel('Maturity (Years)')
            ax.set_ylabel('Yield (%)')
            ax.set_title(f'Treasury Yield Curve - {selected_date.date()}')
            ax.grid(True, linestyle='--', alpha=0.7)
            st.pyplot(fig)
        else:
            st.warning('Sorry... No data has been found for this day. Try another one!')

        # ETF vs Treasury Comparison
        with col2:
            st.subheader('ETF Prices vs 10Y Treasury Yield')

            # Define the series to load
            etf_series = ['TLT', 'LQD']
            treasury_series = ['DGS10']
            all_series = etf_series + treasury_series

            # Load data for each series
            esg_yields = {}
            for series in all_series:
                df = load_data(series)  # Replace with your actual data loading function
                esg_yields[series] = df

            # Check if data was loaded
            if esg_yields:
                # Create figure with consistent size (width, height)
                fig, ax = plt.subplots(figsize=(8, 6))  # Match width=8, height=6

                # Define labels, mapped by specific indices or manually
                labels = ['TLT (Treasury Bond ETF)', 'LQD (Corp Bond ETF)', '10Y Treasury Yield']
                color_map = {'TLT': 'blue', 'LQD': 'red', 'DGS10': 'green'}

                # Plot DGS10 on primary axis
                df_treasury = esg_yields['DGS10']
                if 'yield' in df_treasury.columns:
                    ax.plot(
                        df_treasury.index,
                        df_treasury['yield'],
                        color=color_map['DGS10'],
                        label=labels[2],
                        alpha=0.6,
                    )
                ax.set_ylabel('Yield (%)', color='green')
                ax.tick_params(axis='y', labelcolor='green')

                # Plot ETFs on secondary axis
                ax2 = ax.twinx()
                for i, series in enumerate(['TLT', 'LQD']):
                    df = esg_yields[series]
                    if 'price' in df.columns:
                        ax2.plot(
                            df.index,
                            df['price'],
                            color=color_map[series],
                            label=labels[i],
                            alpha=0.6,
                        )
                ax2.set_ylabel('ETF Price ($)')

                # Customize the plot
                ax.set_title('ETF Prices vs 10Y Treasury (over time)')
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                ax.grid(True, linestyle='--', alpha=0.7)

                # Display the plot in Streamlit
                st.pyplot(fig)

# Tab 2: Historical Trends
with tab2:
    col1, col2, col3 = st.columns([2, 8, 2])

    with col2:
        st.header('Historical Trends')
        trend_data = {}
        for series in trend_series:
            df = load_data(series)
            if not df.empty:
                trend_data[series] = df

        if trend_data:
            # Create figure with consistent size
            fig, ax = plt.subplots(figsize=(8, 6))

            # Plot each series with distinct colors
            color_map = {
                series: plt.cm.tab10(i) for i, series in enumerate(trend_series)
            }  # Auto-generate colors
            for series in trend_series:
                df = trend_data[series]
                ax.plot(
                    df.index,
                    df['yield'],
                    label=series,
                    color=color_map[series],
                    alpha=0.8,
                )

            # Customize the plot
            ax.set_xlabel('Date')
            ax.set_ylabel('Yield (%)')
            ax.set_title('Historical Yield Trends')
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.7)  # Match grid style

            # Add left and right margins
            fig.subplots_adjust(
                left=0.1, right=0.9
            )  # Adjust left and right margins (0.3 = 30% margin)

            # Display in Streamlit
            st.pyplot(fig)

# Tab 3: Portfolio Stats
with tab3:
    st.header('Portfolio Summary')
    try:
        # Initial portfolio setup
        portfolio_initial = [
            {'series': 'DGS1', 'weight': 0.2, 'face_value': 1000, 'coupon': 2.0},
            {'series': 'DGS5', 'weight': 0.3, 'face_value': 1000, 'coupon': 2.5},
            {'series': 'DGS10', 'weight': 0.3, 'face_value': 1000, 'coupon': 3.0},
            {'series': 'DGS30', 'weight': 0.2, 'face_value': 1000, 'coupon': 4.5},
        ]

        st.subheader('Adjust Portfolio Weights')
        st.write(
            'Adjust the sliders below to change the portfolio allocation. Total should equal 100%.'
        )

        # Create sliders for weight adjustment
        col1, col2 = st.columns(2)

        with col1:
            dgs1_weight = st.slider(
                'DGS1 Weight (%)', 0, 100, int(portfolio_initial[0]['weight'] * 100)
            )
            dgs5_weight = st.slider(
                'DGS5 Weight (%)', 0, 100, int(portfolio_initial[1]['weight'] * 100)
            )

        with col2:
            dgs10_weight = st.slider(
                'DGS10 Weight (%)', 0, 100, int(portfolio_initial[2]['weight'] * 100)
            )
            dgs30_weight = st.slider(
                'DGS30 Weight (%)', 0, 100, int(portfolio_initial[3]['weight'] * 100)
            )

        # Calculate total weight and show warning if not 100%
        total_weight = dgs1_weight + dgs5_weight + dgs10_weight + dgs30_weight

        if total_weight != 100:
            st.warning(f'Total weight is {total_weight}%. Please adjust to total 100%.')

        # Update portfolio with new weights
        portfolio = [
            {
                'series': 'DGS1',
                'weight': dgs1_weight / 100,
                'face_value': 1000,
                'coupon': 2.0,
            },
            {
                'series': 'DGS5',
                'weight': dgs5_weight / 100,
                'face_value': 1000,
                'coupon': 2.5,
            },
            {
                'series': 'DGS10',
                'weight': dgs10_weight / 100,
                'face_value': 1000,
                'coupon': 3.0,
            },
            {
                'series': 'DGS30',
                'weight': dgs30_weight / 100,
                'face_value': 1000,
                'coupon': 4.5,
            },
        ]

        portfolio_df = pd.DataFrame(portfolio)
        for i, row in portfolio_df.iterrows():
            df = load_data(row['series'])
            if selected_date in df.index:
                portfolio_df.loc[i, 'yield'] = df.loc[selected_date, 'yield']

        # Get user investment amount
        investment_amount = st.number_input(
            'Total Investment Amount ($)', min_value=1000.0, value=10000.0, step=1000.0
        )

        # Calculate actual dollar allocations
        portfolio_df['dollar_allocation'] = portfolio_df['weight'] * investment_amount

        # Calculate summary stats
        portfolio_df['weighted_yield'] = portfolio_df['weight'] * portfolio_df['yield']
        avg_yield = portfolio_df['weighted_yield'].sum()
        total_annual_income = (
            portfolio_df['dollar_allocation'] * portfolio_df['yield'] / 100
        ).sum()

        # Formatting for display
        display_df = portfolio_df[
            ['series', 'weight', 'yield', 'dollar_allocation']
        ].copy()
        display_df['weight'] = display_df['weight'].apply(lambda x: f'{x:.1%}')
        display_df['yield'] = display_df['yield'].apply(lambda x: f'{x:.2f}%')
        display_df['dollar_allocation'] = display_df['dollar_allocation'].apply(
            lambda x: f'${x:,.2f}'
        )
        display_df.columns = ['Series', 'Weight', 'Yield', 'Allocation ($)']

        st.subheader('Portfolio Allocation')
        st.table(display_df)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label='Average Weighted Yield', value=f'{avg_yield:.2f}%')
        with col2:
            st.metric(
                label='Estimated Annual Income', value=f'${total_annual_income:,.2f}'
            )

        # Limit width
        _, col2, _ = st.columns([2, 8, 2])

        with col2:
            # Portfolio Visualization
            st.header('Portfolio Composition and Yields')

            # Create the visualization
            fig, ax1 = plt.subplots(figsize=(8, 6))

            bars = ax1.bar(
                portfolio_df['series'],
                portfolio_df['weight'],
                color='tab:blue',
                label='Weight',
            )
            ax1.set_ylabel('Weight')
            ax1.set_ylim(0, max(portfolio_df['weight']) * 1.2)  # Add some headroom
            ax1.set_title('Portfolio Allocation and Yields')

            # Add weight labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(
                    f'{height:.1%}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                )

            # Create a second y-axis for yields
            ax2 = ax1.twinx()
            line = ax2.plot(
                portfolio_df['series'],
                portfolio_df['yield'],
                color='red',
                marker='o',
                linewidth=2,
                label='Yield (%)',
            )
            ax2.set_ylabel('Yield (%)')
            ax2.tick_params(axis='y')

            # Add yield labels above markers
            for i, yld in enumerate(portfolio_df['yield']):
                ax2.annotate(
                    f'{yld:.2f}%',
                    xy=(i, yld),
                    xytext=(0, 4),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                )

            # Add legends with better positioning
            ax1.legend(loc='upper right', bbox_to_anchor=(1, 1))
            ax2.legend(loc='upper right', bbox_to_anchor=(1, 0.93))

            # Enhance grid for better readability
            ax1.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()

            st.pyplot(fig)
    except Exception:
        st.warning('Sorry... No data has been found for this day. Try another one!')
        # st.error(f"Error details: {e}")

# Tab 4: Bond Explanation
with tab4:
    # Define the series
    treasury_series = [
        'DGS1MO',
        'DGS3MO',
        'DGS6MO',
        'DGS1',
        'DGS2',
        'DGS5',
        'DGS7',
        'DGS10',
        'DGS20',
        'DGS30',
    ]
    corporate_series = ['TLT', 'LQD']
    trend_series = ['DGS10', 'T10Y2Y']
    portfolio_series = ['DGS1', 'DGS5', 'DGS10', 'LQD']

    # Create a dictionary with explanations
    bond_explanations = {
        'Series': [
            'DGS1MO',
            'DGS3MO',
            'DGS6MO',
            'DGS1',
            'DGS2',
            'DGS5',
            'DGS7',
            'DGS10',
            'DGS20',
            'DGS30',
            'TLT',
            'LQD',
            'T10Y2Y',
        ],
        'Description': [
            '1-Month Treasury Constant Maturity Rate',
            '3-Month Treasury Constant Maturity Rate',
            '6-Month Treasury Constant Maturity Rate',
            '1-Year Treasury Constant Maturity Rate',
            '2-Year Treasury Constant Maturity Rate',
            '5-Year Treasury Constant Maturity Rate',
            '7-Year Treasury Constant Maturity Rate',
            '10-Year Treasury Constant Maturity Rate',
            '20-Year Treasury Constant Maturity Rate',
            '30-Year Treasury Constant Maturity Rate',
            'iShares 20+ Year Treasury Bond ETF',
            'iShares iBoxx $ Inv Grade Corporate Bond ETF',
            '10-Year Treasury minus 2-Year Treasury Yield Spread (yield curve indicator)',
        ],
        'Category': [
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'Treasury',
            'ETF',
            'ETF',
            'Trend',
        ],
    }

    # Create a DataFrame
    df_bonds = pd.DataFrame(bond_explanations)

    # Display the table in Streamlit (e.g., in a tab or section)
    st.header('Bond Series Explanations')
    st.dataframe(
        df_bonds, use_container_width=True
    )  # Use dataframe for better formatting

if __name__ == '__main__':
    st.write('')
