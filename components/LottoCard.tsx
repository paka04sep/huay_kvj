"use client";

import React from "react";

interface LottoCardProps {
  type: "glo" | "lao";
  data: {
    lottery_type: string;
    draw_date: string;
    draw_number: string;
    primary: string;
    secondary: Record<string, any>;
    source_url?: string;
    fetched_at?: string;
  } | null;
  loading: boolean;
  error: string | null;
}

export default function LottoCard({ type, data, loading, error }: LottoCardProps) {
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

  if (loading) {
    return (
      <div className="w-full rounded-2xl border border-zinc-200 bg-white p-8 text-center animate-pulse">
        <div className="mx-auto h-4 w-24 rounded bg-zinc-200 mb-4"></div>
        <div className="mx-auto h-12 w-48 rounded bg-zinc-200 mb-6"></div>
        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="h-20 rounded bg-zinc-100"></div>
          <div className="h-20 rounded bg-zinc-100"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full rounded-2xl border border-red-150 bg-red-50 p-6 text-center text-red-700">
        <p className="font-semibold">ไม่สามารถโหลดข้อมูลรางวัลได้</p>
        <p className="text-xs text-red-500 mt-1">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full rounded-2xl border border-zinc-200 bg-white p-8 text-center text-zinc-500">
        ไม่มีข้อมูลรางวัลล่าสุด
      </div>
    );
  }

  const isGlo = type === "glo";

  return (
    <div className="w-full rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-sm">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-100 pb-4 mb-6">
        <div>
          <span className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-800">
            {isGlo ? "สำนักงานสลากกินแบ่งรัฐบาล" : "หวยพัฒนา ลาว"}
          </span>
          <h2 className="text-xl font-bold text-zinc-950 mt-1">
            งวดประจำวันที่ {formatDate(data.draw_date)}
          </h2>
        </div>
        <div className="mt-2 sm:mt-0 text-left sm:text-right text-xs text-zinc-500">
          <div>งวดที่: {data.draw_number || "-"}</div>
          {data.fetched_at && (
            <div className="text-[10px] text-zinc-400 mt-0.5">
              อัปเดตล่าสุด: {new Date(data.fetched_at).toLocaleTimeString("th-TH")}
            </div>
          )}
        </div>
      </div>

      {/* Main Prize */}
      <div className="bg-zinc-50 rounded-xl p-6 sm:p-8 text-center border border-zinc-100">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
          {isGlo ? "รางวัลที่ 1" : "เลขรางวัลพัฒนา"}
        </p>
        <div className="text-4xl sm:text-5xl font-extrabold tracking-widest text-zinc-950 select-all font-mono">
          {data.primary || "------"}
        </div>
      </div>

      {/* Secondary Prizes */}
      <div className="mt-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-4">
          รางวัลเลขท้ายและเลขอื่น ๆ
        </h3>

        {isGlo ? (
          /* GLO Secondary Prizes */
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Last 2 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลขท้าย 2 ตัว</p>
              <p className="text-2xl font-bold text-zinc-950 font-mono">
                {data.secondary?.last_2 || "--"}
              </p>
            </div>
            
            {/* First 3 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลขหน้า 3 ตัว</p>
              <div className="flex justify-center gap-3">
                {Array.isArray(data.secondary?.first_3) ? (
                  data.secondary.first_3.map((num: string, idx: number) => (
                    <span key={idx} className="text-xl font-bold text-zinc-950 font-mono">
                      {num}
                    </span>
                  ))
                ) : (
                  <span className="text-xl font-bold text-zinc-950 font-mono">
                    {data.secondary?.first_3 || "--"}
                  </span>
                )}
              </div>
            </div>

            {/* Last 3 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลขท้าย 3 ตัว</p>
              <div className="flex justify-center gap-3">
                {Array.isArray(data.secondary?.last_3) ? (
                  data.secondary.last_3.map((num: string, idx: number) => (
                    <span key={idx} className="text-xl font-bold text-zinc-950 font-mono">
                      {num}
                    </span>
                  ))
                ) : (
                  <span className="text-xl font-bold text-zinc-950 font-mono">
                    {data.secondary?.last_3 || "--"}
                  </span>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Lao Secondary Prizes */
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* 4 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลข 4 ตัว</p>
              <p className="text-2xl font-bold text-zinc-950 font-mono">
                {data.secondary?.digits_4 || "--"}
              </p>
            </div>
            
            {/* 3 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลข 3 ตัว</p>
              <p className="text-2xl font-bold text-zinc-950 font-mono">
                {data.secondary?.digits_3 || "--"}
              </p>
            </div>

            {/* 2 Digits */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center">
              <p className="text-xs font-medium text-zinc-500 mb-1">เลข 2 ตัว</p>
              <p className="text-2xl font-bold text-zinc-950 font-mono">
                {data.secondary?.digits_2 || "--"}
              </p>
            </div>
          </div>
        )}
      </div>

      {data.source_url && (
        <div className="mt-6 text-center">
          <a
            href={data.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-zinc-500 underline hover:text-zinc-900 transition-colors"
          >
            ดูผลรางวัลอย่างเป็นทางการจากแหล่งที่มา
          </a>
        </div>
      )}
    </div>
  );
}
