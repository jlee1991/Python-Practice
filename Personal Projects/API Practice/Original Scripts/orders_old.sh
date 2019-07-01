#!/bin/bash 

echo "========================================"
echo "Collecting Orders!"

echo "========================================"
echo "Sending Placed Orders!"
python placed_orders.py

echo "========================================"
echo "Sending Order Products!"
python order_products.py

