"use client";

import React, { useState, useEffect } from "react";
import { getApiUrl } from "@/utils/api";

interface StatsPanelProps {
  type: "glo" | "lao";
}

interface StatNumber {
  number: string;
  count: number;
}

interface Ratio {
  even_count?: number;
  odd_count?: number;
  even_percentage: number;
  odd_percentage: number;
  high_count?: number;
  low_count?: number;
  high_percentage: number;
  low_percentage: number;
}

interface StatsData {
  lottery_type: string;
  position: string;
  stat_type: string;
  limit_draws: number;
  total_draws_analyzed: number;
  total_numbers_sampled: number;
  hot_numbers: StatNumber[];
  cold_numbers: StatNumber[];
  even_odd_ratio: {
    even_count: number;
    odd_count: number;
    even_percentage: number;
    odd_percentage: number;
  };
  high_low_ratio: {
    high_count: number;
    low_count: number;
    high_percentage: number;
    low_percentage: number;
  };
  all_frequencies: Record<string, number>;
}

export default function StatsPanel({ type }: StatsPanelProps) {
  // Config states
  const [limitDraws, setLimitDraws] = useState<number>(100);
  const [position, setPosition] = useState<string>(type === "glo" ? "last_2" : "digits_2");
  const [statType, setStatType] = useState<string>("numbers");

  // API states
  const [data, setData] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Reset position filter when lottery type changes
  useEffect(() => {
    setPosition(type === "glo" ? "last_2" : "digits_2");
  }, [type]);

  // Fetch stats when filters or type change
  useEffect(() => {
    async function fetchStats() {
      // ตรวจสอบความสอดคล้องของ position กับ type เพื่อแก้บั๊ก timing lag (400 Bad Request)
      const isGloPos = ["first_prize", "last_2", "last_3", "first_3"].includes(position);
      const isLaoPos = ["digits_4", "digits_3", "digits_2"].includes(position);
      
      let fetchPosition = position;
      if (type === "glo" && !isGloPos) {
        fetchPosition = "last_2";
      } else if (type === "lao" && !isLaoPos) {
        fetchPosition = "digits_2";
      }

      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          getApiUrl(`/api/stats/hot-cold?type=${type}&limit_draws=${limitDraws}&position=${fetchPosition}&stat_type=${statType}`)
        );
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || "Failed to load statistics");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, [type, limitDraws, position, statType]);

  const handlePositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPosition(e.target.value);
  };

  const handleLimitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLimitDraws(Number(e.target.value));
  };

  const handleStatTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatType(e.target.value);
  };

  const positions = type === "glo"
    ? [
        { id: "last_2", label: "เลขท้าย 2 ตัว" },
        { id: "last_3", label: "เลขท้าย 3 ตัว" },
        { id: "first_3", label: "เลขหน้า 3 ตัว" },
        { id: "first_prize", label: "รางวัลที่ 1" },
      ]
    : [
        { id: "digits_2", label: "เลข 2 ตัว" },
        { id: "digits_3", label: "เลข 3 ตัว" },
        { id: "digits_4", label: "เลข 4 ตัว" },
      ];

  return (
    <div className="w-full space-y-6">
      {/* Filter Control Bar */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-zinc-950 mb-3">ตัวเลือกการวิเคราะห์สถิติ</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Position Selector */}
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">ตำแหน่งรางวัล</label>
            <select
              value={position}
              onChange={handlePositionChange}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            >
              {positions.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Stat Type Selector */}
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">ประเภทการนับความถี่</label>
            <select
              value={statType}
              onChange={handleStatTypeChange}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            >
              <option value="numbers">เลขชุด (เช่น 00-99)</option>
              <option value="digits">เลขเดี่ยวแยกตัว (0-9)</option>
            </select>
          </div>

          {/* Limit Draws Selector */}
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">จำนวนงวดคำนวณย้อนหลัง</label>
            <select
              value={limitDraws}
              onChange={handleLimitChange}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            >
              <option value={30}>30 งวดล่าสุด</option>
              <option value={50}>50 งวดล่าสุด</option>
              <option value={100}>100 งวดล่าสุด</option>
              <option value={200}>200 งวดล่าสุด</option>
              <option value={500}>500 งวดล่าสุด</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="w-full rounded-2xl border border-zinc-200 bg-white p-12 text-center animate-pulse">
          <div className="mx-auto h-4 w-48 rounded bg-zinc-200 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="h-40 rounded bg-zinc-100"></div>
            <div className="h-40 rounded bg-zinc-100"></div>
          </div>
        </div>
      ) : error ? (
        <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-6 text-center text-red-700">
          <p className="font-semibold">เกิดข้อผิดพลาดในการโหลดข้อมูลสถิติ</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Quick Ratios (Even/Odd, High/Low) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Even / Odd Ratio */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-sm font-bold text-zinc-900">อัตราส่วน คู่ : คี่</h4>
                <span className="text-xs text-zinc-500 font-medium">
                  อิงจากหลักหน่วยของรางวัล
                </span>
              </div>
              
              <div className="space-y-3">
                {/* Horizontal Progress Bar */}
                <div className="flex h-6 w-full overflow-hidden rounded-full bg-zinc-100 border border-zinc-200 text-xs font-semibold">
                  <div
                    style={{ width: `${data.even_odd_ratio.even_percentage}%` }}
                    className="flex items-center justify-center bg-zinc-900 text-white transition-all duration-500"
                  >
                    {data.even_odd_ratio.even_percentage >= 15 && `คู่ ${data.even_odd_ratio.even_percentage}%`}
                  </div>
                  <div
                    style={{ width: `${data.even_odd_ratio.odd_percentage}%` }}
                    className="flex items-center justify-center bg-zinc-300 text-zinc-800 transition-all duration-500"
                  >
                    {data.even_odd_ratio.odd_percentage >= 15 && `คี่ ${data.even_odd_ratio.odd_percentage}%`}
                  </div>
                </div>

                <div className="flex justify-between text-xs text-zinc-500 font-medium px-1">
                  <span>เลขคู่: {data.even_odd_ratio.even_count} ครั้ง</span>
                  <span>เลขคี่: {data.even_odd_ratio.odd_count} ครั้ง</span>
                </div>
              </div>
            </div>

            {/* High / Low Ratio */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-sm font-bold text-zinc-900">อัตราส่วน สูง : ต่ำ</h4>
                <span className="text-xs text-zinc-500 font-medium">
                  {statType === "digits" ? "เทียบกับค่ากลาง 0-4 / 5-9" : "เทียบครึ่งช่วงตัวเลข"}
                </span>
              </div>
              
              <div className="space-y-3">
                {/* Horizontal Progress Bar */}
                <div className="flex h-6 w-full overflow-hidden rounded-full bg-zinc-100 border border-zinc-200 text-xs font-semibold">
                  <div
                    style={{ width: `${data.high_low_ratio.high_percentage}%` }}
                    className="flex items-center justify-center bg-zinc-800 text-white transition-all duration-500"
                  >
                    {data.high_low_ratio.high_percentage >= 15 && `สูง ${data.high_low_ratio.high_percentage}%`}
                  </div>
                  <div
                    style={{ width: `${data.high_low_ratio.low_percentage}%` }}
                    className="flex items-center justify-center bg-zinc-200 text-zinc-700 transition-all duration-500"
                  >
                    {data.high_low_ratio.low_percentage >= 15 && `ต่ำ ${data.high_low_ratio.low_percentage}%`}
                  </div>
                </div>

                <div className="flex justify-between text-xs text-zinc-500 font-medium px-1">
                  <span>เลขสูง: {data.high_low_ratio.high_count} ครั้ง</span>
                  <span>เลขต่ำ: {data.high_low_ratio.low_count} ครั้ง</span>
                </div>
              </div>
            </div>
          </div>

          {/* Hot / Cold Table */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Hot Numbers (ออกบ่อยสุด) */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm">
              <h4 className="text-sm font-bold text-zinc-950 mb-3 flex items-center gap-2">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-zinc-900"></span>
                เลขร้อนแรง (Hot Numbers) - ออกบ่อยสุด
              </h4>
              <p className="text-xs text-zinc-500 mb-4">
                ตัวเลข 10 ลำดับที่มีจำนวนการออกรางวัลบ่อยที่สุดในงวดที่นำมาคำนวณ
              </p>
              <div className="divide-y divide-zinc-100">
                {data.hot_numbers.map((item, idx) => (
                  <div key={item.number} className="flex items-center justify-between py-2.5 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-semibold text-zinc-400 w-5">#{idx + 1}</span>
                      <span className={`font-bold font-mono text-base px-2.5 py-0.5 rounded-md border ${
                        idx === 0 ? "bg-red-100 text-red-900 border-red-200" :
                        idx === 1 ? "bg-orange-100 text-orange-900 border-orange-200" :
                        idx === 2 ? "bg-amber-100 text-amber-900 border-amber-200" :
                        idx === 3 ? "bg-yellow-100 text-yellow-900 border-yellow-200" :
                        idx === 4 ? "bg-lime-100 text-lime-900 border-lime-200" :
                        "bg-zinc-100/70 text-zinc-800 border-zinc-200"
                      }`}>
                        {item.number}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-900 font-bold">{item.count}</span>
                      <span className="text-xs text-zinc-500 font-medium">ครั้ง</span>
                    </div>
                  </div>
                ))}
                {data.hot_numbers.length === 0 && (
                  <div className="text-center py-4 text-xs text-zinc-500">ไม่มีข้อมูลเลขออกบ่อย</div>
                )}
              </div>
            </div>

            {/* Cold Numbers (ออกน้อยสุด) */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-sm">
              <h4 className="text-sm font-bold text-zinc-950 mb-3 flex items-center gap-2">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-zinc-300"></span>
                เลขเยือกเย็น (Cold Numbers) - ออกน้อยสุด / ดับ
              </h4>
              <p className="text-xs text-zinc-500 mb-4">
                ตัวเลขที่มีอัตราการออกรางวัลน้อยที่สุด หรือไม่ออกเลยในช่วงที่เลือก
              </p>
              <div className="divide-y divide-zinc-100">
                {data.cold_numbers.map((item, idx) => (
                  <div key={item.number} className="flex items-center justify-between py-2.5 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-semibold text-zinc-400 w-5">#{idx + 1}</span>
                      <span className={`font-bold font-mono text-base px-2.5 py-0.5 rounded-md border ${
                        idx === 0 ? "bg-blue-100 text-blue-900 border-blue-200" :
                        idx === 1 ? "bg-sky-100 text-sky-900 border-sky-200" :
                        idx === 2 ? "bg-cyan-100 text-cyan-900 border-cyan-200" :
                        idx === 3 ? "bg-indigo-100 text-indigo-900 border-indigo-200" :
                        idx === 4 ? "bg-teal-100 text-teal-900 border-teal-200" :
                        "bg-zinc-50/70 text-zinc-600 border-zinc-150"
                      }`}>
                        {item.number}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500 font-semibold">{item.count}</span>
                      <span className="text-xs text-zinc-500 font-medium">ครั้ง</span>
                    </div>
                  </div>
                ))}
                {data.cold_numbers.length === 0 && (
                  <div className="text-center py-4 text-xs text-zinc-500">ไม่มีข้อมูลเลขออกน้อย</div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
