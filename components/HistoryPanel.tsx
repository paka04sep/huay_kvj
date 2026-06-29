"use client";

import React, { useState, useEffect } from "react";
import { getApiUrl } from "@/utils/api";

interface HistoryPanelProps {
  type: "glo" | "lao";
}

interface HistoryResult {
  draw_date: string;
  draw_number: string;
  primary: string;
  secondary: Record<string, any>;
  source_url?: string;
  fetched_at?: string;
}

interface HistoryResponse {
  lottery_type: string;
  page: number;
  limit: number;
  total_count: number;
  total_pages: number;
  results: HistoryResult[];
}

interface PredictionItem {
  number: string;
  probability: number;
}

interface PredictionRecord {
  draw_date: string;
  draw_number: string | null;
  predictions: {
    three_up: PredictionItem[];
    three_todd: PredictionItem[];
    two_up: PredictionItem[];
    two_down: PredictionItem[];
    run_up: PredictionItem[];
    run_down: PredictionItem[];
  };
  actual_result: {
    primary: string;
    secondary: Record<string, any>;
  } | null;
}

interface PredictionsHistoryResponse {
  lottery_type: string;
  page: number;
  limit: number;
  total_count: number;
  total_pages: number;
  results: PredictionRecord[];
}

interface PredictionHistoryCardProps {
  row: PredictionRecord;
  type: "glo" | "lao";
  formatDate: (dateStr: string) => string;
  checkHit: (
    category: "three_up" | "three_todd" | "two_up" | "two_down" | "run_up" | "run_down",
    predictedNumber: string,
    actual: PredictionRecord["actual_result"],
    lotteryType: "glo" | "lao"
  ) => boolean;
}

function PredictionHistoryCard({ row, type, formatDate, checkHit }: PredictionHistoryCardProps) {
  const isDrawn = !!row.actual_result;
  const primary = row.actual_result?.primary || "";
  const secondary = row.actual_result?.secondary || {};

  const shouldBeExpandedByDefault = (row: PredictionRecord) => {
    if (!row.actual_result) return true; // งวดรอยืนยันผลรางวัล
    
    try {
      const [year, month, day] = row.draw_date.split("-").map(Number);
      const drawDate = new Date(year, month - 1, day);
      
      const today = new Date();
      const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
      
      const diffTime = todayDate.getTime() - drawDate.getTime();
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 1) {
        return true; // งวดของเมื่อวานที่ออกแล้ว (or today)
      }
    } catch (e) {
      // Ignore
    }
    return false;
  };

  const [isExpanded, setIsExpanded] = useState(() => shouldBeExpandedByDefault(row));

  // Extract actual values for displaying in header
  let displayPrimary = "";
  let displaySecond = "";
  if (isDrawn) {
    if (type === "glo") {
      displayPrimary = primary;
      displaySecond = secondary.last_2 || "";
    } else {
      displayPrimary = primary;
      displaySecond = secondary.digits_2 || "";
    }
  }

  // Count hits
  let totalHits = 0;
  const categories = [
    { key: "three_up", label: "3 ตัวบน (ตรง)" },
    { key: "three_todd", label: "3 ตัวโต๊ด" },
    { key: "two_up", label: "2 ตัวบน" },
    { key: "two_down", label: "2 ตัวล่าง" },
    { key: "run_up", label: "วิ่งบน" },
    { key: "run_down", label: "วิ่งล่าง" },
  ] as const;

  if (isDrawn) {
    categories.forEach((cat) => {
      const preds = row.predictions[cat.key] || [];
      preds.forEach((pred) => {
        if (checkHit(cat.key, pred.number, row.actual_result, type)) {
          totalHits++;
        }
      });
    });
  }

  return (
    <div className={`bg-white border border-zinc-200 rounded-2xl p-5 shadow-sm hover:border-zinc-300 transition-all duration-255 ${isExpanded ? "space-y-4" : ""}`}>
      {/* Card Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className={`flex items-center justify-between cursor-pointer select-none gap-2 hover:opacity-80 transition-opacity ${isExpanded ? "border-b border-zinc-100 pb-3" : ""}`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between w-full gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-zinc-950"></span>
            <h4 className="font-bold text-zinc-900 text-sm">
              งวดประจำวันที่ {formatDate(row.draw_date)}
            </h4>
          </div>
          <div className="flex items-center gap-2">
            {isDrawn ? (
              totalHits > 0 ? (
                <span className="inline-flex items-center rounded-full bg-emerald-50 border border-emerald-250 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
                  ✨ AI เข้าเป้า {totalHits} จุด
                </span>
              ) : (
                <span className="inline-flex items-center rounded-full bg-zinc-100 border border-zinc-200 px-2.5 py-0.5 text-xs font-semibold text-zinc-500">
                  ไม่พบรางวัลที่ทำนายถูก
                </span>
              )
            ) : (
              <span className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-bold text-amber-700">
                ⏳ รอยืนยันผลรางวัล
              </span>
            )}
          </div>
        </div>
        <div className="text-zinc-400 pl-2">
          <svg
            className={`w-4 h-4 transform transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Winning Results info */}
          {isDrawn && (
            <div className="bg-zinc-50 border border-zinc-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-x-6 gap-y-2">
                <div>
                  <span className="text-[10px] uppercase font-bold text-zinc-400 block">
                    {type === "glo" ? "รางวัลที่ 1" : "เลขท้าย 4 ตัว"}
                  </span>
                  <span className="text-base font-extrabold text-zinc-950 font-mono tracking-wider">
                    {displayPrimary || "------"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-zinc-400 block">
                    เลขท้าย 2 ตัว
                  </span>
                  <span className="text-base font-extrabold text-zinc-950 font-mono">
                    {displaySecond || "--"}
                  </span>
                </div>
                {type !== "glo" && secondary.digits_3 && (
                  <div>
                    <span className="text-[10px] uppercase font-bold text-zinc-400 block">
                      เลข 3 ตัว
                    </span>
                    <span className="text-base font-extrabold text-zinc-950 font-mono">
                      {secondary.digits_3}
                    </span>
                  </div>
                )}
              </div>
              {totalHits > 0 && (
                <div className="text-right py-0.5 px-2 bg-emerald-50 border border-emerald-100 rounded-md">
                  <span className="text-[8px] font-extrabold text-emerald-600 tracking-wider block">
                    STATUS
                  </span>
                  <span className="text-xs font-bold text-emerald-800">
                    HIT SUCCESS
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Predictions Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {categories.map((cat) => {
              const preds = row.predictions[cat.key] || [];
              return (
                <div
                  key={cat.key}
                  className="border border-zinc-100 rounded-xl p-3.5 bg-zinc-50/20 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-zinc-800">
                      {cat.label}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {preds.map((pred) => {
                      const isHit =
                        isDrawn &&
                        checkHit(cat.key, pred.number, row.actual_result, type);
                      return (
                        <div
                          key={pred.number}
                          className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-lg border min-w-[52px] font-mono transition-all ${
                            isHit
                              ? "bg-emerald-50 border-emerald-400 text-emerald-800 shadow-sm"
                              : "bg-white border-zinc-200 text-zinc-700"
                          }`}
                        >
                          <span className="text-sm font-extrabold">
                            {pred.number}
                          </span>
                          <span
                            className={`text-[8px] font-bold ${
                              isHit ? "text-emerald-600" : "text-zinc-400"
                            }`}
                          >
                            {(pred.probability * 100).toFixed(1)}%
                          </span>
                        </div>
                      );
                    })}
                    {preds.length === 0 && (
                      <span className="text-[10px] text-zinc-400 italic">
                        ไม่มีผลทำนาย
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export default function HistoryPanel({ type }: HistoryPanelProps) {
  const [activeTab, setActiveTab] = useState<"results" | "predictions">("results");
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  
  // Cache to store history pages locally
  const [historyCache, setHistoryCache] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = `${type}-${activeTab}-${page}-${limit}`;
  const cachedPageData = historyCache[cacheKey];
  const resultsData = activeTab === "results" ? cachedPageData : null;
  const predictionsData = activeTab === "predictions" ? cachedPageData : null;

  // Reset page when switching types or tabs
  useEffect(() => {
    setPage(1);
  }, [type, activeTab]);

  useEffect(() => {
    async function fetchData() {
      const targetCacheKey = `${type}-${activeTab}-${page}-${limit}`;
      const hasCache = historyCache[targetCacheKey] !== undefined;

      if (!hasCache) {
        setLoading(true);
      }
      setError(null);
      try {
        if (activeTab === "results") {
          const res = await fetch(
            getApiUrl(`/api/results/history?type=${type}&page=${page}&limit=${limit}`)
          );
          if (!res.ok) {
            throw new Error(`API returned status ${res.status}`);
          }
          const json = await res.json();
          setHistoryCache(prev => ({ ...prev, [targetCacheKey]: json }));
        } else {
          const res = await fetch(
            getApiUrl(`/api/predictions/history?type=${type}&page=${page}&limit=${limit}`)
          );
          if (!res.ok) {
            throw new Error(`API returned status ${res.status}`);
          }
          const json = await res.json();
          setHistoryCache(prev => ({ ...prev, [targetCacheKey]: json }));
        }
      } catch (err: any) {
        if (!hasCache) {
          setError(err.message || `Failed to load ${activeTab === "results" ? "lottery history" : "AI prediction history"}`);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, page, limit, activeTab]);

  const formatDate = (dateStr: string) => {
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

  const checkHit = (
    category: "three_up" | "three_todd" | "two_up" | "two_down" | "run_up" | "run_down",
    predictedNumber: string,
    actual: PredictionRecord["actual_result"],
    lotteryType: "glo" | "lao"
  ): boolean => {
    if (!actual) return false;

    const isGlo = lotteryType === "glo";
    const primary = actual.primary || "";
    const secondary = actual.secondary || {};

    // Extract actual values
    let actualLast3 = "";
    if (isGlo) {
      actualLast3 = primary.slice(-3);
    } else {
      actualLast3 = secondary.digits_3 || (primary.length >= 3 ? primary.slice(-3) : "");
    }

    let actualLast2 = "";
    if (isGlo) {
      actualLast2 = secondary.last_2 || "";
    } else {
      actualLast2 = secondary.digits_2 || (primary.length >= 2 ? primary.slice(-2) : "");
    }

    const actualTwoUp = actualLast3 && actualLast3.length >= 2 ? actualLast3.slice(-2) : "";

    switch (category) {
      case "three_up":
        return predictedNumber === actualLast3;
      case "three_todd": {
        if (!actualLast3 || actualLast3.length !== 3) return false;
        const sortedActual = [...actualLast3].sort().join("");
        const sortedPred = [...predictedNumber].sort().join("");
        return sortedPred === sortedActual;
      }
      case "two_up":
        return predictedNumber === actualTwoUp;
      case "two_down":
        return predictedNumber === actualLast2;
      case "run_up":
        return actualLast3.includes(predictedNumber);
      case "run_down":
        return actualLast2.includes(predictedNumber);
      default:
        return false;
    }
  };

  const isGlo = type === "glo";
  const currentData = activeTab === "results" ? resultsData : predictionsData;

  return (
    <div className="w-full space-y-6">
      {/* Sub-tabs Selection */}
      <div className="flex border border-zinc-200 bg-white rounded-xl p-1 shadow-sm">
        <button
          onClick={() => setActiveTab("results")}
          className={`flex-1 py-2 text-xs font-bold text-center rounded-lg transition-all ${
            activeTab === "results"
              ? "bg-zinc-950 text-white"
              : "text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50"
          }`}
        >
          ประวัติผลรางวัลจริง
        </button>
        <button
          onClick={() => setActiveTab("predictions")}
          className={`flex-1 py-2 text-xs font-bold text-center rounded-lg transition-all flex items-center justify-center gap-1.5 ${
            activeTab === "predictions"
              ? "bg-zinc-950 text-white"
              : "text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50"
          }`}
        >
          <span>ประวัติการทำนาย</span>
          <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-extrabold ${activeTab === "predictions" ? "bg-zinc-800 text-zinc-200" : "bg-zinc-100 text-zinc-650"}`}>
            AI
          </span>
        </button>
      </div>

      {loading ? (
        <div className="w-full rounded-2xl border border-zinc-200 bg-white p-12 text-center animate-pulse">
          <div className="mx-auto h-4 w-48 rounded bg-zinc-200 mb-6"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 rounded bg-zinc-100 w-full"></div>
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-6 text-center text-red-700">
          <p className="font-semibold">เกิดข้อผิดพลาดในการโหลดข้อมูล</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
        </div>
      ) : activeTab === "results" && resultsData ? (
        /* =================== RESULTS TAB =================== */
        <div className="rounded-2xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="p-4 border-b border-zinc-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-zinc-950">
              ประวัติผลรางวัลย้อนหลัง ({isGlo ? "รัฐบาลไทย" : "หวยลาว"})
            </h3>
            <span className="text-xs text-zinc-500 font-medium">
              ทั้งหมด {resultsData.total_count} รายการ
            </span>
          </div>

          {/* Table Container */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-zinc-50 border-b border-zinc-200 text-zinc-500 text-xs font-semibold">
                  <th className="py-3 px-4">วันที่ออกรางวัล</th>
                  <th className="py-3 px-4 text-center">รางวัลที่ 1 / รางวัลใหญ่</th>
                  <th className="py-3 px-4 text-center">เลขท้าย 2 ตัว</th>
                  <th className="py-3 px-4">รางวัลอื่นๆ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {resultsData.results.map((row, idx) => {
                  return (
                    <tr key={idx} className="hover:bg-zinc-50/50 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-zinc-900">
                        {formatDate(row.draw_date)}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-zinc-950 font-mono text-base tracking-wider">
                        {row.primary || "-----"}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-zinc-900 font-mono text-base">
                        {isGlo ? row.secondary?.last_2 : row.secondary?.digits_2 || "-"}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-zinc-600">
                        {isGlo ? (
                          <div className="flex flex-col sm:flex-row gap-x-3 gap-y-0.5">
                            <div>
                              <span className="text-zinc-400 mr-1">เลขหน้า 3 ตัว:</span>
                              <span className="font-semibold font-mono">
                                {Array.isArray(row.secondary?.first_3)
                                  ? row.secondary.first_3.join(", ")
                                  : row.secondary?.first_3 || "-"}
                              </span>
                            </div>
                            <div>
                              <span className="text-zinc-400 mr-1">เลขท้าย 3 ตัว:</span>
                              <span className="font-semibold font-mono">
                                {Array.isArray(row.secondary?.last_3)
                                  ? row.secondary.last_3.join(", ")
                                  : row.secondary?.last_3 || "-"}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="flex gap-3">
                            <div>
                              <span className="text-zinc-400 mr-1">เลข 3 ตัว:</span>
                              <span className="font-semibold font-mono">
                                {row.secondary?.digits_3 || "-"}
                              </span>
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {resultsData.results.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-zinc-500 text-xs">
                      ไม่พบประวัติผลรางวัลย้อนหลัง
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : activeTab === "predictions" && predictionsData ? (
        /* =================== PREDICTIONS HISTORY TAB =================== */
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-sm font-bold text-zinc-950">
              ประวัติการทำนายและการวัดผลย้อนหลัง ({isGlo ? "รัฐบาลไทย" : "หวยลาว"})
            </h3>
            <span className="text-xs text-zinc-500 font-medium">
              ทั้งหมด {predictionsData.total_count} งวด
            </span>
          </div>

          <div className="space-y-4">
            {predictionsData.results.map((row, idx) => (
              <PredictionHistoryCard
                key={idx}
                row={row}
                type={type}
                formatDate={formatDate}
                checkHit={checkHit}
              />
            ))}
            {predictionsData.results.length === 0 && (
              <div className="w-full rounded-2xl border border-zinc-200 bg-white p-12 text-center text-zinc-500 text-sm">
                ไม่พบประวัติการทำนายในฐานข้อมูล
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* Pagination Footer */}
      {currentData && currentData.total_pages > 1 && (
        <div className="p-4 rounded-xl border border-zinc-200 bg-zinc-50 flex items-center justify-between">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-950 hover:bg-zinc-100 disabled:opacity-50 disabled:hover:bg-white disabled:hover:text-zinc-700 transition-colors"
          >
            ย้อนกลับ
          </button>
          <span className="text-xs text-zinc-500 font-medium">
            หน้า {currentData.page} จากทั้งหมด {currentData.total_pages}
          </span>
          <button
            disabled={page >= currentData.total_pages}
            onClick={() => setPage((p) => Math.min(p + 1, currentData.total_pages))}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-950 hover:bg-zinc-100 disabled:opacity-50 disabled:hover:bg-white disabled:hover:text-zinc-700 transition-colors"
          >
            ถัดไป
          </button>
        </div>
      )}
    </div>
  );
}
