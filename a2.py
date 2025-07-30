#1. Companies
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

#2. Warehouses
#I have assumne that each warehouse is only associated with one company
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

#3. Products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    #unique because I am assuming different companies cannot have products with same skus
    sku VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    is_bundle BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

# 4. Product Bundles (self-referencing many-to-many)
CREATE TABLE product_bundle_items (
    #this here handles self-referencing bundles with quantities
    bundle_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (bundle_id, item_id)
);

# 5. Inventory (tracks product quantity at each warehouse)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 0),
    #Prevents duplicate entries and ensures 1 record per combo
    UNIQUE (product_id, warehouse_id)  -- A product can only exist once per warehouse
);

# 6. Inventory History (audit trail for changes in quantity)
CREATE TABLE inventory_history (
    id SERIAL PRIMARY KEY,
    inventory_id INT NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    change INT NOT NULL,  -- + or - value
    reason VARCHAR(255),  -- e.g., "stock-in", "sale", "adjustment"
    changed_at TIMESTAMP DEFAULT NOW()
);

# 7. Suppliers
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

# 8. Supplier Products (many-to-many between suppliers and products)
CREATE TABLE supplier_products (
    supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (supplier_id, product_id)
);


#Potential Questions:
#1) Can different companies can have different products with same SKUs?
#2) Can a warehouse be associated with multiple companies?
#3) Additonally we haven't taken in consideration the user schema who will be accounting, so should I store who made the change (user tracking) 
#4) I have assumed that bundles would not be actualy kept in the warehouse shelf as a bundle of products, and the bundle would be actually created and maintained virtually only , so I have created many to many relationship with bundles and products, this would give bundles a specific SKUs and as well maintain all the different product in it . Should I treat bundle as a single product placed within the shelf .
# Can bundles be nested (bundle within bundle)?
# Can one supplier supply the same product to multiple companies at different prices?
# can differnt suppliers supply the same product at different prices ?

