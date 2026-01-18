-- =========================
-- Seed data: products (cars)
-- category = brand
-- =========================
INSERT INTO products (name, category) VALUES
  ('Toyota Corolla', 'Toyota'),
  ('Toyota Camry', 'Toyota'),
  ('Toyota Land Cruiser', 'Toyota'),

  ('Honda Civic', 'Honda'),
  ('Honda Accord', 'Honda'),
  ('Honda CR-V', 'Honda'),

  ('Nissan Altima', 'Nissan'),
  ('Nissan Rogue', 'Nissan'),
  ('Nissan GT-R', 'Nissan'),

  ('Mazda 3', 'Mazda'),
  ('Mazda CX-5', 'Mazda'),

  ('Subaru Impreza', 'Subaru'),
  ('Subaru Forester', 'Subaru')
ON CONFLICT DO NOTHING;

-- =========================
-- Seed data: features (car features)
-- =========================
INSERT INTO features (name) VALUES
  ('hybrid_engine'),
  ('all_wheel_drive'),
  ('advanced_safety'),
  ('infotainment_system'),
  ('luxury_interior'),
  ('off_road_capability'),
  ('performance_engine')
ON CONFLICT (name) DO NOTHING;

-- =========================
-- Seed relationships: product_features
-- =========================

-- Economy & Sedan features
INSERT INTO product_features (product_id, feature_id)
SELECT p.id, f.id
FROM products p, features f
WHERE p.name IN (
  'Toyota Corolla',
  'Honda Civic',
  'Mazda 3',
  'Subaru Impreza'
)
AND f.name IN ('advanced_safety','infotainment_system')
ON CONFLICT DO NOTHING;

-- Mid-range sedans & SUVs
INSERT INTO product_features (product_id, feature_id)
SELECT p.id, f.id
FROM products p, features f
WHERE p.name IN (
  'Toyota Camry',
  'Honda Accord',
  'Nissan Altima',
  'Honda CR-V',
  'Mazda CX-5',
  'Subaru Forester',
  'Nissan Rogue'
)
AND f.name IN ('advanced_safety','infotainment_system','all_wheel_drive')
ON CONFLICT DO NOTHING;

-- Hybrid models
INSERT INTO product_features (product_id, feature_id)
SELECT p.id, f.id
FROM products p, features f
WHERE p.name IN ('Toyota Corolla','Toyota Camry')
AND f.name = 'hybrid_engine'
ON CONFLICT DO NOTHING;

-- Off-road & premium SUVs
INSERT INTO product_features (product_id, feature_id)
SELECT p.id, f.id
FROM products p, features f
WHERE p.name = 'Toyota Land Cruiser'
AND f.name IN ('all_wheel_drive','off_road_capability','luxury_interior','advanced_safety')
ON CONFLICT DO NOTHING;

-- Performance vehicles
INSERT INTO product_features (product_id, feature_id)
SELECT p.id, f.id
FROM products p, features f
WHERE p.name = 'Nissan GT-R'
AND f.name IN ('performance_engine','luxury_interior','advanced_safety')
ON CONFLICT DO NOTHING;

-- =========================
-- Seed sales data (2020–2026)
-- Values represent revenue per model per year
-- =========================
WITH years AS (
  SELECT generate_series(2020, 2026) AS year
)
INSERT INTO sales (product_id, year, revenue)
SELECT
  p.id,
  y.year,
  CASE
    -- Toyota
    WHEN p.name = 'Toyota Corolla' THEN (180000 + (y.year - 2020) * 12000)
    WHEN p.name = 'Toyota Camry' THEN (220000 + (y.year - 2020) * 15000)
    WHEN p.name = 'Toyota Land Cruiser' THEN (320000 + (y.year - 2020) * 25000)

    -- Honda
    WHEN p.name = 'Honda Civic' THEN (170000 + (y.year - 2020) * 11000)
    WHEN p.name = 'Honda Accord' THEN (210000 + (y.year - 2020) * 14000)
    WHEN p.name = 'Honda CR-V' THEN (240000 + (y.year - 2020) * 16000)

    -- Nissan
    WHEN p.name = 'Nissan Altima' THEN (190000 + (y.year - 2020) * 13000)
    WHEN p.name = 'Nissan Rogue' THEN (230000 + (y.year - 2020) * 15000)
    WHEN p.name = 'Nissan GT-R' THEN (450000 + (y.year - 2020) * 30000)

    -- Mazda
    WHEN p.name = 'Mazda 3' THEN (160000 + (y.year - 2020) * 10000)
    WHEN p.name = 'Mazda CX-5' THEN (225000 + (y.year - 2020) * 14500)

    -- Subaru
    WHEN p.name = 'Subaru Impreza' THEN (165000 + (y.year - 2020) * 10500)
    WHEN p.name = 'Subaru Forester' THEN (235000 + (y.year - 2020) * 15500)

    ELSE 120000
  END::NUMERIC
FROM products p
CROSS JOIN years y
ON CONFLICT DO NOTHING;
