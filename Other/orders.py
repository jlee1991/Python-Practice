import dateutil.parser as dp
import base64
import requests
import pprint
import json
import os

######################
##Shopify API Orders##
######################

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

####################
##Global Functions##
####################

#Convert JSON to Base64 String
def stringToBase64(s):
    return base64.b64encode(json.dumps(s).encode('utf-8')).decode('utf-8')

#Function to convert ISO to UNIX numbers
def ISOtoUNIX(tm):    
    parsed_t = dp.parse(tm)
    tmseconds = parsed_t.strftime('%s')
    return tmseconds

###########
##Classes##
###########

#Create a class for Placed Orders with methods 
class PlacedOrders:

    #Function to get items in an Placed Order
    def getItems(j,k):

        items = {}
        items.update([
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
        return items

    #Function to check/return the value if a Discount Code exists
    def DiscountCode(j):
        if len(j['discount_codes']) >= 1: return j['discount_codes'][0]['code']
        else: return []

    #Function to check/return the value if a Discount Amount exists    
    def DiscountAmount(j):
        if len(j['discount_codes']) >= 1: return j['discount_codes'][0]['amount']
        else: return []

    #Function to create Placed Order Customer Key/Values
    def PlacedOrderCustomer(j):
        for i in range(0,len(j['customer'])):
            placed_order['customer_properties'].update([
                ('$email' ,  j['customer']['email']),
                ('$first_name' , j['customer']['first_name']),
                ('$last_name' , j['customer']['last_name']),
            ])

    #Function to create Placed Order Property Key/Values        
    def PlacedOrderProperties(j):
        placed_order['properties'].update([
        ('$event_id' , j['order_number']),
        ('$value' , j['total_line_items_price']), 
        ('items' , [j['line_items'][x]['title'] for x in range(0,len(j['line_items']))]),
        ('collections' , [j['line_items'][x]['properties'] for x in range(0,len(j['line_items']))]),
        ('item_count' , [j['line_items'][x]['quantity'] for x in range(0,len(j['line_items']))]),
        ('discount_codes' , PlacedOrders.DiscountCode(j)), #One discount code per order
        ('total_discounts' , PlacedOrders.DiscountAmount(j)), #One discount code per order
        ('source_name' , j['source_name']),
        ('items' , [PlacedOrders.getItems(j,x) for x in range(0,len(j['line_items']))])
        ])

#Create a class for Ordered Products with methods 
class orderedProducts:
    
    #Function to create Ordered Product Customer Key/Values  
    def orderedProductCustomer(j):
        for i in range(0,len(j['customer'])):
            ordered_product['customer_properties'].update([
                ('$email' ,  j['customer']['email']),
                ('$first_name' , j['customer']['first_name']),
                ('$last_name' , j['customer']['last_name']),
            ])
    
    #Helper function to check Property Names
    def checkPropertyNames(j,k):
        if len(j['line_items'][k]['properties']) >= 1: return j['line_items'][k]['properties'][0]['name']
        else: return j['line_items'][k]['properties']
    
    #Function to create Ordered Product Property Key/Values  
    def orderedProductProperty(j):
         for k in range(0,len(j['line_items'])):
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
            ('attributename' , orderedProducts.checkPropertyNames(j,k)),
            ('tags' , j['tags']),
            ])

################
##Placed Orders#
################

#$event_id: Order number
#$value: The total value of the placed order, inclusive of shipping and any applied discounts
#Items: The names of the products in someone's order, e.g., t-shirt or pants
#Collections: The complete set of the collections of the products in someone's order, e.g., t-shirts, mens, pants, and sale
#Item Count: The number of items in the order, e.g., 2
#Discount Codes: Any discount or coupon codes someone used towards the order, e.g., SPRING2015; while this isn't synced as a specific metric, there will be a Discount Codes property for each order that will allow you to see who purchased using particular codes.
#Total Discounts: The total amount of any coupons or discounts if someone used a code, e.g., 10.00
#Source Name: POS, Mobile etc.    

#Just to alert the user - not neccessary for functionality
os.system("echo ========================================")
os.system("echo 'Sending Placed Orders!'")  

#Create dictionaries
placed_order = {}
placed_order['customer_properties'] = {}
placed_order['properties'] = {}

#Uncomment below (and at the bottom) to see all orders/dictionaries (converted to strings) added to a single set/JSON
#Test set structure to contain all ordered products
#test = set()

#Loop through all of the orders
for j in orders['orders']:

    #Create token key (API Key Obtained from personal Klaviyo account)
    placed_order['token'] = 'K9RuRi'

    #Create an event key
    placed_order['event'] = 'Placed Order'

    #Update customer key
    PlacedOrders.PlacedOrderCustomer(j)

    #Items, Collections and Item Count are aggregated via list comprehension to display various items in a single order
    PlacedOrders.PlacedOrderProperties(j)

    #Create a time key, use function to convert time from ISO to UNIX
    placed_order['time'] = ISOtoUNIX(j['created_at'])

    #Encode in Base64 and send the JSON file back to Klaviyo API via a Track Call
    #Note: A requests POST should be able to do this, but I get 403 Errors for some reason (see below)
    ##requests.post('https://a.klaviyo.com/api/track?data='+enc_placed_order)
    enc_placed_order = stringToBase64(placed_order)
    post_url = 'https://a.klaviyo.com/api/track?data=%s' % (enc_placed_order)
    os.popen("curl -i "+post_url).read()

    #Uncomment below to see all orders/dictionaries (converted to strings) added to a single set/JSON
    #Current setting replaces dictionary with latest placed order read
    #Note: Could not replicate adding nested dictionaries to sets (e.g. https://stackoverflow.com/questions/34097959/add-a-dictionary-to-a-set-with-union)
    #test.add(json.dumps(placed_order))
    #print(test)

#Uncomment below to export file
#with open('placed_orders.json', 'w') as outfile:  
#    json.dump(placed_order, outfile)

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

#Just to alert the user - not neccessary for functionality
os.system("echo ========================================")
os.system("echo 'Sending Ordered Products!'")

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
        
        #Create Ordered Product Customer Key/Values
        orderedProducts.orderedProductCustomer(j)

        #Create Ordered Product Properties Key/Values    
        #Obtain properties of product and append to the ordered_product
        orderedProducts.orderedProductProperty(j)

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