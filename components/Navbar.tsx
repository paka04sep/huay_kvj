"use client";

import React from "react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeType: "glo" | "lao";
  setActiveType: (type: "glo" | "lao") => void;
}

export default function Navbar({
  activeTab,
  setActiveTab,
  activeType,
  setActiveType,
}: NavbarProps) {
  const tabs = [
    { id: "results", label: "ผลรางวัลล่าสุด" },
    { id: "stats", label: "วิเคราะห์สถิติ (Hot/Cold)" },
    { id: "predictions", label: "ระบบทำนายผล AI" },
    { id: "history", label: "ประวัติย้อนหลัง" },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-950 text-white font-bold text-lg tracking-tight">
            K
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-zinc-950">HUAY KVJ</h1>
            <p className="text-[10px] text-zinc-500 font-medium -mt-1">ML LOTTO PREDICTOR</p>
          </div>
        </div>

        {/* Lotto Type Selector */}
        <div className="flex items-center gap-1 rounded-full bg-zinc-100 p-1 border border-zinc-200">
          <button
            onClick={() => setActiveType("glo")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all duration-200 ${
              activeType === "glo"
                ? "bg-white text-zinc-950 shadow-sm"
                : "text-zinc-600 hover:text-zinc-950"
            }`}
          >
            รัฐบาลไทย (GLO)
          </button>
          <button
            onClick={() => setActiveType("lao")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all duration-200 ${
              activeType === "lao"
                ? "bg-white text-zinc-950 shadow-sm"
                : "text-zinc-600 hover:text-zinc-950"
            }`}
          >
            หวยลาว (LAO)
          </button>
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="border-t border-zinc-100 bg-white">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 -mb-px overflow-x-auto scrollbar-none" aria-label="Tabs">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-all ${
                    isActive
                      ? "border-zinc-950 text-zinc-950 font-semibold"
                      : "border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
