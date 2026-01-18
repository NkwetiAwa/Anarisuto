CREATE TABLE IF NOT EXISTS products (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS features (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS product_features (
  product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  feature_id INT NOT NULL REFERENCES features(id) ON DELETE CASCADE,
  PRIMARY KEY (product_id, feature_id)
);

CREATE TABLE IF NOT EXISTS sales (
  id SERIAL PRIMARY KEY,
  product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  year INT NOT NULL,
  revenue NUMERIC NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sales_year ON sales(year);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
