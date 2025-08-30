-- 飞行记录解析系统 - PostgreSQL数据库表结构设计
-- 简化的H3网格信号系统

-- H3网格数据表 - 存储聚合后的H3网格信号数据
CREATE TABLE h3_grid_data (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,         -- 设备唯一标识符，如：8UUDMAQ00A0202
    resolution INTEGER NOT NULL,             -- H3分辨率级别 (0-15)
    h3_index VARCHAR(20) NOT NULL,          -- H3网格索引（全球唯一）
    point_count INTEGER NOT NULL,           -- 网格内数据点数量
    avg_sdr_signal DECIMAL(5,2),            -- 平均SDR信号强度
    max_sdr_signal INTEGER,                 -- 最大SDR信号强度
    min_sdr_signal INTEGER,                 -- 最小SDR信号强度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 复合索引优化查询性能
    UNIQUE(device_id, resolution, h3_index)
);

-- 创建索引优化查询性能
CREATE INDEX idx_h3_grid_data_device ON h3_grid_data(device_id);
CREATE INDEX idx_h3_grid_data_resolution ON h3_grid_data(resolution);
CREATE INDEX idx_h3_grid_data_h3_index ON h3_grid_data(h3_index);
CREATE INDEX idx_h3_grid_data_signal ON h3_grid_data(avg_sdr_signal);
