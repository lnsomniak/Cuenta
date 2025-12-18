"use client";
// reciept interface meant to be luxurious but not pretentious. that is very important.
import { useState } from "react";
import { getCurrentPosition, findNearestStores, NearbyStore } from "@/lib/geolocation";

interface BasketItem {
  id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  total_protein: number;
  total_calories: number;
  fitness_score: number;
  reason: string;
  category: string;
}

interface OptimizationResult {
  success: boolean;
  status: string;
  summary: {
    total_cost: number;
    total_protein: number;
    total_calories: number;
    budget: number;
    calorie_target: number;
    budget_utilization: string;
    calorie_achievement: string;
  };
  items: BasketItem[];
}

interface Recipe {
  id: number;
  title: string;
  image: string;
  usedIngredients: string[];
  missedIngredients: string[];
}

export default function Home() {
  const [budget, setBudget] = useState(75);
  const [calories, setCalories] = useState(2000);
  const [protein, setProtein] = useState(150);

  const [maxPerProduct, setMaxPerProduct] = useState(3);
  const [diet, setDiet] = useState<string>(""); 
  const [allergies, setAllergies] = useState<string[]>([]);

// College student mode
const [universityName, setUniversityName] = useState("");
const [selectedStore, setSelectedStore] = useState("");

  // Geolocation state
  const [nearbyStores, setNearbyStores] = useState<NearbyStore[]>([]);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [userCoords, setUserCoords] = useState<{lat: number, lon: number} | null>(null);

  const [optimizing, setOptimizing] = useState(false);
  const [loadingRecipes, setLoadingRecipes] = useState(false);

  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"basket" | "recipes">("basket");

  const API_URL=process.env.NEXT_PUBLIC_API_URL||"http://127.0.0.1:8000";

  // ============================================================================
  // GEOLOCATION HANDLER - THE MAGIC
  // ============================================================================
  const handleUseLocation = async () => {
    alert("Button clicked!");  // please work button
    console.log("Starting geolocation...");
    setLocationLoading(true);
    setLocationError(null);

    try {
      // Get user's position
      const coords = await getCurrentPosition();
      setUserCoords({ lat: coords.latitude, lon: coords.longitude });
      
      // Find nearest stores (top 5,)
      const stores = findNearestStores(coords.latitude, coords.longitude, 5);
      setNearbyStores(stores);
      
      // Auto-select the nearest store's chain
      if (stores.length > 0) {
        setSelectedStore(stores[0].chain);
      }
    } catch (err) {
      setLocationError(err instanceof Error ? err.message : "Location failed");
    } finally {
      setLocationLoading(false);
    }
  };

    // Filter nearby stores by chain when user wants to see specific chain options
  const handleFilterByChain = (chain: string) => {
    if (!userCoords) return;
    const filtered = findNearestStores(userCoords.lat, userCoords.lon, 5, chain);
    setNearbyStores(filtered);
    setSelectedStore(chain);
  };


  const handleOptimize = async () => {
    setOptimizing(true);
    setError(null);
    setRecipes([]);
    setActiveTab("basket");

    try {
      const response = await fetch(`${API_URL}/api/optimize`, { // small error fix 12/14/25 1:34am 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget,
          daily_calories: calories,
          daily_protein: protein,
          max_per_product: maxPerProduct,
          diet: diet || null, // Send null or empty string if "None" is selected
          allergies: allergies,
          university_name: universityName || null,
          selected_store: selectedStore || null,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Optimization failed");
      }

      const data: OptimizationResult = await response.json();
      setResult(data);

      if (data.success && data.items.length > 0) {
        fetchRecipes(data.items);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setOptimizing(false);
    }
  };

  const fetchRecipes = async (items: BasketItem[]) => {
    setLoadingRecipes(true);
    try {
      const ingredients = items.map((item) =>
        item.name
          .toLowerCase()
          .replaceAll(/\([^)]*\)/g, "")
          .replaceAll(/kirkwood|friendly farms.../gi, "") // this replaceall bs i had to fix
          .trim()
          .split(" ")
          .slice(0, 2)
          .join(" ")
      );
      const uniqueIngredients = Array.from(new Set(ingredients)).slice(0, 5);
      const params = new URLSearchParams();
      uniqueIngredients.forEach((ing) => params.append("ingredients", ing));
      params.append("number", "6");

      const response = await fetch(`${API_URL}/api/recipes/from-ingredients?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setRecipes(data.recipes || []);
      }
    } catch (e) {
      console.error("Failed to fetch recipes:", e);
    } finally {
      setLoadingRecipes(false);
    }
  };

  const getProteinPerDollar = (item: BasketItem) => {
    return item.total_price > 0 ? (item.total_protein / item.total_price).toFixed(1) : "0";
  };

  const getProteinPerCal = (item: BasketItem) => {
    return item.total_calories > 0 ? ((item.total_protein / item.total_calories) * 100).toFixed(1) : "0";
  };

// such an underrated feature, seeing the time is so perfect. looks SOOO good imo. 
  const receiptDate = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "2-digit",
    year: "numeric",
  });
  const receiptTime = new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
  
  const getRecipeTabLabel = () => {
  if (loadingRecipes) return "IDEAS ...";
  if (recipes.length > 0) return `IDEAS [${recipes.length}]`;
  return "IDEAS";
};

const barcodePattern = [2,1,3,1,2,1,1,3,2,1,1,2,3,1,2,1,1,2,1,3,2,1,1,2,1,3,1,2,1,1,3,2,1,2,1,1,2,3,1,2];

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
          {/* Torn top edge that will get fixed to my liking later but works for now */}
          <svg viewBox="0 0 400 15" className="w-full" style={{ backgroundColor: "#1a1a1a" }}>
            <path 
              d="M0,15 Q10,5 20,15 T40,15 T60,15 T80,15 T100,15 T120,15 T140,15 T160,15 T180,15 T200,15 T220,15 T240,15 T260,15 T280,15 T300,15 T320,15 T340,15 T360,15 T380,15 T400,15 L400,15 L0,15 Z" 
              fill="#fefefa"
            />
          </svg>

          <div className="px-6 pb-8">
            {/* Header */}
            <div className="text-center py-6 border-b-2 border-dashed border-gray-300">
              <div className="text-3xl font-bold tracking-widest mb-1">CUENTA</div>
              <div className="text-xs tracking-widest text-gray-500">GROCERY INTELLIGENCE</div>
              <div className="text-xs mt-2 text-gray-400">options, not decisions</div>
            </div>

            {/* Date/Time */}
            <div className="flex justify-between text-xs py-3 border-b border-dashed border-gray-200">
              <span>{receiptDate}</span>
              <span>{receiptTime}</span>
            </div>

            {/* Order Input Section */}
            <div className="py-4 border-b border-dashed border-gray-200">
              <div className="text-xs text-gray-500 mb-3 tracking-wider">** PARAMETERS **</div>
              
              {/* Budget Input */}
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm">WEEKLY BUDGET</span>
                <div className="flex items-center gap-1">
                  <span className="text-sm">$</span>
                  <input
                    type="number"
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                    className="w-16 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
                    style={{ backgroundColor: "transparent" }}
                  />
                </div>
              </div>

              {/* Calories Input */}
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm">DAILY CALORIES</span>
                <input
                  type="number"
                  value={calories}
                  onChange={(e) => setCalories(Number(e.target.value))}
                  className="w-20 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
                  style={{ backgroundColor: "transparent" }}
                  step={100}
                />
              </div>

              {/* Protein Input */}
              <div className="flex justify-between items-center">
                <span className="text-sm">DAILY PROTEIN (G)</span>
                <input
                  type="number"
                  value={protein}
                  onChange={(e) => setProtein(Number(e.target.value))}
                  className="w-16 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
                  style={{ backgroundColor: "transparent" }}
                  step={10}
                />
              </div>
            </div> 

    {/* Max Per Product Input */} 
    <div className="flex justify-between items-center mb-3">
        <span className="text-sm">MAX PER PRODUCT</span>
        <input
            type="number"
            value={maxPerProduct}
            onChange={(e) => setMaxPerProduct(Number(e.target.value))}
            className="w-16 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
            style={{ backgroundColor: "transparent" }}
            min={1} // Set minimum to 1, matching my backend constraint
            max={10} // Set maximum to 10, matching mt backend constraint
            step={1}
        />
    </div>

        {/* DIETARY RESTRICTION (Single Select) */}
        <div className="flex justify-between items-center mb-3">
            <span className="text-sm">DIET RESTRICTION</span>
            <select
                value={diet}
                onChange={(e) => setDiet(e.target.value)}
                className="w-24 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
                style={{ backgroundColor: "transparent" }}
            >
                <option value="">NONE</option>
                <option value="Vegan">VEGAN</option>
                <option value="Vegetarian">VEGETARIAN</option>
                <option value="Pescatarian">PESCATARIAN</option>
                <option value="Keto">KETO</option>
            </select>
        </div>

        {/* ALLERGIES (Multi Select) */}
{/* NOTE: I've learned, handling multi select in a simple <select> (because of my lack of screen real estate is tricky in React, but this is the functional way. */}
        <div className="flex justify-between items-center">
            <span className="text-sm">ALLERGY EXCLUSIONS</span>
            <select
                // The value attribute expects an array for multi-select
                value={allergies}
                // When an option is clicked, update the state array based on the selections
                onChange={(e) => {
                    const selectedOptions = Array.from(e.target.options)
                        .filter(option => option.selected)
                        .map(option => option.value);
                    setAllergies(selectedOptions);
                }}
                multiple 
                className="w-24 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900 h-10 overflow-y-auto"
                style={{ backgroundColor: "transparent" }}
            >
                <option value="Dairy">DAIRY</option>
                <option value="Eggs">EGGS</option>
                <option value="Gluten">GLUTEN</option>
                <option value="Nuts">NUTS</option>
                <option value="Soy">SOY</option>
                <option value="Fish">FISH</option>
            </select>
        </div>

        {/* ============================================================ */}
        {/* LOCATION SECTION - NOW FUNCTIONAL */}
        {/* ============================================================ */}
        <div className="py-4 border-b border-dashed border-gray-200">
            <div className="text-xs text-gray-500 mb-3 tracking-wider">** LOCATION **</div>
            
            {/* University Name/Location Input */}
            <div className="flex justify-between items-center mb-3">
                <span className="text-sm">UNIVERSITY / CITY</span>
                <input
                    type="text"
                    placeholder="e.g., Rice University"
                    value={universityName}
                    onChange={(e) => setUniversityName(e.target.value)}
                    className="w-40 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900 placeholder-gray-300"
                    style={{ backgroundColor: "transparent" }}
                />
            </div>

            {/* Nearest Store Selector (Allows Editing) */}
            <div className="flex justify-between items-center">
                <span className="text-sm">STORE CHAIN</span>
                <select
                    value={selectedStore}
                    onChange={(e) => {
                      setSelectedStore(e.target.value);
                    // filter nearby stores by the chain
                    if (userCoords && e.target.value) {
                      const filtered = findNearestStores(userCoords.lat, userCoords.lon, 5, e.target.value);
                      setNearbyStores(filtered);
                    }
                }} // this took way too long to get right for no reason
                className="w-40 bg-transparent border-b-2 border-gray-400 text-right text-sm font-bold focus:outline-none focus:border-gray-900"
                style={{ backgroundColor: "transparent" }}
                >
                  <option value="">ALL STORES</option>
                  <option value="Aldi">ALDI</option>
                  <option value="HEB">HEB</option>
                  <option value="Kroger">KROGER</option>
              </select>
          </div>

            {/* Geolocation Button (to be implemented NOW) */}
            <button
                onClick={handleUseLocation}
                disabled={locationLoading}
                className="w-full mt-4 py-2 text-xs tracking-wider border border-gray-400 disabled:opacity-50"
                style={{ color: "#1a1a1a", backgroundColor: "transparent" }}
            >
              {locationLoading ? "locating..." : "USE CURRENT LOCATION"}
            </button>

              {/* Location Error */}
              {locationError && (
                <div className="mt-2 text-xs text-center" style={{ color: "#dc2626" }}>
                  !! {locationError.toUpperCase()} !!
                </div>
              )}

              {/* Nearby Stores (shows after location found) */}
              {nearbyStores.length > 0 && (
                <div className="mt-3 pt-3 border-t border-dashed border-gray-200">
                  <div className="text-xs text-gray-500 mb-2 tracking-wider">NEARBY STORES:</div>
                  {nearbyStores.slice(0, 4).map((store) => (
                    <button
                      key={store.id}
                      onClick={() => setSelectedStore(store.chain)}
                      className="w-full text-left py-2 px-2 text-xs hover:bg-gray-100 transition-colors flex justify-between items-center"
                      style={{
                        backgroundColor: selectedStore === store.chain ? "#f0f0f0" : "transparent",
                      }}
                    >
                      <div className="flex-1">
                        <div className="font-medium">{store.name}</div>
                        <div className="text-gray-400 text-[10px]">{store.address}</div>
                      </div>
                      <span className="text-gray-500 ml-2 font-mono">
                        {store.distance.toFixed(1)} mi 
                      </span>
                    </button>
                  ))}
                  
                  {/* Quick chain filters */}
                  {userCoords && (
                    <div className="flex gap-2 mt-3 pt-2 border-t border-gray-100">
                      <button
                        onClick={() => {
                          const all = findNearestStores(userCoords.lat, userCoords.lon, 5);
                          setNearbyStores(all);
                          setSelectedStore("");
                        }}
                        className="flex-1 py-1 text-[10px] border border-gray-300 hover:bg-gray-100"
                        style={{ backgroundColor: selectedStore ? "#f0f0f0" : "transparent" }}
                      >
                        ALL
                      </button>
                      {["Kroger", "HEB", "Aldi"].map((chain) => (
                        <button
                          key={chain}
                          onClick={() => handleFilterByChain(chain)}
                          className="flex-1 py-1 text-[10px] border border-gray-300 hover:bg-gray-100"
                          style={{ backgroundColor: selectedStore === chain ? "#f0f0f0" : "transparent" }}
                        >
                          {chain.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Optimize Button */}
            <div className="py-4 border-b border-dashed border-gray-200">
              <button
                onClick={handleOptimize}
                disabled={optimizing}
                className="w-full py-3 text-sm tracking-widest transition-colors disabled:opacity-50"
                style={{ 
                  backgroundColor: "#1a1a1a", 
                  color: "#fefefa",
                }}
              >
                {optimizing ? "Building your mealplan..." : "[ Ready? ]"} 
              </button>
            </div>

            {/* JIC. */}
            {error && (
              <div className="py-3 text-center text-xs border-b border-dashed border-gray-200" style={{ color: "#dc2626" }}>
                !! ERROR: {error.toUpperCase()} !!
              </div>
            )}

            {/* Results */}
            {result && result.success && (
              <>
                {/* Tabs */}
                <div className="flex border-b border-dashed border-gray-200">
                  <button
                    onClick={() => setActiveTab("basket")}
                    className="flex-1 py-3 text-xs tracking-wider transition-colors"
                    style={{ 
                      backgroundColor: activeTab === "basket" ? "#1a1a1a" : "transparent",
                      color: activeTab === "basket" ? "#fefefa" : "#1a1a1a"
                    }}
                  >
                  BASKET [{result.items.length}]
                </button>
                <button
                  onClick={() => setActiveTab("recipes")}
                  className="flex-1 py-3 text-xs tracking-wider transition-colors"
                  style={{ 
                    backgroundColor: activeTab === "recipes" ? "#1a1a1a" : "transparent",
                    color: activeTab === "recipes" ? "#fefefa" : "#1a1a1a"
                  }}
                >
                  {getRecipeTabLabel()}
                </button>
              </div>

                {/* Basket Tab */}
                {activeTab === "basket" && (
                  <>
                    {/* Efficiency Legend */}
                    <div className="py-3 border-b border-gray-200 text-xs text-gray-500">
                      <div className="flex justify-between">
                        <span>g/$ = protein per dollar</span>
                        <span>g/c = protein per 100cal</span>
                      </div>
                    </div>

                    {/* Items */}
                    <div className="py-2">
                      {result.items.map((item, index) => (
                        <div key={item.id} className="py-3 border-b border-gray-100">
                          <div className="flex justify-between text-sm">
                            <span className="flex-1 pr-2 font-medium">
                              {item.name.toUpperCase().slice(0, 26)}
                              {item.name.length > 26 && "..."}
                            </span>
                            <span className="font-bold">${item.total_price.toFixed(2)}</span>
                          </div>
                          
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>{item.quantity}x @ ${item.unit_price.toFixed(2)}</span>
                            <span className="text-gray-400">#{String(index + 1).padStart(3, "0")}</span>
                          </div>
                          
                          {/* Efficiency Metrics */}
                          <div className="flex justify-between text-xs mt-2 pt-2 border-t border-gray-100">
                            <span>
                              <span className="text-gray-400">{item.total_protein.toFixed(0)}g protein</span>
                            </span>
                            <span className="flex gap-3">
                              <span className="font-medium" style={{ color: "#059669" }}>
                                {getProteinPerDollar(item)} g/$
                              </span>
                              <span className="font-medium" style={{ color: "#2563eb" }}>
                                {getProteinPerCal(item)} g/c
                              </span>
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Divider */}
                    <div className="border-t-2 border-dashed border-gray-300 my-2" />

                    {/* Totals */}
                    <div className="py-2 space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>SUBTOTAL</span>
                        <span>${result.summary.total_cost.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-gray-500">
                        <span>BUDGET</span>
                        <span>${result.summary.budget.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-gray-500">
                        <span>REMAINING</span>
                        <span>${(result.summary.budget - result.summary.total_cost).toFixed(2)}</span>
                      </div>
                    </div>

                    {/* Double line divider */}
                    <div className="border-t-4 border-double border-gray-400 my-2" />

                    {/* Total */}
                    <div className="py-2">
                      <div className="flex justify-between text-lg font-bold">
                        <span>TOTAL</span>
                        <span>${result.summary.total_cost.toFixed(2)}</span>
                      </div>
                    </div>

                    <div className="border-t border-dashed border-gray-200 my-2" />

                    {/* Aggregate Metrics */}
                    <div className="py-2 text-xs space-y-2">
                      <div className="text-gray-500 tracking-wider mb-3">** WEEKLY SUMMARY **</div>
                      
                      <div className="flex justify-between">
                        <span>TOTAL PROTEIN</span>
                        <span className="font-bold">{Math.round(result.summary.total_protein)}G</span>
                      </div>
                      <div className="flex justify-between text-gray-500">
                        <span>  └─ daily average</span>
                        <span>{Math.round(result.summary.total_protein / 7)}g</span>
                      </div>
                      
                      <div className="flex justify-between mt-2">
                        <span>TOTAL CALORIES</span>
                        <span className="font-bold">{result.summary.total_calories.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-gray-500">
                        <span>  └─ daily average</span>
                        <span>{Math.round(result.summary.total_calories / 7).toLocaleString()}</span>
                      </div>

                      {/* Aggregate Efficiency */}
                      <div className="border-t border-gray-200 mt-3 pt-3">
                        <div className="flex justify-between">
                          <span>OVERALL g/$</span>
                          <span className="font-bold" style={{ color: "#059669" }}>
                            {(result.summary.total_protein / result.summary.total_cost).toFixed(1)}
                          </span>
                        </div>
                        <div className="flex justify-between mt-1">
                          <span>OVERALL g/100cal</span>
                          <span className="font-bold" style={{ color: "#2563eb" }}>
                            {((result.summary.total_protein / result.summary.total_calories) * 100).toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="border-t border-dashed border-gray-200 my-2" />
                    <div className="py-3 text-center">
                      <div className="text-xs text-gray-500 mb-1">BUDGET UTILIZATION</div>
                      <div className="text-xl font-bold">{result.summary.budget_utilization}</div>
                    </div>
                  </>
                )}

                {/* Recipes Tab */}
                {activeTab === "recipes" && (
                  <div className="py-4">
                    {loadingRecipes && (
                      <div className="text-center py-8 text-sm text-gray-500">
                        FINDING IDEAS...
                      </div>
                    )}
                    {!loadingRecipes&&recipes.length>0&&(
                      <div className="space-y-4">
                        <div className="text-xs text-gray-500 tracking-wider">** MEAL IDEAS **</div>
                        <div className="text-xs text-gray-400 -mt-2 mb-3">
                          based on your basket ingredients
                        </div>
                        {recipes.map((recipe, index) => (
                          <div key={recipe.id} className="border border-dashed border-gray-300 p-3">
                            <div className="flex gap-3">
                              {recipe.image && (
                                <img
                                  src={recipe.image}
                                  alt={recipe.title}
                                  className="w-16 h-16 object-cover grayscale hover:grayscale-0 transition-all"
                                />
                              )}
                              <div className="flex-1 min-w-0">
                                <div className="text-xs text-gray-400">#{String(index + 1).padStart(2, "0")}</div>
                                <div className="text-sm font-bold leading-tight mt-0.5">
                                  {recipe.title.toUpperCase().slice(0, 32)}
                                  {recipe.title.length > 32 && "..."}
                                </div>
                                {recipe.usedIngredients.length > 0 && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    ✓ have: {recipe.usedIngredients.slice(0, 2).join(", ")}
                                    {recipe.usedIngredients.length > 2 && ` +${recipe.usedIngredients.length - 2}`}
                                  </div>
                                )}
                                {recipe.missedIngredients.length > 0 && (
                                  <div className="text-xs text-gray-400 mt-0.5">
                                    + need: {recipe.missedIngredients.slice(0, 2).join(", ")}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {!loadingRecipes&&recipes.length===0&&(
                      <div className="text-center py-8 text-sm text-gray-500">
                        NO RECIPES FOUND
                      </div>
                    )}
                  </div>
                )}

               {/* Barcode */}
                <div className="border-t border-dashed border-gray-200 mt-4 pt-4">
                  <div className="flex justify-center items-end gap-px h-12">
                    {barcodePattern.map((w, i) => (
                      <div 
                        key={`bar-${i}-${w}`}
                        className="h-full" 
                        style={{ 
                          width: `${w * 2}px`,
                          backgroundColor: "#1a1a1a"
                        }}
                      />
                    ))}
                  </div>
                  <div className="text-center text-xs text-gray-400 mt-2 tracking-widest">
                    {Date.now().toString().slice(-12)}
                  </div>
                </div>

                {/* Footer Message */}
                <div className="text-center py-4 text-xs text-gray-500">
                  <div>THE DATA IS YOURS</div>
                  <div className="mt-1 text-gray-400">the decision is too</div>
                </div>
              </>
            )}

            {/* Empty State */}
            {!result && !optimizing && (
              <div className="py-8 text-center">
                <div className="text-4xl mb-3">📊</div>
                <div className="text-sm text-gray-600">SET YOUR PARAMETERS</div>
                <div className="text-xs text-gray-400 mt-1">then run optimization</div>
                <div className="text-xs text-gray-300 mt-4 max-w-xs mx-auto">
                  cuenta shows you the tradeoffs.<br/>
                  you make the call.
                </div>
              </div>
            )}

            {/* Store Hours Footer, more dynamic based on your selection */}
            <div className="border-t border-dashed border-gray-200 mt-4 pt-4 text-center text-xs text-gray-400">
              <div>
                {selectedStore ? `${selectedStore.toUpperCase()} • ` : ""}
                HOUSTON TX
              </div>
            <div className="mt-1 tracking-wider">CUENTA.APP</div>
          </div>
        </div>

          {/* Torn bottom edge needs to get fixed but frontend isn't my realm*/}
          <svg viewBox="0 0 400 15" className="w-full" style={{ backgroundColor: "#1a1a1a" }}>
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