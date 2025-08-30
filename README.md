# 飞行记录解析系统

一个简单的飞行记录JSON文件解析工具，用于提取飞行数据并输出为CSV格式。支持H3网格聚合功能。

## 功能特性

- 解析飞行记录JSON文件
- 提取飞机实时位置信息（经纬度）
- 提取SDR信号质量数据
- 输出标准CSV格式文件
- 支持自定义输出文件名
- **H3网格聚合** - 将飞行轨迹点聚合到H3六边形网格中
- **多分辨率支持** - 支持H3分辨率级别0-15

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

解析飞行记录文件并输出到默认CSV文件：

```bash
python main.py --input data/flight_replay_8UUDMAQ00A0202
```

### 指定输出文件

解析飞行记录文件并指定输出CSV文件名：

```bash
python main.py --input data/flight_replay_8UUDMAQ00A0202 --output my_flight_data.csv
```

### H3网格聚合

解析飞行记录并聚合到H3网格（分辨率13）：

```bash
python main.py --input data/flight_replay_8UUDMAQ00A0202 --h3 --resolution 13
```

### H3聚合并指定输出文件

```bash
python main.py --input data/flight_replay_8UUDMAQ00A0202 --h3 --resolution 13 --output-raw raw_data.csv --output-h3 h3_data.csv
```

## 输出格式

### 原始数据CSV格式

解析后的原始CSV文件包含以下列：

- `timestamp`: 时间戳（已转换为可读格式）
- `latitude`: 飞机纬度
- `longitude`: 飞机经度
- `sdr_signal`: SDR信号质量

### H3聚合数据CSV格式

H3聚合后的CSV文件包含以下列：

- `h3_index`: H3网格索引（全球唯一标识符）
- `point_count`: 该网格内的数据点数量
- `avg_sdr_signal`: 平均SDR信号强度
- `max_sdr_signal`: 最大SDR信号强度
- `min_sdr_signal`: 最小SDR信号强度

**注意**: 为了简化数据结构，以下字段已被移除：
- 时间戳相关字段（first_timestamp, last_timestamp）
- 经纬度统计字段（avg_latitude, min_latitude, max_latitude, avg_longitude, min_longitude, max_longitude）
- SDR信号标准差（std_sdr_signal）
- H3网格几何信息（h3_center_lat, h3_center_lng, h3_area_km2）

**数据特点**:
- 每个H3网格代表一个边长约4米的六边形区域
- 网格面积约42平方米（相当于一个中等房间大小）
- 适合城市级别的精细分析
- 数据文件更简洁，处理效率更高

## H3分辨率说明

H3分辨率级别决定了网格的大小：

| 分辨率 | 平均边长 | 平均面积 | 说明 |
|--------|----------|----------|------|
| 0 | 110.7 km | 4,250,547 km² | 最大网格 |
| 9 | 174 m | 0.105 km² | 城市级别 |
| 10 | 62 m | 0.015 km² | 街区级别 |
| 11 | 22 m | 0.002 km² | 建筑级别 |
| 12 | 7.6 m | 0.0003 km² | 精确位置 |
| 13 | 4.04 m | 0.000042 km² | 高精度（当前使用） |
| 14 | 0.96 m | 0.000006 km² | 超高精度 |
| 15 | 0.34 m | 0.0000009 km² | 最高精度 |

## 项目结构

```
fly/
├── main.py              # 主程序入口
├── data_processor.py    # 数据处理核心模块
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明
├── data/               # 数据目录
│   └── flight_replay_8UUDMAQ00A0202  # 飞行记录文件
└── flight_record_parse.log  # 解析日志
```

## 注意事项

- 输入文件必须是有效的JSON格式
- 程序会自动处理时间戳转换（从毫秒转换为可读格式）
- 如果飞行记录中没有位置信息，输出的CSV文件可能为空
- 信号数据只在变化时才会更新记录
- H3分辨率越高，网格越小，数据越精确，但处理时间也越长
- 建议根据数据密度选择合适的H3分辨率

## 日志

程序运行时会生成详细的日志信息，包括：
- 解析进度
- 数据统计信息
- H3聚合统计信息
- 错误信息（如果有）

日志文件保存在 `flight_record_parse.log` 中。

## TODO

### API设计

基于生成的H3聚合数据，可以设计简洁的API接口：

```python
# 示例：Flask API
from flask import Flask, jsonify
import pandas as pd
import h3

app = Flask(__name__)

@app.route('/api/h3-data')
def get_h3_data():
    # 读取H3聚合数据
    df = pd.read_csv('h3_aggregated_res13.csv')
    
    # 转换为JSON格式，添加中心点坐标
    data = []
    for _, row in df.iterrows():
        center = h3.cell_to_latlng(row['h3_index'])
        data.append({
            "h3_index": row['h3_index'],
            "center_lat": center[0],
            "center_lng": center[1],
            "avg_sdr_signal": row['avg_sdr_signal'],
            "max_sdr_signal": row['max_sdr_signal'],
            "min_sdr_signal": row['min_sdr_signal']
        })
    
    return jsonify({
        "success": True,
        "data": data,
        "metadata": {
            "resolution": 13,
            "grid_size_meters": 4.04,
            "total_grids": len(data)
        }
    })
```

### 数据格式说明

#### 后端返回的JSON格式：
```json
{
  "success": true,
  "data": [
    {
      "h3_index": "8d411c18e08013f",
      "center_lat": 22.793704684705848,
      "center_lng": 114.3586296726113,
      "avg_sdr_signal": 5.0,
      "max_sdr_signal": 5,
      "min_sdr_signal": 5
    }
  ],
  "metadata": {
    "resolution": 13,
    "grid_size_meters": 4.04,
    "total_grids": 232
  }
}
```
