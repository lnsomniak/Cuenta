import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface Product {
    id: string;
    name: string;
    brand: string | null;
    barcode: string | null;
    external_id: string | null;
    store_id: string;
    price: number;
    unit_price: string | null;
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    fiber: number;
    serving_size: string | null;
    servings_per_container: number;
    protein_per_dollar: number;
    protein_per_100cal: number;
    category: string;
    tags: string[];
    image_url: string | null;
    last_updated: string;
    created_at: string;
}

export interface Store {
    id: string;
    name: string;
    external_id: string | null;
    chain: string | null;
    zip_code: string | null;
    city: string | null;
    state: string | null;
}

export async function getProducts(options: {
    storeId?: string;
    category?: string;
    minProteinPerDollar?: number;
    limit?: number;
    orderBy?: 'protein_per_dollar' | 'protein_per_100cal' | 'price' | 'protein';
    ascending?: boolean;
} = {}) {
const {
    storeId,
    category,
    minProteinPerDollar,
    limit = 100,
    orderBy = 'protein_per_dollar',
    ascending = false,
} = options;

let query = supabase
    .from('products')
    .select('*')
    .gt('protein', 0); // I am so sleepy

if (storeId) {
    query = query.eq('store_id', storeId);
}

if (category && category !== 'all') {
    query = query.eq('category', category);
}

if (minProteinPerDollar) {
    query = query.gte('protein_per_dollar', minProteinPerDollar);
}

query = query.order(orderBy, { ascending }).limit(limit);

    const { data, error } = await query;

    if (error) {
        console.error('Error fetching products:', error);
        return [];
    }

    return data as Product[];
}

export async function getStores(chain?: string) {
let query = supabase.from('stores').select('*');

if (chain) {
    query = query.eq('chain', chain);
}

    const { data, error } = await query;

    if (error) {
    console.error('Error fetching stores:', error);
    return [];
    }

    return data as Store[];
}

export async function getCategories() {
    const { data, error } = await supabase
    .from('products')
    .select('category')
    .gt('protein', 0);

if (error) {
    console.error('Error fetching categories:', error);
    return [];
}

    const categories = [...new Set(data.map((p) => p.category))].filter(Boolean);
    return categories.sort();
}

export async function getTopProducts(limit: number = 20) {
    const { data, error } = await supabase
        .from('products')
        .select('*, stores(name, chain)')
        .gt('protein', 0)
        .order('protein_per_dollar', { ascending: false })
        .limit(limit);

if (error) {
    console.error('Error fetching top products:', error);
    return [];
}

return data;
}

export async function searchProducts(query: string, limit: number = 20) {
const { data, error } = await supabase
    .from('products')
    .select('*')
    .ilike('name', `%${query}%`)
    .gt('protein', 0)
    .order('protein_per_dollar', { ascending: false })
    .limit(limit);

    if (error) {
        console.error('Error searching products:', error);
        return [];
    } 

    return data as Product[];
}