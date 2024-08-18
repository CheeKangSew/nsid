# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 13:52:49 2024

@author: ck
"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

# Streamlit App
st.title("Fuel Transaction Analysis")

# Sidebar for page navigation
page = st.sidebar.selectbox("Select Page", ["Fuel Analysis", "Additional Analysis"])

# Step 1: Upload the CSV file in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload the Soliduz fuel data in .csv file", type="csv")

if uploaded_file is not None:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(uploaded_file)
    
    # Convert 'Quantity', 'TotalAmount', and 'Odometer' to numeric values (removing commas)
    df['Quantity'] = df['Quantity'].replace(',', '', regex=True).astype(float)
    df['TotalAmount'] = df['TotalAmount'].replace(',', '', regex=True).astype(float)
    df['Odometer'] = df['Odometer'].replace(',', '', regex=True).astype(float)
    
    # Convert 'TransactionDate' to datetime format
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], errors='coerce').dt.date

    if page == "Fuel Analysis":
        st.header("Fuel Analysis")
        
        # Calculate the fuel efficiency for each vehicle
        vehicle_efficiency = df.groupby('VehicleRegistrationNo').agg(
            initial_odometer=('Odometer', 'min'),
            last_odometer=('Odometer', 'max'),
            total_quantity=('Quantity', 'sum')
        )

        vehicle_efficiency['FuelEfficiency'] = (vehicle_efficiency['last_odometer'] - vehicle_efficiency['initial_odometer']) / vehicle_efficiency['total_quantity']
        vehicle_efficiency = vehicle_efficiency.sort_values(by='FuelEfficiency', ascending=False)

        # Get total Quantity and Amount of fuel by each vehicle
        vehicle_summary = df.groupby('VehicleRegistrationNo').agg({'Quantity': 'sum', 'TotalAmount': 'sum'})
        vehicle_summary = vehicle_summary.sort_values(by='Quantity', ascending=False)

        # Get total Amount of fuel purchased by each driver
        driver_summary = df.groupby('DriverFullName')['TotalAmount'].sum().sort_values(ascending=False)

        # Combine data into a single DataFrame for download
        fuel_analysis_data = vehicle_efficiency.copy()
        fuel_analysis_data = fuel_analysis_data.merge(vehicle_summary, on='VehicleRegistrationNo')
        #fuel_analysis_data['TotalAmountByDriver'] = df.groupby('DriverFullName')['TotalAmount'].transform('sum')

        # Reset index to prepare for Excel export
        fuel_analysis_data.reset_index(inplace=True)

        # Plot the fuel efficiency (KM/L) in chart
        fig, ax = plt.subplots(figsize=(10, 6))
        vehicle_efficiency['FuelEfficiency'].plot(kind='bar', color='green', ax=ax)
        ax.set_title('Fuel Efficiency by Vehicle (KM/L)')
        ax.set_ylabel('Fuel Efficiency (KM/L)')
        ax.set_xlabel('Vehicle Registration No')

        st.pyplot(fig)

        # Merged Bar chart for total Quantity and Amount of fuel by each vehicle
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        vehicle_summary['Quantity'].plot(kind='bar', color='skyblue', ax=ax1, position=1, width=0.4)
        vehicle_summary['TotalAmount'].plot(kind='bar', color='orange', ax=ax2, position=0, width=0.4)

        ax1.set_ylabel('Total Quantity (L) of Fuel')
        ax2.set_ylabel('Total Amount (IDR) of Fuel')
        ax1.set_xlabel('Vehicle Registration No')
        plt.title('Total Quantity and Amount of Fuel by Vehicle')

        st.pyplot(fig)

        # Display Bar chart for total Amount of fuel purchased by each driver
        fig, ax = plt.subplots(figsize=(10, 6))
        driver_summary.plot(kind='bar', color='purple', ax=ax)
        ax.set_title('Total Amount of Fuel Purchased by Driver')
        ax.set_ylabel('Total Amount (IDR) of Fuel')
        ax.set_xlabel('Driver')

        st.pyplot(fig)
        
        # Total ItemName count across all dates
        itemname_count = df['ItemName'].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        itemname_count.plot(kind='bar', color='blue', ax=ax)
        ax.set_title('Total Fuel Type Across All Dates')
        ax.set_ylabel('Count')
        ax.set_xlabel('Item Name')

        st.pyplot(fig)       
        
        # Button to download the Excel file with analysis data for Fuel Analysis
        st.header("Download Fuel Analysis Data")

        def convert_df_to_excel(vehicle_df, driver_df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write vehicle analysis to the first sheet
                vehicle_df.to_excel(writer, index=False, sheet_name='Vehicle Analysis')
                
                # Write driver analysis to the second sheet
                driver_df.to_excel(writer, index=False, sheet_name='Driver Analysis')
                
            processed_data = output.getvalue()
            return processed_data

        # Prepare driver summary data for download
        driver_summary_df = driver_summary.reset_index().rename(columns={'TotalAmount': 'TotalAmountByDriver'})

        # Generate the Excel download link
        st.download_button(
            label="Download Excel",
            data=convert_df_to_excel(fuel_analysis_data, driver_summary_df),
            file_name='fuel_analysis_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    elif page == "Additional Analysis":
        st.header("Additional Analysis")
        
        # Example: Total Quantity and Amount of fuel by Date
        date_summary = df.groupby('TransactionDate').agg({'Quantity': 'sum', 'TotalAmount': 'sum'}).sort_values(by='TransactionDate', ascending=False)

        # Plotting the data
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        date_summary['Quantity'].plot(kind='bar', color='lightblue', ax=ax1, position=1, width=0.4)
        date_summary['TotalAmount'].plot(kind='bar', color='salmon', ax=ax2, position=0, width=0.4)

        ax1.set_ylabel('Total Quantity (L) of Fuel')
        ax2.set_ylabel('Total Amount (IDR) of Fuel')
        ax1.set_xlabel('Transaction Date')
        plt.title('Total Quantity and Amount of Fuel by Date')

        st.pyplot(fig)
        
        # ItemName count per date
        itemname_count_per_date = df.groupby(['TransactionDate', 'ItemName']).size().unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(10, 6))
        itemname_count_per_date.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('ItemName Count Per Date')
        ax.set_ylabel('Count')
        ax.set_xlabel('Transaction Date')

        st.pyplot(fig)         

        # Button to download the Excel file with analysis data for Additional Analysis
        st.header("Download Additional Analysis Data")
        output_file = date_summary.copy()
        output_file.reset_index(inplace=True)
        
        
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            processed_data = output.getvalue()
            return processed_data

        # Generate the Excel download link
        st.download_button(
            label="Download Excel",
            data=convert_df_to_excel(output_file),
            file_name='date_summary_analysis.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
