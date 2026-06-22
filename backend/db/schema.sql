-- สร้าง extension สำหรับ uuid-ossp (ถ้ายังไม่มี)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ตารางเก็บประเภทหวย
CREATE TABLE IF NOT EXISTS lottery_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Bangkok',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. ตารางเก็บผลการออกรางวัล
CREATE TABLE IF NOT EXISTS lottery_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lottery_type_id UUID NOT NULL REFERENCES lottery_types(id) ON DELETE CASCADE,
    draw_date DATE NOT NULL,
    draw_number VARCHAR(50),
    result_json JSONB NOT NULL,
    source_url VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'rejected', 'pending'
    error_reason TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_type_draw_date UNIQUE (lottery_type_id, draw_date)
);

-- สร้างฟังก์ชันและ trigger สำหรับอัปเดต updated_at อัตโนมัติ
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_lottery_types_updated_at
    BEFORE UPDATE ON lottery_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lottery_results_updated_at
    BEFORE UPDATE ON lottery_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- สร้าง Index เพื่อเพิ่มประสิทธิภาพในการ Query ย้อนหลังตามประเภทและวันที่
CREATE INDEX IF NOT EXISTS idx_lottery_results_type_date ON lottery_results(lottery_type_id, draw_date DESC);
CREATE INDEX IF NOT EXISTS idx_lottery_results_status ON lottery_results(status);

-- 3. เพิ่มข้อมูลประเภทหวยพื้นฐาน
INSERT INTO lottery_types (code, name, timezone) VALUES
('glo', 'สลากกินแบ่งรัฐบาล', 'Asia/Bangkok'),
('lao', 'หวยลาว', 'Asia/Vientiane'),
('hanoi', 'หวยฮานอย', 'Asia/Ho_Chi_Minh'),
('yeekee', 'หวยยี่กี', 'Asia/Bangkok')
ON CONFLICT (code) DO NOTHING;
