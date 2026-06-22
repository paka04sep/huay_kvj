/**
 * ประกอบ URL สำหรับการเชื่อมต่อ Backend API ให้รองรับทั้งการใช้งานบน Localhost 
 * และการเข้าใช้งานผ่านอุปกรณ์อื่นในวงแลนเดียวกัน (LAN)
 */
export function getApiUrl(path: string): string {
  // คืนค่าเป็น relative path เพื่อให้วิ่งผ่าน Next.js rewrite proxy ในพอร์ต 3000 เดียวกัน
  // ช่วยแก้ปัญหาการเชื่อมต่อข้ามอุปกรณ์ในวงแลน และเลี่ยงปัญหา CORS/Firewall
  return path;
}
