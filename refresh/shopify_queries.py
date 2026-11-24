#!/usr/bin/env python3
"""Prints the Shopify MCP calls (user-Shopify, read-only) for today's windows and the ingest name for each result."""
import datetime as dt, json
IST=dt.timezone(dt.timedelta(hours=5,minutes=30)); t=dt.datetime.now(IST).date(); y=t-dt.timedelta(days=1)
d30=y-dt.timedelta(days=29); p60=y-dt.timedelta(days=59); m12=(y.replace(day=1)-dt.timedelta(days=365)).replace(day=1)
Q=[('daily_sales','run-analytics-query',f"FROM sales SHOW orders, net_sales, total_sales, new_customers, returning_customers, customers TIMESERIES day SINCE {p60} UNTIL {y}"),
 ('daily_sessions','run-analytics-query',f"FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_reached_checkout, sessions_that_completed_checkout TIMESERIES day SINCE {p60} UNTIL {y}"),
 ('rfm','run-analytics-query',"FROM customers SHOW percent_of_customers, new_customer_records, days_since_last_order, total_number_of_orders, total_amount_spent GROUP BY rfm_group WITH TOTALS ORDER BY new_customer_records DESC"),
 ('cohorts','run-analytics-query',f"FROM customers SHOW new_customer_records, total_number_of_orders, total_amount_spent TIMESERIES month SINCE {m12} UNTIL {y}"),
 ('subs_30d','run-analytics-query',f"FROM sales SHOW net_sales, orders, gross_sales GROUP BY product_title, product_variant_title WHERE product_variant_title CONTAINS 'Subscription' OR product_variant_title CONTAINS 'Deliveries' SINCE {d30} UNTIL {y} ORDER BY net_sales DESC"),
 ('top_products_30d','run-analytics-query',f"FROM sales SHOW net_sales, orders GROUP BY product_title SINCE {d30} UNTIL {y} ORDER BY net_sales DESC LIMIT 8"),
 ('sources_30d','run-analytics-query',f"FROM sales SHOW orders, net_sales GROUP BY order_referrer_source SINCE {d30} UNTIL {y} ORDER BY net_sales DESC"),
 ('monthly','run-analytics-query',f"FROM sales SHOW customers, new_customers, returning_customers, orders, net_sales TIMESERIES month SINCE {m12} UNTIL {y}"),
 ('daily_sales_400','run-analytics-query',f"FROM sales SHOW orders, net_sales, total_sales, new_customers, returning_customers, customers TIMESERIES day SINCE {y-dt.timedelta(days=394)} UNTIL {y}"),
 ('daily_sessions_400','run-analytics-query',f"FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_reached_checkout, sessions_that_completed_checkout TIMESERIES day SINCE {y-dt.timedelta(days=394)} UNTIL {y}"),
 ('daily_sales_prev','run-analytics-query',f"FROM sales SHOW orders, net_sales, total_sales, new_customers, returning_customers, customers TIMESERIES day SINCE {y-dt.timedelta(days=729)} UNTIL {y-dt.timedelta(days=395)}"),
 ('daily_sessions_prev','run-analytics-query',f"FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_reached_checkout, sessions_that_completed_checkout TIMESERIES day SINCE {y-dt.timedelta(days=729)} UNTIL {y-dt.timedelta(days=395)}"),
 ('cohort_matrix','run-analytics-query',f"FROM sales SHOW customers GROUP BY customer_cohort_month, month SINCE {m12} UNTIL {y}"),
 ('new_vs_ret_12m','run-analytics-query',f"FROM sales SHOW net_sales, orders, average_order_value GROUP BY new_or_returning_customer SINCE {y-dt.timedelta(days=364)} UNTIL {y}"),
 ('products_12m','run-analytics-query',f"FROM sales SHOW net_sales, orders GROUP BY product_title SINCE {y-dt.timedelta(days=364)} UNTIL {y} ORDER BY net_sales DESC LIMIT 80"),
 ('abandoned_p1','graphql_query','query { abandonedCheckoutsCount(query: "created_at:>=%s created_at:<%s") { count precision } abandonedCheckouts(first: 100, sortKey: CREATED_AT, reverse: true, query: "created_at:>=%s created_at:<%s") { pageInfo { hasNextPage endCursor } nodes { createdAt completedAt totalPriceSet { shopMoney { amount } } customer { id } discountCodes lineItems(first: 5) { nodes { title quantity } } } } }'%(d30,t,d30,t)),
 ('catalog','graphql_query','query { prior: abandonedCheckoutsCount(query: "created_at:>=%s created_at:<%s") { count } products(first: 100, query: "status:active") { nodes { title handle variants(first: 40) { nodes { title price compareAtPrice availableForSale inventoryQuantity } } } } }'%(p60,d30))]
for name,tool,q in Q:
    arg={'query':q}
    print(f"## {name}  ->  CallDynamicTool user-Shopify/{tool} (write_to_file=true), then: python3 ingest.py {name} <result file>\n{json.dumps(arg)}\n")

# ---- Attribution (order-level, for build_attr.py) ----
# Shopify MCP graphql_query, write_to_file=true, one chain per calendar month (12 chains in parallel), 250 orders/page:
ORDERS_Q = ('query($after: String) { orders(first: 250, after: $after, query: "created_at:>=YYYY-MM-01 created_at:<NEXT-MM-01", sortKey: CREATED_AT) '
 '{ pageInfo { hasNextPage endCursor } nodes { name createdAt cancelledAt sourceName attribution { handle } paymentGatewayNames tags discountCodes '
 'currentSubtotalPriceSet { shopMoney { amount } } customer { id } shippingAddress { provinceCode } customerJourneySummary { ready customerOrderIndex '
 'firstVisit { source referrerUrl utmParameters { source medium campaign } } lastVisit { source referrerUrl utmParameters { source medium campaign } } } '
 'lineItems(first: 3) { nodes { title variantTitle quantity discountedTotalSet { shopMoney { amount } } product { productType } } } } } }')
print('\n# ORDERS (attribution): for each of the last 12 months run graphql_query with ORDERS_Q (dates filled in), write_to_file=true;')
print('#   python3 ingest_orders.py <files...> prints hasNext/endCursor per file; repeat with variables {"after": cursor} until hasNext is False.')
print('#   Clear shopify/orders/ first for a full refresh (files are deduped by order name anyway). ~51 pages for 12 months.')
print(ORDERS_Q)

# ---- Abandoned checkouts deep-dive (build_abandoned.py). Clear shopify/abandoned/ first, then page through with {"after": endCursor}.
# The MCP's write_to_file copy is cut at 8 KB; ./ingest_latest_ab.sh picks the full copy saved beside it. Contains contact details: box only.
_d90=(y-dt.timedelta(days=89))
ABANDONED_Q=('query($after: String) { abandonedCheckouts(first: 100, after: $after, sortKey: CREATED_AT, reverse: true, query: "created_at:>=%s") '
 '{ pageInfo { hasNextPage endCursor } nodes { id name createdAt updatedAt completedAt note customAttributes { key value } discountCodes '
 'totalPriceSet { shopMoney { amount } } subtotalPriceSet { shopMoney { amount } } totalLineItemsPriceSet { shopMoney { amount } } '
 'totalDiscountSet { shopMoney { amount } } totalTaxSet { shopMoney { amount } } shippingAddress { provinceCode city phone } billingAddress { phone } '
 'customer { id numberOfOrders createdAt defaultEmailAddress { emailAddress marketingState } defaultPhoneNumber { phoneNumber smsMarketingConsent { state } } } '
 'lineItems(first: 10) { nodes { title variantTitle quantity sku customAttributes { key value } originalUnitPriceSet { shopMoney { amount } } '
 'discountedTotalPriceSet { shopMoney { amount } } variant { id availableForSale inventoryQuantity price } product { id handle productType } } } } } }')%_d90
print('\n# ABANDONED (step 1d): rm -f shopify/abandoned/*.json; graphql_query with this query (write_to_file=true), then ./ingest_latest_ab.sh; repeat with variables {"after": endCursor} until hasNext is False (~11 pages).')
print(ABANDONED_Q)
