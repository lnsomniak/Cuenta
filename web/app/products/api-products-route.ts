import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY! // Use service key for server-side
);

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);

    const category = searchParams.get("category");
    const storeId = searchParams.get("store_id");
    const limit = parseInt(searchParams.get("limit") || "50");
    const orderBy = searchParams.get("order_by") || "protein_per_dollar";
    const minProtein = parseFloat(searchParams.get("min_protein") || "0");

    try {
    let query = supabase
        .from("products")
        .select(
        `
        *,
        stores (
            name,
            chain
        )
        `
        )
        .gt("protein", minProtein);

    if (category && category !== "all") {
        query = query.eq("category", category);
    }

    if (storeId) {
        query = query.eq("store_id", storeId);
    }

    query = query.order(orderBy, { ascending: false }).limit(limit);

    const { data, error } = await query;

    if (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({
        success: true,
        count: data.length,
        products: data,
    });
    } catch (e) {
    return NextResponse.json(
        { error: "Failed to fetch products" },
        { status: 500 }
    );
    }
}
