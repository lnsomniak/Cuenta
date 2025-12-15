-- ============================================================================
-- CUENTA MVP: Complete Schema
-- ============================================================================

-- PG VECTOR IMPLEMENTED ALREADY BECAUSE WHY WOULD WE EVER USE MYSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PRODUCTS TABLE (ALDI inventory)
-- ============================================================================
-- Recipes cached from API
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spoonacular_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    image_url TEXT,
    prep_minutes INTEGER,
    servings INTEGER,
    calories_per_serving INTEGER,
    protein_per_serving FLOAT,
    carbs_per_serving FLOAT,
    fat_per_serving FLOAT,
    cost_per_serving FLOAT,
    cached_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recipe ingredients mapped to our products
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),  -- nullable if no ALDI match
    ingredient_name TEXT NOT NULL,            -- original from API
    quantity FLOAT,
    unit TEXT
);

-- User's saved meal plans
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meal_plan_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id UUID REFERENCES recipes(id),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack'))
);

-- ============================================================================
-- ROW LEVEL SECURITY AS A MEASURE THAT WILL GET IMPLEMENTED. 
-- ============================================================================
-- RLS policies
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Recipes are public" ON recipes FOR SELECT USING (true);

ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their meal plans" ON meal_plans 
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE meal_plan_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access their meal plan items" ON meal_plan_items
    FOR ALL USING (
        meal_plan_id IN (SELECT id FROM meal_plans WHERE user_id = auth.uid())
    );

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_protein_per_dollar ON products(protein_per_dollar DESC);
CREATE INDEX IF NOT EXISTS idx_baskets_user_id ON baskets(user_id);
CREATE INDEX IF NOT EXISTS idx_basket_items_basket_id ON basket_items(basket_id);

-- ============================================================================
-- AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
