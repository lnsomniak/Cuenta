"use client";

import { useState } from "react";

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

export default function Home() {
  const [budget, setBudget] = useState(75);
  const [calories, setCalories] = useState(2000);
  const [protein, setProtein] = useState(150);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget,
          daily_calories: calories,
          daily_protein: protein,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Optimization failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      Protein: "bg-red-100 text-red-800",
      Dairy: "bg-blue-100 text-blue-800",
      Grains: "bg-amber-100 text-amber-800",
      Produce: "bg-green-100 text-green-800",
      Legumes: "bg-orange-100 text-orange-800",
      Snacks: "bg-purple-100 text-purple-800",
      Pantry: "bg-gray-100 text-gray-800",
    };
    return colors[category] || "bg-gray-100 text-gray-800";
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return "bg-green-500";
    if (score >= 50) return "bg-blue-500";
    if (score >= 30) return "bg-amber-500";
    return "bg-gray-400";
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">🛒 Fit-Econ</h1>
          <p className="text-gray-600 mt-1">
            AI-optimized grocery lists for your fitness goals
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Input Card */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Your Goals
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Budget */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Weekly Budget
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                  $
                </span>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min={20}
                  max={500}
                />
              </div>
            </div>

            {/* Calories */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Daily Calories
              </label>
              <input
                type="number"
                value={calories}
                onChange={(e) => setCalories(Number(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min={1200}
                max={5000}
                step={100}
              />
            </div>

            {/* Protein */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Daily Protein (g)
              </label>
              <input
                type="number"
                value={protein}
                onChange={(e) => setProtein(Number(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min={50}
                max={400}
                step={10}
              />
            </div>
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className="mt-6 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Optimizing...
              </span>
            ) : (
              "Optimize My Basket"
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8">
            <p className="font-medium">Optimization Failed</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && result.success && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-xl border p-4">
                <p className="text-sm text-gray-500">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${result.summary.total_cost}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  {result.summary.budget_utilization} of budget
                </p>
              </div>

              <div className="bg-white rounded-xl border p-4">
                <p className="text-sm text-gray-500">Weekly Protein</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(result.summary.total_protein)}g
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {Math.round(result.summary.total_protein / 7)}g/day
                </p>
              </div>

              <div className="bg-white rounded-xl border p-4">
                <p className="text-sm text-gray-500">Weekly Calories</p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.summary.total_calories.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {result.summary.calorie_achievement} of target
                </p>
              </div>

              <div className="bg-white rounded-xl border p-4">
                <p className="text-sm text-gray-500">Items</p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.items.length}
                </p>
                <p className="text-xs text-gray-500 mt-1">products selected</p>
              </div>
            </div>

            {/* Item List */}
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b bg-gray-50">
                <h3 className="font-semibold text-gray-900">
                  Your Optimized Basket
                </h3>
              </div>

              <div className="divide-y">
                {result.items.map((item) => (
                  <div key={item.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start gap-4">
                      {/* Score Badge */}
                      <div
                        className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold ${getScoreColor(item.fitness_score)}`}
                      >
                        {Math.round(item.fitness_score)}
                      </div>

                      {/* Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900 truncate">
                            {item.name}
                          </h4>
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(item.category)}`}
                          >
                            {item.category}
                          </span>
                        </div>

                        <p className="text-sm text-gray-500 mt-1">
                          {item.reason}
                        </p>

                        <div className="flex items-center gap-4 mt-2 text-sm">
                          <span className="text-gray-600">
                            <span className="font-medium">{item.quantity}×</span>{" "}
                            ${item.unit_price.toFixed(2)}
                          </span>
                          <span className="text-gray-400">•</span>
                          <span className="text-green-600 font-medium">
                            {Math.round(item.total_protein)}g protein
                          </span>
                          <span className="text-gray-400">•</span>
                          <span className="text-gray-600">
                            {item.total_calories} cal
                          </span>
                        </div>
                      </div>

                      {/* Price */}
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          ${item.total_price.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Empty State */}
        {!result && !loading && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Set your goals and click optimize</p>
            <p className="text-sm mt-1">
              We&apos;ll find the best products for your budget and macros
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
