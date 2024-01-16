import shippo
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Shippo API key
shippo.api_key = 'shippo_test_9c3e66eb7b38504e6dd7bff1289d0579d6518704'

# WooCommerce API credentials
woocommerce_url = 'https://izzieprop.com'
woocommerce_key = 'ck_3971c6a5ca8541182b4a27bb0cf73d00ab162160'
woocommerce_secret = 'cs_a4853cf23a1a8967fc1d91f50b58fcf886c0d6fa'

# Email configuration (replace with your actual email server details)
email_host = 'smtp.mailersend.net'
email_port = 587
email_username = 'MS_PQEEay@izzieprop.com'
email_password = 'xdyhXbqtTaPY50WT'

# Function to get the most recent order details from WooCommerce
def get_most_recent_order_details():
    endpoint = '/wp-json/wc/v3/orders'
    url = f'{woocommerce_url}{endpoint}?order=desc&orderby=date&per_page=1'

    # Debugging output
    print(f"Fetching the most recent order details from: {url}")

    response = requests.get(url, auth=(woocommerce_key, woocommerce_secret), params={'consumer_key': woocommerce_key, 'consumer_secret': woocommerce_secret})

    # Debugging output
    print(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        order_data = response.json()

        if order_data:
            most_recent_order = order_data[0]
            order_id = most_recent_order.get('id')
            line_items = most_recent_order.get('line_items', [])

            if line_items:
                # Assuming the order has only one product for simplicity
                product_id = line_items[0].get('product_id')
                vendor_id = line_items[0].get('vendor_id')  # Get vendor_id if available

                shipping_address = most_recent_order.get('shipping', {}).get('address', {})
                return order_id, vendor_id, product_id, shipping_address
            else:
                print("No line items found in the most recent order.")
                return None, None, None, None
        else:
            print("No orders found.")
            return None, None, None, None
    else:
        print(f"Failed to retrieve most recent order details. Status code: {response.status_code}")
        return None, None, None, None

# Function to get vendor details from WooCommerce
def get_vendor_details(vendor_id):
    endpoint = f'/wp-json/wc/v3/products/vendors/{vendor_id}'
    url = f'{woocommerce_url}{endpoint}'

    response = requests.get(url, auth=(woocommerce_key, woocommerce_secret))

    if response.status_code == 200:
        vendor_data = response.json()
        vendor_address = {
            "name": vendor_data.get('name', ''),
            "street1": vendor_data.get('address', {}).get('street', ''),
            "city": vendor_data.get('address', {}).get('city', ''),
            "state": vendor_data.get('address', {}).get('state', ''),
            "zip": vendor_data.get('address', {}).get('postcode', ''),
            "country": vendor_data.get('address', {}).get('country', ''),
            "email": vendor_data.get('email', ''),  # Add vendor's email address
        }
        return vendor_address
    else:
        print(f"Failed to retrieve vendor details. Status code: {response.status_code}")
        return None

# Function to get product details from WooCommerce
def get_product_details(product_id):
    endpoint = f'/wp-json/wc/v3/products/{product_id}'
    url = f'{woocommerce_url}{endpoint}'

    response = requests.get(url, auth=(woocommerce_key, woocommerce_secret))

    if response.status_code == 200:
        product_data = response.json()
        dimensions = {
            "length": str(product_data.get('dimensions', {}).get('length', '')),
            "width": str(product_data.get('dimensions', {}).get('width', '')),
            "height": str(product_data.get('dimensions', {}).get('height', '')),
            "distance_unit": "in",
        }
        weight = {
            "weight": str(product_data.get('weight', '')),
            "mass_unit": "lb",
        }
        return dimensions, weight
    else:
        print(f"Failed to retrieve product details. Status code: {response.status_code}")
        return None, None

# Function to send email with label attachment
def send_email(to_email, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = email_username
    msg['To'] = to_email
    msg['Subject'] = 'Shipping Label'

    # Attach the label file
    with open(attachment_path, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), Name='label.pdf')
        part['Content-Disposition'] = f'attachment; filename=label.pdf'
        msg.attach(part)

    # Connect to the email server and send the email
    with smtplib.SMTP(email_host, email_port) as server:
        server.starttls()
        server.login(email_username, email_password)
        server.send_message(msg)

# Fetch the most recent order details
order_id, vendor_id, product_id, customer_address = get_most_recent_order_details()

if order_id and vendor_id and product_id and customer_address:
    # Create shipment with order ID, vendor address, customer address, and parcel information
    shipment = shippo.Shipment.create(
        order_id=order_id,
        address_from=get_vendor_details(vendor_id),
        address_to=customer_address,
        parcels=[{
            **get_product_details(product_id)[0],
            **get_product_details(product_id)[1],
        }],
    )

    # Get label URL
    label_url = shipment.rates[0].label_url  # Assuming you want the first rate's label URL

    #
