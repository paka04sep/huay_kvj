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

export default function HistoryPanel({ type }: HistoryPanelProps) {
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Reset page when switching types
  useEffect(() => {
    setPage(1);
  }, [type]);

  useEffect(() => {
    async function fetchHistory() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          getApiUrl(`/api/results/history?type=${type}&page=${page}&limit=${limit}`)
        );
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || "Failed to load lottery history");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [type, page, limit]);

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

  const isGlo = type === "glo";

  return (
    <div className="w-full space-y-4">
      {loading ? (
        <div className="w-full rounded-2xl border border-zinc-200 bg-white p-12 text-center animate-pulse">
          <div className="mx-auto h-4 w-48 rounded bg-zinc-200 mb-6"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 rounded bg-zinc-150 w-full"></div>
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-6 text-center text-red-700">
          <p className="font-semibold">เกิดข้อผิดพลาดในการโหลดประวัติรางวัล</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
        </div>
      ) : data ? (
        <div className="rounded-2xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="p-4 border-b border-zinc-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-zinc-950">
              ประวัติผลรางวัลย้อนหลัง ({isGlo ? "รัฐบาลไทย" : "หวยลาว"})
            </h3>
            <span className="text-xs text-zinc-500 font-medium">
              ทั้งหมด {data.total_count} รายการ
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
                {data.results.map((row, idx) => {
                  const hasSecondary = row.secondary && Object.keys(row.secondary).length > 0;
                  return (
                    <tr key={idx} className="hover:bg-zinc-50/50 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-zinc-900">
                        {formatDate(row.draw_date)}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-zinc-950 font-mono text-base">
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
                            {/* <div>
                              <span className="text-zinc-400 mr-1">เลขท้าย 4 ตัว:</span>
                              <span className="font-semibold font-mono">
                                {row.secondary?.digits_4 || "-"}
                              </span>
                            </div> */}
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
                {data.results.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-zinc-500 text-xs">
                      ไม่พบประวัติผลรางวัลย้อนหลัง
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Table Pagination Footer */}
          {data.total_pages > 1 && (
            <div className="p-4 border-t border-zinc-150 bg-zinc-50 flex items-center justify-between">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-950 hover:bg-zinc-100 disabled:opacity-50 disabled:hover:bg-white disabled:hover:text-zinc-700 transition-colors"
              >
                ย้อนกลับ
              </button>
              <span className="text-xs text-zinc-500 font-medium">
                หน้า {data.page} จากทั้งหมด {data.total_pages}
              </span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(p + 1, data.total_pages))}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-950 hover:bg-zinc-100 disabled:opacity-50 disabled:hover:bg-white disabled:hover:text-zinc-700 transition-colors"
              >
                ถัดไป
              </button>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
