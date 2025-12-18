"use client";

import { useState, useEffect } from "react";

interface Product {
    id: string;
    name: string;
    brand: string | null;
    price: number;
    calories: number;
    protein: number;
    protein_per_dollar: number;
    protein_per_100cal: number;
    category: string;
    serving_size: string | null;
    servings_per_container: number;
    image_url: string | null;
    stores?: {
    name: string;
    chain: string;
    };
}

const CATEGORIES = [
    { value: "all", label: "ALL" },
    { value: "meat", label: "MEAT" },
    { value: "seafood", label: "SEAFOOD" },
    { value: "dairy", label: "DAIRY" },
    { value: "eggs", label: "EGGS" },
    { value: "protein", label: "PROTEIN" },
    { value: "plant", label: "PLANT" },
    { value: "other", label: "OTHER" },
];

export default function BrowsePage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [category, setCategory] = useState("all");
    const [sortBy, setSortBy] = useState("protein_per_dollar");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchProducts();
    }, [category, sortBy]);

    const fetchProducts = async () => {
        setLoading(true);
        setError(null);

    try {
    const params = new URLSearchParams({
        limit: "100",
        order_by: sortBy,
        min_protein: "1",
    });

    if (category !== "all") {
        params.append("category", category);
    }

    const response = await fetch(`/api/products?${params.toString()}`);
    const data = await response.json();

    if (data.success) {
        setProducts(data.products);
    } else {
        setError(data.error || "Failed to load products");
    }
    } catch (e) {
        setError("Failed to connect to server");
    } finally {
        setLoading(false);
    }
};

const receiptDate = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "2-digit",
    year: "numeric",
});

return (
    <main
    className="min-h-screen flex items-start justify-center p-4 md:p-8"
    style={{ backgroundColor: "#1a1a1a" }}
    >
    <div className="w-full max-w-md">
        <div
        className="shadow-2xl relative"
        style={{
            backgroundColor: "#fefefa",
            fontFamily: "'Courier New', Courier, monospace",
            color: "#1a1a1a",
        }}
        >
        <svg
            viewBox="0 0 400 15"
            className="w-full"
            style={{ backgroundColor: "#1a1a1a" }}
        >
            <path
            d="M0,15 Q10,5 20,15 T40,15 T60,15 T80,15 T100,15 T120,15 T140,15 T160,15 T180,15 T200,15 T220,15 T240,15 T260,15 T280,15 T300,15 T320,15 T340,15 T360,15 T380,15 T400,15 L400,15 L0,15 Z"
            fill="#fefefa"
            />
        </svg>

    <div className="px-6 pb-8">
        <div className="text-center py-6 border-b-2 border-dashed border-gray-300">
            <div className="text-3xl font-bold tracking-widest mb-1">
                CUENTA
            </div>
            <div className="text-xs tracking-widest text-gray-500">
                PRODUCT CATALOG
            </div>
            <div className="text-xs mt-2 text-gray-400">
                {products.length} high-protein products
            </div>
        </div>
        <div className="flex justify-between text-xs py-3 border-b border-dashed border-gray-200">
            <span>{receiptDate}</span>
            <span>LIVE DATA</span>
        </div>

        <div className="py-4 border-b border-dashed border-gray-200">
            <div className="text-xs text-gray-500 mb-3 tracking-wider">
                ** FILTERS **
            </div>

            <div className="flex justify-between items-center mb-3">
                <span className="text-sm">CATEGORY</span>
                <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-28 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none"
                    style={{ backgroundColor: "transparent" }}
                >
            {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                    {cat.label}
                    </option>
                ))}
            </select>
        </div>

            <div className="flex justify-between items-center">
                <span className="text-sm">SORT BY</span>
                <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-28 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none"
                    style={{ backgroundColor: "transparent" }}
                >
                    <option value="protein_per_dollar">G/$</option>
                    <option value="protein_per_100cal">G/100CAL</option>
                    <option value="protein">PROTEIN</option>
                    <option value="price">PRICE</option>
                </select>
            </div>
        </div>

        <div className="py-3 border-b border-gray-200 text-xs text-gray-500">
            <div className="flex justify-between">
                <span>g/$ = protein per dollar</span>
                <span>g/c = protein per 100cal</span>
            </div>
        </div>

            {loading && (
            <div className="py-12 text-center">
                <div className="text-sm text-gray-500">LOADING...</div>
            </div>
        )}

            {error && (
            <div
                className="py-4 text-center text-xs"
                style={{ color: "#dc2626" }}
            >
                !! {error.toUpperCase()} !!
            </div>
        )}

            {!loading && !error && (
            <div className="py-2">
                {products.map((product, index) => (
                <div
                    key={product.id}
                    className="py-3 border-b border-gray-100"
                >
                    <div className="flex justify-between text-sm">
                    <span className="flex-1 pr-2 font-medium">
                        {product.name.toUpperCase().slice(0, 28)}
                        {product.name.length > 28 && "..."}
                    </span>
                    <span className="font-bold">
                        ${product.price.toFixed(2)}
                    </span>
                </div>

                <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>
                        {product.brand || product.category.toUpperCase()}
                </span>
                    <span className="text-gray-400">
                        #{String(index + 1).padStart(3, "0")}
                    </span>
                </div>

                <div className="flex justify-between text-xs mt-2 pt-2 border-t border-gray-100">
                    <span>
                        <span className="text-gray-400">
                        {product.protein.toFixed(0)}g protein •{" "}
                        {product.calories} cal
                    </span>
                </span>
                    <span className="flex gap-3">
                        <span
                        className="font-bold"
                        style={{ color: "#059669" }}
                        >
                        {product.protein_per_dollar?.toFixed(1) || "0"} g/$
                    </span>
                    <span
                        className="font-bold"
                        style={{ color: "#2563eb" }}
                        >
                        {product.protein_per_100cal?.toFixed(1) || "0"} g/c
                        </span>
                    </span>
                </div>
            </div>
        ))}
            </div>
        )}

            {!loading && !error && products.length === 0 && (
            <div className="py-12 text-center">
                <div className="text-4xl mb-3">🔍</div>
                <div className="text-sm text-gray-600">NO PRODUCTS FOUND</div>
                <div className="text-xs text-gray-400 mt-1">
                try a different category
                </div>
            </div>
        )}

            {!loading && products.length > 0 && (
            <>
        <div className="border-t-2 border-dashed border-gray-300 my-4" />
            <div className="py-2 text-xs space-y-2">
                <div className="text-gray-500 tracking-wider mb-3">
                    ** CATALOG STATS **
                </div>
            <div className="flex justify-between">
                <span>PRODUCTS SHOWN</span>
                <span className="font-bold">{products.length}</span>
                    </div>
                <div className="flex justify-between">
                    <span>AVG PROTEIN/DOLLAR</span>
                    <span className="font-bold" style={{ color: "#059669" }}>
                {(
                    products.reduce(
                        (sum, p) => sum + (p.protein_per_dollar || 0),
                            0
                        ) / products.length
                    ).toFixed(1)}{" "}
                    g/$
                </span>
            </div>
            <div className="flex justify-between">
                    <span>TOP EFFICIENCY</span>
                    <span className="font-bold" style={{ color: "#059669" }}>
                    {Math.max(
                        ...products.map((p) => p.protein_per_dollar || 0)
                    ).toFixed(1)}{" "}
                    g/$
                    </span>
                </div>
            </div>
        </>
            )}
            <div className="border-t border-dashed border-gray-200 mt-4 pt-4 text-center text-xs text-gray-400">
                <div>KROGER • HOUSTON TX</div>
                <div className="mt-1 tracking-wider">CUENTA.APP</div>
            </div>
        </div>
        <svg
            viewBox="0 0 400 15"
            className="w-full"
            style={{ backgroundColor: "#1a1a1a" }}
        >
        <path
            d="M0,0 Q10,10 20,0 T40,0 T60,0 T80,0 T100,0 T120,0 T140,0 T160,0 T180,0 T200,0 T220,0 T240,0 T260,0 T280,0 T300,0 T320,0 T340,0 T360,0 T380,0 T400,0 L400,0 L0,0 Z"
            fill="#fefefa"
            />
            </svg>
        </div>
    </div>
</main>
);
}