"use client";

import React from "react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeType: "glo" | "lao";
  setActiveType: (type: "glo" | "lao") => void;
}

export default function Navbar({
  activeType,
  setActiveType,
}: Omit<NavbarProps, "activeTab" | "setActiveTab">) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-200 bg-white/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-950 text-white font-bold text-lg tracking-tight">
            K
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-zinc-950">HUAY KVJ</h1>
            <p className="text-[10px] text-zinc-500 font-medium -mt-1">By Pakawat</p>
          </div>
        </div>

        {/* Lotto Type Selector */} 
        <div className="flex items-center gap-1 rounded-full bg-zinc-100 p-1 border border-zinc-200">
          <button
            onClick={() => setActiveType("glo")}
            className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all duration-200 ${
              activeType === "glo"
                ? "bg-white text-zinc-950 shadow-sm"
                : "text-zinc-500 hover:text-zinc-950"
            }`}
          >
            รัฐบาลไทย
          </button>
          <button
            onClick={() => setActiveType("lao")}
            className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all duration-200 ${
              activeType === "lao"
                ? "bg-white text-zinc-950 shadow-sm"
                : "text-zinc-500 hover:text-zinc-950"
            }`}
          >
            หวยลาว
          </button>
        </div>
      </div>
    </header>
  );
}
