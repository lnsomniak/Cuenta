-- ============================================================================
-- CUENTA MVP: Seed Data
-- ============================================================================
-- Realistic ALDI products with actual-ish nutritional data
-- Ran AFTER schema.sql my god why do i forget.
-- ============================================================================

INSERT INTO products (name, price, calories, protein, carbs, fat, fiber, serving_size, servings_per_container, category) VALUES

-- taken directly from aldi.com fight me
('Kirkwood Chicken Breast (3 lb)', 8.99, 120, 26, 0, 1.5, 0, '4 oz', 12, 'Protein'),
('Kirkwood Chicken Thighs (3 lb)', 5.99, 180, 22, 0, 10, 0, '4 oz', 12, 'Protein'),
('Never Any! Ground Turkey 93/7', 5.49, 170, 21, 0, 9, 0, '4 oz', 4, 'Protein'),
('Fresh Ground Beef 80/20', 5.99, 290, 19, 0, 23, 0, '4 oz', 4, 'Protein'),
('Fresh Ground Beef 93/7', 6.99, 170, 22, 0, 9, 0, '4 oz', 4, 'Protein'),
('Fremont Fish Market Tilapia (2 lb)', 7.99, 110, 23, 0, 2, 0, '4 oz', 8, 'Protein'),
('Fremont Fish Market Salmon Fillets', 8.99, 180, 25, 0, 8, 0, '4 oz', 4, 'Protein'),
('Appleton Farms Bacon (16 oz)', 5.49, 80, 6, 0, 6, 0, '2 slices', 16, 'Protein'),
('Park Street Deli Rotisserie Chicken', 6.49, 140, 19, 1, 7, 0, '3 oz', 10, 'Protein'),
('Casa Mamita Carnitas', 6.99, 210, 16, 4, 14, 0, '4 oz', 4, 'Protein'),
('Goldhen Large Eggs (18 ct)', 3.29, 70, 6, 0, 5, 0, '1 egg', 18, 'Dairy'),
('Goldhen Large Eggs (36 ct)', 5.99, 70, 6, 0, 5, 0, '1 egg', 36, 'Dairy'),
('Friendly Farms Greek Yogurt (32 oz)', 4.49, 100, 17, 6, 0, 0, '1 cup', 4, 'Dairy'),
('Friendly Farms Cottage Cheese (24 oz)', 2.99, 110, 13, 5, 4, 0, '1/2 cup', 6, 'Dairy'),
('Happy Farms String Cheese (24 ct)', 6.99, 80, 7, 1, 6, 0, '1 stick', 24, 'Dairy'),
('Happy Farms Shredded Mozzarella (32 oz)', 6.49, 80, 7, 1, 6, 0, '1/4 cup', 32, 'Dairy'),
('Friendly Farms Whole Milk (gallon)', 3.49, 150, 8, 12, 8, 0, '1 cup', 16, 'Dairy'),
('Friendly Farms 2% Milk (gallon)', 3.29, 120, 8, 12, 5, 0, '1 cup', 16, 'Dairy'),
('Simply Nature Organic Brown Rice (2 lb)', 3.29, 170, 4, 35, 1.5, 2, '1/4 cup dry', 18, 'Grains'),
('Specially Selected Jasmine Rice (5 lb)', 5.99, 160, 3, 36, 0, 0, '1/4 cup dry', 45, 'Grains'),
('Barilla Pasta (16 oz)', 1.29, 200, 7, 42, 1, 2, '2 oz dry', 8, 'Grains'),
('L''Oven Fresh Whole Wheat Bread', 1.99, 70, 4, 13, 1, 2, '1 slice', 20, 'Grains'),
('Millville Old Fashioned Oats (42 oz)', 2.99, 150, 5, 27, 3, 4, '1/2 cup dry', 30, 'Grains'),
('Mama Cozzi''s Pizza Dough', 1.49, 150, 5, 28, 2, 1, '1/6 dough', 6, 'Grains'),
('Tortillas Flour (10 ct)', 2.29, 140, 3, 24, 3, 1, '1 tortilla', 10, 'Grains'),
('Simply Nature Quinoa (16 oz)', 4.49, 170, 6, 29, 2.5, 3, '1/4 cup dry', 12, 'Grains'),
('Bananas (bunch ~3 lb)', 1.49, 105, 1, 27, 0, 3, '1 medium', 7, 'Produce'),
('Sweet Potatoes (3 lb bag)', 2.99, 112, 2, 26, 0, 4, '1 medium', 5, 'Produce'),
('Russet Potatoes (5 lb bag)', 2.99, 160, 4, 37, 0, 4, '1 medium', 8, 'Produce'),
('Baby Spinach (16 oz)', 3.99, 7, 1, 1, 0, 1, '1 cup', 16, 'Produce'),
('Broccoli Crowns (per lb)', 1.69, 55, 4, 11, 0, 4, '1 cup', 3, 'Produce'),
('Frozen Broccoli Florets (12 oz)', 1.29, 30, 3, 6, 0, 2, '1 cup', 3, 'Produce'),
('Frozen Mixed Vegetables (12 oz)', 1.19, 60, 2, 12, 0, 2, '1 cup', 3, 'Produce'),
('Avocados (each)', 0.89, 234, 3, 12, 21, 10, '1 avocado', 1, 'Produce'),
('Roma Tomatoes (per lb)', 1.29, 11, 1, 2, 0, 1, '1 tomato', 4, 'Produce'),
('Yellow Onions (3 lb bag)', 2.49, 44, 1, 10, 0, 2, '1 medium', 6, 'Produce'),
('Dakota''s Pride Black Beans (15 oz)', 0.79, 110, 7, 20, 0, 7, '1/2 cup', 3.5, 'Legumes'),
('Dakota''s Pride Pinto Beans (15 oz)', 0.79, 110, 6, 20, 0, 6, '1/2 cup', 3.5, 'Legumes'),
('Dakota''s Pride Chickpeas (15 oz)', 0.89, 120, 6, 20, 2, 5, '1/2 cup', 3.5, 'Legumes'),
('Simply Nature Organic Lentils (16 oz)', 2.49, 170, 12, 30, 0, 8, '1/4 cup dry', 13, 'Legumes'),
('Southern Grove Peanut Butter (28 oz)', 3.49, 190, 7, 7, 16, 2, '2 tbsp', 26, 'Legumes'),
('Simply Nature Organic Tofu (14 oz)', 2.29, 90, 10, 2, 5, 1, '3 oz', 4.5, 'Legumes'),
('Elevation Protein Bars (5 ct)', 5.99, 200, 20, 22, 7, 5, '1 bar', 5, 'Snacks'),
('Southern Grove Almonds (16 oz)', 5.99, 170, 6, 6, 15, 3, '1 oz', 16, 'Snacks'),
('Clancy''s Tortilla Chips (13 oz)', 1.99, 140, 2, 19, 7, 1, '1 oz', 13, 'Snacks'),
('Fit & Active Rice Cakes', 1.99, 35, 1, 7, 0, 0, '1 cake', 14, 'Snacks'),
('Specially Selected Olive Oil (17 oz)', 4.99, 120, 0, 0, 14, 0, '1 tbsp', 33, 'Pantry'),
('Burman''s Honey (12 oz)', 3.99, 60, 0, 17, 0, 0, '1 tbsp', 24, 'Pantry'),
('Stonemill Seasonings (various)', 1.29, 0, 0, 0, 0, 0, '1/4 tsp', 50, 'Pantry'),
('SimplyNature Almond Milk (64 oz)', 2.79, 30, 1, 1, 2.5, 0, '1 cup', 8, 'Dairy');

-- verified after writing all this ^ I could've used AI but I refuse to succumb. 
SELECT 
    category,
    COUNT(*) as products,
    ROUND(AVG(protein_per_dollar)::numeric, 1) as avg_protein_per_dollar,
    ROUND(AVG(price)::numeric, 2) as avg_price
FROM products
GROUP BY category
ORDER BY avg_protein_per_dollar DESC;
