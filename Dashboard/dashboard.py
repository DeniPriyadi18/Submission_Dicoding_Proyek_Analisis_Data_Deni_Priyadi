import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency


def create_daily_order_df(df):
    daily_order_df = df.resample(rule ='D', on='order_purchase_timestamp').agg({
        "order_id" : "nunique",
        "payment_value" : "sum"
    })
    daily_order_df = daily_order_df.reset_index()        
    daily_order_df.rename(columns={
        "order_id" : "order_count",
        "payment_value" : "revenue"
    }, inplace = True)

    return daily_order_df

def create_sum_order_item_df(df):
    sum_order_item_df = df.groupby(by = "product_category_name").product_id.count().reset_index()
    sum_order_item_df.rename(columns = {
        "product_id" : "product"
    }, inplace = True)
    sum_order_item_df = sum_order_item_df.sort_values(by='product', ascending = False)
    return sum_order_item_df

def create_customer_city_df(df):
    customer_city_df = df.groupby(by='customer_city').customer_id.nunique().reset_index()
    customer_city_df.rename(columns={
        'customer_id' : 'customer_count'
    }, inplace=True)
    customer_city_df = customer_city_df.sort_values(by= 'customer_count', ascending = False)
    return customer_city_df

def create_customer_state_df(df):
    customer_state_df = df.groupby(by='customer_state').customer_id.nunique().reset_index()
    customer_state_df.rename(columns={
        'customer_id' : 'customer_count'
    }, inplace = True)

    return customer_state_df

def create_cancel_order_df(df):
    cancel_order_df = df[df['order_status']=='canceled']
    cancel_order_df = cancel_order_df.groupby(by='product_category_name').size().reset_index(name='total_cancel')
    cancel_order_df = cancel_order_df.sort_values(by='total_cancel', ascending=False)
    cancel_order_df.rename(columns={
    'product_category_name' : 'produk'
    }, inplace = True)

    return cancel_order_df

def create_late_order_item_df(df):
    late_order_item_df = df[df['delivery_status']=='late']
    late_order_item_df = late_order_item_df.groupby(by='seller_city').size().reset_index(name = 'total_late')
    late_order_item_df = late_order_item_df.sort_values(by='total_late',ascending = False)

    return late_order_item_df


def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "payment_value": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df['customer_id']  = rfm_df['customer_id'].str[-10:]
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

df = pd.read_csv('Dashboard/e-commerce.csv')

datetime_columns = ['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date', 'shipping_limit_date']
df.sort_values(by='order_purchase_timestamp', inplace =True)
df.reset_index(inplace = True)

for column in datetime_columns:
    df[column] = pd.to_datetime(df[column])

min_date = df['order_purchase_timestamp'].min()
max_date = df['order_purchase_timestamp'].max()

with st.sidebar:
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
main_df = df[(df['order_purchase_timestamp'] >= str(start_date)) & (df['order_purchase_timestamp'] <= str(end_date))]

daily_order_df = create_daily_order_df(main_df)
sum_order_item_df = create_sum_order_item_df(main_df)
customer_city_df = create_customer_city_df(main_df)
cancel_order_df = create_cancel_order_df(main_df)
late_order_item_df = create_late_order_item_df(main_df)
customer_state_df = create_customer_state_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('E-Commerce Dashboard')

st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_order_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_order_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_order_df["order_purchase_timestamp"],
    daily_order_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)


st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="product", y="product_category_name", data=sum_order_item_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="product", y="product_category_name", data=sum_order_item_df.sort_values(by="product", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

st.subheader("Customer Demographics")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))

    sns.barplot(
        y="customer_count", 
        x="customer_city",
        data=customer_city_df.head(10),
        palette='viridis',
        ax=ax
    )
    ax.set_title("Number of Customer by City", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='x', labelsize=15, rotation = 45)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    
    sns.barplot(
        y="customer_state", 
        x="customer_count",
        data=customer_state_df.sort_values(by="customer_count", ascending=False),
        palette='coolwarm',
        orient = 'h'
    )
    ax.set_title("Number of Customer by State", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='x', labelsize=20)
    ax.tick_params(axis='y', labelsize=15)
    st.pyplot(fig)

st.subheader("Top 5 canceled products")

fig, ax = plt.subplots(figsize=(10,7))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x='produk',
    y='total_cancel',
    data = cancel_order_df[:5],
    palette = colors 
    )    
ax.set_title("canceled products", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis = 'x', size = 50, rotation = 45)
ax.tick_params(axis = 'y', size = 50)
st.pyplot(fig)

st.subheader("Top 5 Cities that are Late")

fig, ax = plt.subplots(figsize=(10,7))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x='seller_city',
    y='total_late',
    data= late_order_item_df[:5],
    palette = colors
)
ax.set_title("Top 5 Cities that are Late", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis = 'x', size = 50, rotation = 45)
ax.tick_params(axis = 'y', size = 50)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=15)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis='y', labelsize=20)
ax[0].tick_params(axis='x', labelsize=10, rotation = 25)

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=15)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=10, rotation = 25)

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=15)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=10, rotation = 25)

st.pyplot(fig)