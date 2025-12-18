-- 1. Clear out the existing mess
TRUNCATE TABLE stores CASCADE;

-- 2. Insert the "Golden Record" locations (Clean & Verified)
INSERT INTO stores (name, store_id, zip_code, city, state, address) VALUES
-- Aldi
('Aldi - Houston Old Spanish Trail', 'aldi-houston-ost', '77021', 'Houston', 'TX', '3618 Old Spanish Trl'),
('Aldi - Houston Almeda Genoa', 'aldi-houston-almeda-genoa', '77075', 'Houston', 'TX', '10064 Almeda Genoa Rd'),
('Aldi - Houston Gessner', 'aldi-houston-gessner', '77080', 'Houston', 'TX', '2550 Gessner Rd'),

-- Target
('Target - Houston Braeswood', '0761', '77025', 'Houston', 'TX', '8500 Main St'),
('Target - Houston Central', '2093', '77007', 'Houston', 'TX', '2580 Shearn St'),
('Target - Houston Montrose', '3375', '77098', 'Houston', 'TX', '2075 Westheimer Rd'),

-- Kroger
('Kroger - Houston OST', '03400605', '77054', 'Houston', 'TX', '1990 Old Spanish Trl'),
('Kroger - Houston Montrose', '03400243', '77006', 'Houston', 'TX', '3300 Montrose Blvd'),
('Kroger - Houston Kirby', '03400740', '77030', 'Houston', 'TX', '7747 Kirby Dr');