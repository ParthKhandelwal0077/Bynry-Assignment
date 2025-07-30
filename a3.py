
@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    try:
        # Define what we mean by "recent sales activity"
        # We'll consider only sales that happened in the last 30 days
        RECENT_DAYS = 30
        recent_start = datetime.utcnow() - timedelta(days=RECENT_DAYS)

        # Step 1: Get all warehouses that belong to the given company
        warehouses = Warehouse.query.filter_by(company_id=company_id).all()
        warehouse_ids = [w.id for w in warehouses]

        # If the company has no warehouses, there can't be any stock alerts
        if not warehouse_ids:
            return jsonify({"alerts": [], "total_alerts": 0}), 200

        # Step 2: Get all inventory records for those warehouses,
        # and bring along their associated products and warehouse details
        inventory_entries = (
            db.session.query(Inventory, Product, Warehouse)
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .filter(Inventory.warehouse_id.in_(warehouse_ids))
            .all()
        )

        alerts = []

        # Step 3: Go through each inventory record and check if it's low on stock
        for inventory, product, warehouse in inventory_entries:
            # Step 3a: Check recent sales for this product in this specific warehouse
            sales_total = (
                db.session.query(func.sum(Sale.quantity))
                .filter(
                    Sale.product_id == product.id,
                    Sale.warehouse_id == warehouse.id,
                    Sale.sold_at >= recent_start
                )
                .scalar()
            )

            # If there's been no recent sales, we skip this product for alerting
            if not sales_total or sales_total == 0:
                continue

            # Step 3b: Calculate the average number of units sold per day
            avg_daily_sales = sales_total / RECENT_DAYS

            # Just a safety check to avoid dividing by zero later
            if avg_daily_sales == 0:
                continue

            # Step 4: Determine the low-stock threshold for this product
            # If the product doesn’t have a threshold set, we assume a default of 20
            threshold = getattr(product, 'low_stock_threshold', 20)

            # If the current stock is above the threshold, we’re not worried about it
            if inventory.quantity >= threshold:
                continue

            # Step 5: Estimate how many days are left before stock runs out
            # based on the current quantity and average sales rate
            days_until_stockout = int(inventory.quantity / avg_daily_sales)

            # Step 6: Fetch supplier details for this product (just the first one for now)
            supplier = (
                db.session.query(Supplier)
                .join(SupplierProduct, Supplier.id == SupplierProduct.supplier_id)
                .filter(SupplierProduct.product_id == product.id)
                .first()
            )

            # Build the supplier response block
            supplier_info = None
            if supplier:
                supplier_info = {
                    "id": supplier.id,
                    "name": supplier.name,
                    "contact_email": supplier.contact_info or "N/A"
                }

            # Add this low-stock product to our alert list
            alerts.append({
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "current_stock": inventory.quantity,
                "threshold": threshold,
                "days_until_stockout": days_until_stockout,
                "supplier": supplier_info
            })

        # Send back all the alerts found, along with a count
        return jsonify({
            "alerts": alerts,
            "total_alerts": len(alerts)
        }), 200

    except Exception as e:
        # Something went wrong — log the error and return a server error response
        return jsonify({"error": "Server error", "details": str(e)}), 500

#Edge Case Handling
#No warehouses for company -> No warehouses for company
#Products with no recent sales->Skipped
#Division by zero in sales->Skipped if avg is 0
#Missing threshold->Defaults to 20 (or configurable default)
#Database exception->500 error with message for debugging
