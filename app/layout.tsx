import type { Metadata } from "next";
import { Noto_Sans_Thai } from "next/font/google";
import "./globals.css";

const notoSansThai = Noto_Sans_Thai({
  variable: "--font-noto-sans-thai",
  subsets: ["thai", "latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Huay KVJ - สถิติและระบบทำนายหวยด้วย AI",
  description: "ระบบตรวจผลหวย วิเคราะห์สถิติ และทำนายเลขเด็ดงวดถัดไปด้วยปัญญาประดิษฐ์ (LSTM & Ensemble)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="th"
      className={`${notoSansThai.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900 font-sans">
        {children}
      </body>
    </html>
  );
}

