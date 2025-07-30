


#the first thing I notied is the post the queries in the initial snippet were made consecutively without taking in consideration about what would happen if the first query failed and the second got executed or vice versa , and one would not be able to rollback the changes . This would create inconsistencies in database.

#This consideration opened a lot of thinking about how the snippet is void of data validation which is coming with the request .

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Check if we are getting all the required fields for the query to be made, if any of the field is mission we can instantly throw an error .

    # This is a good practice but usually during the client side form we already use for validation  before making the request 
    required_fields = ['name', 'sku', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Validating price to check if it is a number and not negative and throwing an error if it is not
    try:
        price = float(data['price'])
        if price < 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid price format"}), 400

    # SKU uniqueness check
    existing = Product.query.filter_by(sku=data['sku']).first()
    if existing:
        return jsonify({"error": "SKU already exists"}), 409

    # Creating product but not copling warehouses with each product, since we are assuming that a product might be place in several warehouses and so we updated the original snippet.
    product = Product(
        name=data['name'],
        sku=data['sku'],
        price=price
    )
    # Making sure that we are not commit the changes here and commit them after all the queries has been made for consistencies in database
    db.session.add(product)

    try:
        db.session.flush()  # get product.id before commit
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to create product"}), 500

    # Optionally handle inventory because I assumed that it's not always that the product creation will be followed by inventory creation and so I updated the original snippet and added an if clause.
    if 'warehouse_id' in data and 'initial_quantity' in data:
        try:
            #sinple validation which the original snippets were missing 
            quantity = int(data['initial_quantity'])
            if quantity < 0:
                raise ValueError()
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify({"error": "Invalid initial quantity"}), 400

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=quantity
        )
        db.session.add(inventory)

    try:
        #commiting the changes after all the queries has been made for consistencies in database
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database error during commit"}), 500

    return jsonify({"message": "Product created", "product_id": product.id}), 201


#Here are few of the assumptions I made while updating the original code snippet.
#initial_quantity is optional
#product can exist in multiple warehouses



