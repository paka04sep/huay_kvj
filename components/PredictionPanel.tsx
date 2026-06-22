"use client";

import React, { useState, useEffect } from "react";

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
    last_2: PredictionItem[];
    last_3: PredictionItem[];
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
        const res = await fetch(`http://localhost:8000/api/predictions?type=${type}`);
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

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("th-TH", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch (e) {
      return dateStr;
    }
  };

  const toPercentage = (val: number) => {
    return (val * 100).toFixed(2) + "%";
  };

  if (loading) {
    return (
      <div className="w-full rounded-2xl border border-zinc-200 bg-white p-12 text-center animate-pulse">
        <div className="mx-auto h-4 w-48 rounded bg-zinc-200 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="h-64 rounded bg-zinc-100"></div>
          <div className="h-64 rounded bg-zinc-100"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-6 text-center text-red-700">
        <p className="font-semibold">ไม่สามารถเรียกข้อมูลโมเดลทำนายผล AI ได้</p>
        <p className="text-xs text-red-500 mt-1">{error}</p>
        <p className="text-xs text-zinc-500 mt-3">
          หมายเหตุ: โปรดตรวจสอบว่ารันโมเดล LSTM ใน Backend backend/ml/models เรียบร้อยแล้ว
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full rounded-2xl border border-zinc-200 bg-white p-8 text-center text-zinc-500">
        ไม่มีข้อมูลทำนายผลหวยล่าสุด
      </div>
    );
  }

  const hasPredictions =
    (data.predictions.last_2 && data.predictions.last_2.length > 0) ||
    (data.predictions.last_3 && data.predictions.last_3.length > 0);

  return (
    <div className="w-full space-y-6">
      {/* Prediction Schedule Card */}
      <div className="rounded-2xl border border-zinc-200 bg-zinc-950 text-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="inline-flex items-center rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs font-semibold text-zinc-300">
              ระบบวิเคราะห์ด้วยปัญญาประดิษฐ์ (Ensemble Model)
            </span>
            <h3 className="text-lg font-bold text-white mt-1.5">
              เลขแนะนำสำหรับงวดถัดไป: {formatDate(data.next_draw_date)}
            </h3>
          </div>
          <div className="text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-lg p-2.5">
            <div>อ้างอิงข้อมูลงวดล่าสุด: {formatDate(data.latest_draw_date)}</div>
            <div className="mt-0.5">โมเดลประมวลผล: LSTM 60% + Frequency 40%</div>
          </div>
        </div>
      </div>

      {!hasPredictions ? (
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center text-zinc-500">
          ไม่พบข้อมูลเลขทำนายในงวดนี้
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 2-Digit Predictions */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-zinc-950 mb-1">
                เลขแนะนำ 2 ตัวท้าย (Top 5 Recommendations)
              </h4>
              <p className="text-xs text-zinc-500 mb-4">
                คำนวณผ่านโครงข่ายประสาทเทียม LSTM ผสานกับความน่าจะเป็นตามสถิติความถี่
              </p>

              <div className="space-y-3">
                {data.predictions.last_2?.map((item, idx) => (
                  <div key={item.number} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-zinc-400 w-5">#{idx + 1}</span>
                        <span className="font-extrabold text-zinc-950 font-mono text-lg bg-zinc-100 px-3 py-0.5 rounded-lg">
                          {item.number}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-semibold">
                        <span>โอกาส:</span>
                        <span className="text-zinc-900 font-bold">{toPercentage(item.probability)}</span>
                      </div>
                    </div>
                    {/* Visual bar */}
                    <div className="w-full bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        style={{ width: `${Math.min(item.probability * 300, 100)}%` }}
                        className="bg-zinc-900 h-full rounded-full transition-all duration-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-6 border-t border-zinc-100 pt-4 text-[10px] text-zinc-400">
              * ข้อมูลความน่าจะเป็นเป็นการวิเคราะห์ทางคณิตศาสตร์จากข้อมูลดิบในอดีตเท่านั้น
            </div>
          </div>

          {/* 3-Digit Predictions */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-zinc-950 mb-1">
                เลขแนะนำ 3 ตัวท้าย (Top 5 Recommendations)
              </h4>
              <p className="text-xs text-zinc-500 mb-4">
                วิเคราะห์แนวโน้มการออกเลขรางวัล 3 ตัวตรง/โต๊ด โดยใช้ Deep Learning
              </p>

              <div className="space-y-3">
                {data.predictions.last_3?.map((item, idx) => (
                  <div key={item.number} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-zinc-400 w-5">#{idx + 1}</span>
                        <span className="font-extrabold text-zinc-950 font-mono text-lg bg-zinc-100 px-3 py-0.5 rounded-lg tracking-wider">
                          {item.number}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-semibold">
                        <span>โอกาส:</span>
                        <span className="text-zinc-900 font-bold">{toPercentage(item.probability)}</span>
                      </div>
                    </div>
                    {/* Visual bar */}
                    <div className="w-full bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        style={{ width: `${Math.min(item.probability * 500, 100)}%` }}
                        className="bg-zinc-700 h-full rounded-full transition-all duration-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 border-t border-zinc-100 pt-4 text-[10px] text-zinc-400">
              * ข้อมูลชุดนี้อัปเดตผ่านระบบ Ensemble Model โดยอัตโนมัติเมื่อตรวจพบรางวัลล่าสุด
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
