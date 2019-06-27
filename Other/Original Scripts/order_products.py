import dateutil.parser as dp
import base64
import requests
import pprint
import json
import os

###################
##Ordered Product##
###################

#$event_id: Combines order number and productid
#$value: The total value of the item purchased; no shipping costs or discounts included
#Name: The name or title of the ordered product in Shopify, e.g., t-shirt
#Variant Name: The name or title of the product variant in Shopify, e.g., red, size medium t-shirt
#SKU: The SKU of the product variant, e.g., REDMEDIUMTSHIRT
#ProductID: The ID associated with the product in your store
#Quantity: The total quantity ordered of the product
#Collections: The complete set of collections or categories applied to the product, e.g., t-shirts, men's and sale
#Tags: Any tags applied to the product in your store
#Variant Option: <OptionName>: the name and value of any variant options for the variant ordered, e.g., Variant Option: Size would be Medium and Variant Option: Color would be Red
#Attribute: <AttributeName>: the name and value of any product attributes for the product ordered, e.g., Attribute: Season would be Spring

#All Keys/Password Credentials:
API_KEY = '490f41edd92a10c5b3a407586a9afddc'
PASSWORD = '37146826a987bc7d64eedc6ccab575ea'
ACCOUNT = 'paucek-considine6869'

#List of Various Shopify API Calls that can be changed on the URL:
#https://help.shopify.com/en/api/reference/orders/order (source)
ALL_ORDERS = 'admin/api/2019-04/orders.json?limit=250' #limit is set to 50 (so last 7 are cut off)
ONE_ORDER = '/admin/api/2019-04/orders/1245264004.json' #Example order with two line_items/products
##NOTE: When executing for only one order above, the naming convention of the key x['Orders'] becomes x['Order']
COUNT = 'admin/api/2019-04/orders/count.json' #Count of orders (57) - Note that there are only TWO 2016 Orders, so it is more ideal to work with a more diverse data set
FIELD_ORDERS = 'admin/api/2019-04/orders.json?fields=line_items' #Specify fields
FINSTATUS_ORDERS = 'admin/api/2019-04/orders.json?financial_status=authorized' #Filter by financial_status
#Filter to only paid orders created in 2016
ORDERS16 = 'admin/api/2019-04/orders.json?financial_status=paid&created_at_min=2015-12-31T23:59:59-00:00&created_at_max=2017-01-01T00:00:00-00:01' 

#Use ORDERS16 instead of ALL_ORDERS to run only Paid 2016 orders
shop_url = "https://%s:%s@%s.myshopify.com/%s" % (API_KEY, PASSWORD, ACCOUNT, ORDERS16) 
orders = requests.get(shop_url).json()

#Convert JSON to Base64 String
def stringToBase64(s):
    return base64.b64encode(json.dumps(s).encode('utf-8')).decode('utf-8')

#Function to convert ISO to UNIX numbers
def ISOtoUNIX(tm):    
    parsed_t = dp.parse(tm)
    tmseconds = parsed_t.strftime('%s')
    return tmseconds

#Create dictionaries
ordered_product = {}
ordered_product['customer_properties'] = {}
ordered_product['properties'] = {}

#Uncomment below (and at the bottom) to see all orders/dictionaries (converted to strings) added to a single set/JSON
#Test set structure to contain all ordered products
#test = set()

#Loop through all of the orders
for j in orders['orders']:

    #Loop through all possible individual line_items on each order. 
    for k in range(0,len(j['line_items'])):
    
        #Create token key (API Key Obtained from personal Klaviyo account)
        ordered_product['token'] = 'K9RuRi'

        #Create an event key
        ordered_product['event'] = 'Ordered Product'

        #Update customer key
        for i in range(0,len(j['customer'])):
            ordered_product['customer_properties'].update([
                ('$email' ,  j['customer']['email']),
                ('$first_name' , j['customer']['first_name']),
                ('$last_name' , j['customer']['last_name']),
            ])

        #Update properties key
        #Obtain properties of each product and append to the ordered_product
        try:
            ordered_product['properties'].update([
            ('$event_id', str(j['order_number'])+str(j['line_items'][k]['product_id'])),
            ('$value' , j['line_items'][k]['price']),
            ('name' , j['line_items'][k]['title']),
            ('variant_name' , j['line_items'][k]['name']),
            ('sku' ,  j['line_items'][k]['sku']),
            ('productID' , j['line_items'][k]['product_id']),
            ('quantity' , j['line_items'][k]['quantity']),
            ('collections' , j['line_items'][k]['properties']),
            ('optionname' , j['line_items'][k]['variant_title']),
            ('attributename' , j['line_items'][k]['properties'][0]['name']),
            ('tags' , j['tags']),
            ])
        #Exception statement when name in properties are blank
        except IndexError: 
            ordered_product['properties'].update([
            ('$event_id', str(j['order_number'])+str(j['line_items'][k]['product_id'])),
            ('$value' , j['line_items'][k]['price']),
            ('name' , j['line_items'][k]['title']),
            ('variant_name' , j['line_items'][k]['name']),
            ('sku' ,  j['line_items'][k]['sku']),
            ('productID' , j['line_items'][k]['product_id']),
            ('quantity' , j['line_items'][k]['quantity']),
            ('collections' , j['line_items'][k]['properties']),
            ('optionname' , j['line_items'][k]['variant_title']),
            ('attributename' , j['line_items'][k]['properties']),
            ('tags' , j['tags']),
            ])

        #Create a time key, use function to convert time from ISO to UNIX
        ordered_product['time'] = ISOtoUNIX(j['created_at'])

        #Encode in Base64 and send the JSON file back to Klaviyo API via a Track Call
        #Note: A requests POST should be able to do this, but I get 403 Errors for some reason (see below)
        ##requests.post('https://a.klaviyo.com/api/track?data='+enc_ordered_product)
        enc_ordered_product = stringToBase64(ordered_product)
        post_url = 'https://a.klaviyo.com/api/track?data=%s' % (enc_ordered_product)
        os.popen("curl -i "+post_url).read()

        #Uncomment below to see all orders/dictionaries (converted to strings) added to a single set/JSON
        #Current setting replaces dictionary with latest ordered products read
        #Note: Could not replicate adding nested dictionaries to sets (e.g. https://stackoverflow.com/questions/34097959/add-a-dictionary-to-a-set-with-union)
        #test.add(json.dumps(ordered_product))
        #print(test)

#Uncomment below to export file
#with open('order_products.json', 'w') as outfile:  
#    json.dump(ordered_product, outfile)
