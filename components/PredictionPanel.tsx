"use client";

import React, { useState, useEffect } from "react";
import { getApiUrl } from "@/utils/api";

interface PredictionPanelProps {
  type: "glo" | "lao";
}

interface PredictionItem {
  number: string;
  probability: number;
  model: string;
}

interface PredictionData {
  lottery_type: string;
  latest_draw_date: string;
  next_draw_date: string;
  predictions: {
    three_up: PredictionItem[];
    three_todd: PredictionItem[];
    two_up: PredictionItem[];
    two_down: PredictionItem[];
    run_up: PredictionItem[];
    run_down: PredictionItem[];
  };
}

export default function PredictionPanel({ type }: PredictionPanelProps) {
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPredictions() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(getApiUrl(`/api/predictions?type=${type}`));
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || "Failed to load predictions from AI engine");
      } finally {
        setLoading(false);
      }
    }
    fetchPredictions();
  }, [type]);

  const toPercentage = (val: number) => {
    return (val * 100).toFixed(1) + "%";
  };

  // Helper component to render list of predictions
  const renderPredictionList = (
    title: string,
    subtitle: string,
    items: PredictionItem[],
    multiplier: number = 300,
    trackingClass: string = ""
  ) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm space-y-3">
        <div>
          <h4 className="text-xs font-bold text-zinc-900">{title}</h4>
          <p className="text-[10px] text-zinc-400 mt-0.5">{subtitle}</p>
        </div>
        <div className="space-y-2.5">
          {items.map((item, idx) => (
            <div key={item.number} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-zinc-300 w-4">#{idx + 1}</span>
                  <span className={`font-extrabold text-zinc-950 font-mono text-sm bg-zinc-50 border border-zinc-200 px-2.5 py-0.5 rounded ${trackingClass}`}>
                    {item.number}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-zinc-400 font-semibold">
                  <span>โอกาส:</span>
                  <span className="text-zinc-800 font-bold font-mono">{toPercentage(item.probability)}</span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-zinc-100 h-1 rounded-full overflow-hidden">
                <div
                  style={{ width: `${Math.min(item.probability * multiplier, 100)}%` }}
                  className="bg-zinc-950 h-full rounded-full transition-all duration-300"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="w-full space-y-4">
        {[...Array(3)].map((_, idx) => (
          <div key={idx} className="h-36 rounded-2xl bg-white border border-zinc-200 p-5 animate-pulse">
            <div className="h-3.5 w-32 rounded bg-zinc-200 mb-4"></div>
            <div className="space-y-2">
              <div className="h-5 rounded bg-zinc-150 w-full"></div>
              <div className="h-5 rounded bg-zinc-150 w-full"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-5 text-center text-red-700 text-sm">
        <p className="font-bold">ไม่สามารถดึงข้อมูลทำนายผล AI ได้</p>
        <p className="text-xs text-red-500 mt-1">{error}</p>
        <p className="text-xs text-zinc-400 mt-3">
          โปรดตรวจสอบว่าเปิดใช้งาน FastAPI server และเทรนโมเดล LSTM ใน backend/ml/models เรียบร้อยแล้ว
        </p>
      </div>
    );
  }

  if (!data) return null;

  const preds = data.predictions;

  return (
    <div className="w-full space-y-6">
      {/* Title Header */}
      <div className="rounded-xl border border-zinc-200 bg-zinc-950 text-white px-4 py-3 shadow-sm flex items-center justify-between text-xs">
        <span className="font-semibold">ระบบประเมินความน่าจะเป็น (Ensemble AI)</span>
        <span className="text-zinc-400 font-mono text-[9px]">LSTM 60% + Freq 40%</span>
      </div>

      {/* --- Section 1: หมวดหมู่ 3 ตัว --- */}
      <div className="space-y-3">
        <div className="border-l-2 border-zinc-900 pl-2">
          <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wider">ทำนายผลรางวัล 3 ตัว</h3>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {renderPredictionList(
            "เลขท้าย 3 ตัวบน (ตรง)",
            "ประเมินตามโอกาสการออกรางวัล 3 ตัวบนตรงแบบระบุหลัก",
            preds.three_up,
            300,
            "tracking-wider"
          )}
          {renderPredictionList(
            "เลขท้าย 3 ตัวบน (โต๊ด)",
            "กลุ่มเลข 3 ตัวสลับตำแหน่งกัน (โอกาสถูกรางวัลสูงขึ้น)",
            preds.three_todd,
            120, // Todd has lower individual probabilities because they represent permutations
            "tracking-widest"
          )}
        </div>
      </div>

      {/* --- Section 2: หมวดหมู่ 2 ตัว --- */}
      <div className="space-y-3">
        <div className="border-l-2 border-zinc-900 pl-2">
          <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wider">ทำนายผลรางวัล 2 ตัว</h3>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {renderPredictionList(
            "เลขท้าย 2 ตัวบน",
            "ความน่าจะเป็นสะสมของ 2 หลักสุดท้ายของรางวัลที่ 1",
            preds.two_up,
            300
          )}
          {renderPredictionList(
            "เลขท้าย 2 ตัวล่าง",
            "คำนวณจากความถี่และโครงข่ายประสาทเทียมสำหรับ 2 ตัวล่างตรง",
            preds.two_down,
            300
          )}
        </div>
      </div>

      {/* --- Section 3: หมวดหมู่เลขวิ่งเดี่ยว --- */}
      <div className="space-y-3">
        <div className="border-l-2 border-zinc-900 pl-2">
          <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wider">ทำนายเลขเด่นตัวเดียว (เลขวิ่ง)</h3>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {renderPredictionList(
            "วิ่งบน (เด่น 3 ตัวบน)",
            "ตัวเลขเดี่ยว 0-9 ที่มีโอกาสสอดแทรกอยู่ในรางวัล 3 ตัวบนมากที่สุด",
            preds.run_up,
            120
          )}
          {renderPredictionList(
            "วิ่งล่าง (เด่น 2 ตัวล่าง)",
            "ตัวเลขเดี่ยว 0-9 ที่มีโอกาสสอดแทรกอยู่ในรางวัล 2 ตัวล่างมากที่สุด",
            preds.run_down,
            150
          )}
        </div>
      </div>
    </div>
  );
}
