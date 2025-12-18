// Brand new file, that way it's actually the nextjs api route
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get("category");
    const storeId = searchParams.get("store_id");
    const limit = Number.parseInt(searchParams.get("limit") || "50");
    const orderBy = searchParams.get("order_by") || "protein_per_dollar";
    const minProtein = Number.parseFloat(searchParams.get("min_protein") || "0");

    try {
        let query = supabase
            .from("products")
            .select(`
                *,
                stores (
                    name,
                    chain
                )
            `)
            .gt("protein", minProtein)
            .gt("price", 0);

        if (category && category !== "all") {
            query = query.eq("category", category);
        }

        if (storeId) {
            query = query.eq("store_id", storeId);
        }

        const ascending = orderBy === "price"; // Only price sorts low-to-high
        query = query.order(orderBy, { ascending }).limit(limit);

        const { data, error } = await query;

        if (error) {
            console.error("Supabase error:", error);
            return NextResponse.json(
                { success: false, error: error.message },
                { status: 500 }
            );
        }

        return NextResponse.json({
            success: true,
            count: data?.length || 0,
            products: data || [],
        });
    } catch (e) {
        console.error("API error:", e);
        return NextResponse.json(
            { success: false, error: "Failed to fetch products" },
            { status: 500 }
        );
    }
}