"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import LottoCard from "@/components/LottoCard";
import StatsPanel from "@/components/StatsPanel";
import PredictionPanel from "@/components/PredictionPanel";
import HistoryPanel from "@/components/HistoryPanel";

interface LatestResult {
  lottery_type: string;
  draw_date: string;
  draw_number: string;
  primary: string;
  secondary: Record<string, any>;
  source_url?: string;
  fetched_at?: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("results");
  const [activeType, setActiveType] = useState<"glo" | "lao">("glo");
  
  // Latest result state (shared / cached)
  const [latestData, setLatestData] = useState<LatestResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch latest draw results when activeType changes
  useEffect(() => {
    async function fetchLatest() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`http://localhost:8000/api/results/latest?type=${activeType}`);
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        const json = await res.json();
        setLatestData(json);
      } catch (err: any) {
        setError(err.message || "Failed to load latest results");
      } finally {
        setLoading(false);
      }
    }
    fetchLatest();
  }, [activeType]);

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 text-zinc-900 font-sans">
      {/* Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeType={activeType}
        setActiveType={setActiveType}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {/* Title and Intro */}
        <div className="text-center sm:text-left">
          <h2 className="text-3xl font-extrabold tracking-tight text-zinc-950">
            ระบบวิเคราะห์และคาดการณ์สถิติหวย
          </h2>
          <p className="mt-2 text-sm text-zinc-500 max-w-2xl">
            แพลตฟอร์มเพื่อการศึกษา รวบรวมข้อมูลสถิติผลสลากกินแบ่งรัฐบาลไทย (GLO) และหวยพัฒนาลาว (LAO) 
            พร้อมประมวลผลวิเคราะห์ด้วยปัญญาประดิษฐ์และโครงข่ายประสาทเทียม
          </p>
        </div>

        {/* Tab rendering logic */}
        <div className="space-y-6">
          {activeTab === "results" && (
            <div className="space-y-6">
              <LottoCard
                type={activeType}
                data={latestData}
                loading={loading}
                error={error}
              />
              
              {/* Additional helpful guidelines card */}
              <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
                <h3 className="text-sm font-bold text-zinc-900 mb-2">คู่มือการใช้งานระบบทำนาย</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  ผู้ใช้งานสามารถสลับแถบด้านบนเพื่อดู <b>วิเคราะห์สถิติ</b> เพื่อตรวจดูเลขฮอต/เลขดับแบบรายงวด 
                  หรือกด <b>ระบบทำนายผล AI</b> เพื่อให้ระบบ Ensemble LSTM & Statistical Predictor 
                  คำนวณโอกาสความน่าจะเป็นสำหรับการออกรางวัลในงวดหน้าโดยอ้างอิงจากข้อมูลสถิติที่เก็บย้อนหลังในฐานข้อมูล
                </p>
              </div>
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
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 bg-white py-6 mt-12 text-center text-xs text-zinc-400">
        <p>© 2026 HUAY KVJ Project. พัฒนาขึ้นเพื่อการวิเคราะห์ทางวิทยาศาสตร์และสถิติข้อมูลสลากกินแบ่งเท่านั้น</p>
      </footer>
    </div>
  );
}

