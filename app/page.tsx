"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import LottoCard from "@/components/LottoCard";
import StatsPanel from "@/components/StatsPanel";
import PredictionPanel from "@/components/PredictionPanel";
import HistoryPanel from "@/components/HistoryPanel";
import { getApiUrl } from "@/utils/api";

interface LatestResult {
  lottery_type: string;
  draw_date: string;
  draw_number: string;
  primary: string;
  secondary: Record<string, any>;
  source_url?: string;
  fetched_at?: string;
}

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("results");
  const [activeType, setActiveType] = useState<"glo" | "lao">("glo");
  
  // Latest result state
  const [latestData, setLatestData] = useState<LatestResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);

  // Next draw date countdown state
  const [nextDrawDate, setNextDrawDate] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<TimeLeft | null>(null);

  // Fetch latest draw results and predictions (for next_draw_date)
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      setNextDrawDate(null);
      setTimeLeft(null);
      try {
        // 1. Fetch Latest Results
        const res = await fetch(getApiUrl(`/api/results/latest?type=${activeType}`));
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        const json = await res.json();
        setLatestData(json);

        // 2. Fetch predictions in background to get next draw date
        const predRes = await fetch(getApiUrl(`/api/predictions?type=${activeType}`));
        if (predRes.ok) {
          const predJson = await predRes.json();
          if (predJson.next_draw_date) {
            setNextDrawDate(predJson.next_draw_date);
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load latest results");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [activeType]);

  // Countdown timer logic
  useEffect(() => {
    if (!nextDrawDate) return;
    
    // GLO draws finish around 16:00. LAO draws finish around 20:30.
    const drawTime = activeType === "glo" ? "16:00:00" : "20:30:00";
    const targetDate = new Date(`${nextDrawDate}T${drawTime}+07:00`);
    
    const updateTimer = () => {
      const now = new Date();
      const diff = targetDate.getTime() - now.getTime();
      
      if (diff <= 0) {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
      } else {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((diff / 1000 / 60) % 60);
        const seconds = Math.floor((diff / 1000) % 60);
        setTimeLeft({ days, hours, minutes, seconds });
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [nextDrawDate, activeType]);

  // Handle smooth tab transitions
  const handleTabChange = (tabId: string) => {
    setIsTransitioning(true);
    setTimeout(() => {
      setActiveTab(tabId);
      setIsTransitioning(false);
    }, 150);
  };

  const formatNextDrawDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("th-TH", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-100 text-zinc-900 font-sans flex justify-center items-stretch antialiased">
      {/* Mobile Frame Container */}
      <div className="w-full max-w-md bg-zinc-50 flex flex-col shadow-xl min-h-screen relative pb-20 border-x border-zinc-200">
        
        {/* Header App Bar */}
        <Navbar
          activeType={activeType}
          setActiveType={setActiveType}
        />

        {/* Content Container */}
        <main className="flex-1 px-4 py-6 overflow-y-auto space-y-5">
          {/* Transition wrapper */}
          <div className={`transition-all duration-200 ${isTransitioning ? "opacity-0 translate-y-2 scale-98" : "opacity-100 translate-y-0 scale-100"}`}>
            
            {activeTab === "results" && (
              <div className="space-y-4">
                
                {/* Clean, Non-intrusive Countdown Timer above the LottoCard */}
                {nextDrawDate && timeLeft && (
                  <div className="rounded-xl border border-zinc-200 bg-white px-4 py-3 shadow-sm flex items-center justify-between text-xs">
                    <div className="font-semibold text-zinc-700">
                      งวดถัดไป: {formatNextDrawDate(nextDrawDate)}
                    </div>
                    <div className="flex items-center gap-1 text-zinc-950 font-mono font-bold">
                      <span className="bg-zinc-100 px-1.5 py-0.5 rounded text-zinc-900">
                        {String(timeLeft.days).padStart(2, "0")}
                      </span>
                      <span className="text-zinc-300">:</span>
                      <span className="bg-zinc-100 px-1.5 py-0.5 rounded text-zinc-900">
                        {String(timeLeft.hours).padStart(2, "0")}
                      </span>
                      <span className="text-zinc-300">:</span>
                      <span className="bg-zinc-100 px-1.5 py-0.5 rounded text-zinc-900">
                        {String(timeLeft.minutes).padStart(2, "0")}
                      </span>
                      <span className="text-zinc-300">:</span>
                      <span className="bg-zinc-100 px-1.5 py-0.5 rounded text-zinc-600">
                        {String(timeLeft.seconds).padStart(2, "0")}
                      </span>
                    </div>
                  </div>
                )}

                <LottoCard
                  type={activeType}
                  data={latestData}
                  loading={loading}
                  error={error}
                />
              </div>
            )}

            {activeTab === "stats" && (
              <StatsPanel type={activeType} />
            )}

            {activeTab === "predictions" && (
              <PredictionPanel type={activeType} />
            )}

            {activeTab === "history" && (
              <HistoryPanel type={activeType} />
            )} 
          </div>

          {/* Disclaimer Footnote */}
          <div className="text-center text-[10px] text-zinc-400 pt-6 pb-2 border-t border-zinc-200 mt-6 font-medium">
            การคำนวณนี้เป็นเพียงการประมวลผลทางสถิติเท่านั้น ไม่การันตีผลรางวัลได้ 100% นะจ๊ะะ
          </div>
        </main>

        {/* Bottom Navigation Bar with Minimalist Outline SVGs */}
        <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-t border-zinc-200 py-2.5 px-4 flex justify-around items-center max-w-md mx-auto shadow-lg">
          {/* Item 1: Results */}
          <button
            onClick={() => handleTabChange("results")}
            className="flex flex-col items-center gap-1 focus:outline-none flex-1 py-1 relative"
          >
            <svg
              className={`w-5 h-5 transition-colors ${activeTab === "results" ? "text-zinc-950" : "text-zinc-400"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-12h9c.621 0 1.125.504 1.125 1.125V18c0 .621-.504 1.125-1.125 1.125h-9A1.125 1.125 0 016.375 18V7.125C6.375 6.504 6.879 6 7.5 6zM4.5 9h1.875M4.5 12h1.875M4.5 15h1.875" />
            </svg>
            <span className={`text-[10px] font-bold tracking-tight ${activeTab === "results" ? "text-zinc-950" : "text-zinc-400"}`}>
              รางวัลล่าสุด
            </span>
            {activeTab === "results" && <span className="absolute bottom-0 w-6 h-0.5 bg-zinc-950 rounded-full" />}
          </button>

          {/* Item 2: Stats */}
          <button
            onClick={() => handleTabChange("stats")}
            className="flex flex-col items-center gap-1 focus:outline-none flex-1 py-1 relative"
          >
            <svg
              className={`w-5 h-5 transition-colors ${activeTab === "stats" ? "text-zinc-950" : "text-zinc-400"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v5.25c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 013 18.375v-5.25zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125v-9.75zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v14.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            <span className={`text-[10px] font-bold tracking-tight ${activeTab === "stats" ? "text-zinc-950" : "text-zinc-400"}`}>
              สถิติหวย
            </span>
            {activeTab === "stats" && <span className="absolute bottom-0 w-6 h-0.5 bg-zinc-950 rounded-full" />}
          </button>

          {/* Item 3: Predictions */}
          <button
            onClick={() => handleTabChange("predictions")}
            className="flex flex-col items-center gap-1 focus:outline-none flex-1 py-1 relative"
          >
            <svg
              className={`w-5 h-5 transition-colors ${activeTab === "predictions" ? "text-zinc-950" : "text-zinc-400"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21m0 0l-.813-5.096m.813 5.096a5.126 5.126 0 115.25-5.25m-5.25 5.25a5.126 5.126 0 01-5.25-5.25M9 10.5V3m0 7.5a3 3 0 100 6M9 10.5a3 3 0 010 6m9-9h3.75m-3.75 3h3.75m-3.75 3h3.75m-11.25-3h3.75" />
            </svg>
            <span className={`text-[10px] font-bold tracking-tight ${activeTab === "predictions" ? "text-zinc-950" : "text-zinc-400"}`}>
              ทำนาย AI
            </span>
            {activeTab === "predictions" && <span className="absolute bottom-0 w-6 h-0.5 bg-zinc-950 rounded-full" />}
          </button>

          {/* Item 4: History */}
          <button
            onClick={() => handleTabChange("history")}
            className="flex flex-col items-center gap-1 focus:outline-none flex-1 py-1 relative"
          >
            <svg
              className={`w-5 h-5 transition-colors ${activeTab === "history" ? "text-zinc-950" : "text-zinc-400"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className={`text-[10px] font-bold tracking-tight ${activeTab === "history" ? "text-zinc-950" : "text-zinc-400"}`}>
              ประวัติย้อนหลัง
            </span>
            {activeTab === "history" && <span className="absolute bottom-0 w-6 h-0.5 bg-zinc-950 rounded-full" />}
          </button>
        </nav>
      </div>
    </div>
  );
}

