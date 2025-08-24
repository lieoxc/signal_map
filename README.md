# 无人机信号地图分析系统

一个基于Python的无人机信号地图分析系统，用于分析无人机飞行过程中记录的4G信号质量数据，并生成可视化的信号覆盖地图。支持六边形网格和正方形网格两种空间划分方式。

## 功能特性

### 🗺️ 信号地图可视化
- **4G信号强度热力图** - 显示无人机飞行区域的4G信号覆盖情况
- **六边形网格地图** - 基于正六边形网格的信号强度可视化
- **正方形网格地图** - 基于正方形网格的高性能信号强度可视化
- **交互式地图** - 支持缩放、平移、点击查看详细信息

### 📊 数据分析功能
- **信号强度分布统计** - 直方图显示信号强度分布
- **信号随距离变化分析** - 散点图显示信号强度与距离的关系
- **等高线图** - 2D等高线图显示信号强度分布
- **数据表格** - 详细的数据记录查看

### 🔧 数据处理能力
- **多格式支持** - 支持CSV和JSON格式的数据文件
- **数据合并** - 自动合并飞行轨迹数据和信号数据
- **区域过滤** - 根据指定中心点和半径过滤数据
- **数据标准化** - 自动标准化信号数据用于可视化
- **六边形网格** - 支持正六边形网格空间划分，每个网格计算平均值、最大值、最小值
- **正方形网格** - 支持正方形网格空间划分，使用空间索引优化性能

### ⚡ 性能优化
- **空间索引** - 正方形网格使用STRtree空间索引，性能提升10倍
- **集中数据生成** - 支持可配置的数据集中度，模拟真实飞行场景
- **内存优化** - 优化的数据结构，减少内存占用

## 系统架构

```
无人机信号地图分析系统/
├── data_processor.py      # 数据处理模块 (30KB)
├── signal_mapper.py       # 地图绘制模块 (37KB)
├── main.py               # 主程序入口 (10KB)
├── quick_start.py        # 六边形网格快速开始 (4KB)
├── quick_start_square.py # 正方形网格快速开始 (5KB)
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明文档
```

## 安装和使用

### 1. 环境要求
- Python 3.8+
- Windows/Linux/macOS

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 快速开始

#### 六边形网格快速开始
```bash
python quick_start.py
```
这将生成示例数据并使用六边形网格创建信号地图。

#### 正方形网格快速开始（推荐）
```bash
python quick_start_square.py
```
这将生成示例数据并使用正方形网格创建信号地图，性能更好。

#### 处理数据文件
```bash
# 生成示例数据
python main.py --sample

# 传统热力图处理
python main.py --data your_data.csv --center-lat 39.9042 --center-lon 116.4074 --radius 5.0 --process

# 六边形网格处理
python main.py --data your_data.csv --center-lat 39.9042 --center-lon 116.4074 --radius 5.0 --hexagonal-grid --hex-size 1.0 --process

# 完整流程：生成示例数据并使用六边形网格处理
python main.py --sample --hexagonal-grid --process
```

## 数据格式

### 输入数据格式
系统支持CSV和JSON格式的数据文件，需要包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| timestamp | datetime | 时间戳 |
| latitude | float | 纬度 |
| longitude | float | 经度 |
| altitude | float | 高度（米） |
| 4g_signal | float | 4G信号强度（dBm） |

### 示例数据格式
```csv
timestamp,latitude,longitude,altitude,4g_signal
2024-01-01 10:00:00,39.9042,116.4074,100.5,-75.2
2024-01-01 10:00:02,39.9045,116.4078,102.1,-78.1
...
```

## 网格类型对比

### 六边形网格 vs 正方形网格

| 特性 | 六边形网格 | 正方形网格 |
|------|------------|------------|
| 几何复杂度 | 6个顶点，复杂多边形判断 | 4个顶点，简单矩形判断 |
| 数据分配算法 | 暴力循环，O(n×m) | 空间索引(STRtree)，O(n×log m) |
| 内存占用 | 每个网格6个顶点 | 每个网格4个顶点 |
| 处理时间 | ~30秒 | ~3秒 |
| 性能提升 | 基准 | 约10倍 |
| 适用场景 | 需要精确六边形网格 | 追求性能，可接受正方形网格 |

## 核心模块说明

### `data_processor.py`
数据处理核心模块，提供以下功能：
- 数据加载和验证
- 数据合并和过滤
- 六边形网格生成和处理
- 正方形网格生成和处理（优化版本）
- 示例数据生成（支持集中度配置）

### `signal_mapper.py`
地图绘制模块，提供以下功能：
- 热力图生成
- 六边形网格地图
- 正方形网格地图
- 等高线图
- 统计图表

### `main.py`
命令行主程序，提供完整的命令行界面：
- 参数解析和验证
- 示例数据生成
- 数据文件处理
- 多种处理模式支持

### `quick_start.py` / `quick_start_square.py`
快速开始脚本，用于演示系统功能：
- 生成示例数据
- 使用指定网格类型处理
- 生成地图和统计信息
- 性能对比分析

## 使用示例

### 1. 生成示例数据
```python
from data_processor import DroneSignalProcessor

processor = DroneSignalProcessor()
sample_data = processor.generate_sample_data(
    center_lat=39.9042,
    center_lon=116.4074,
    num_points=10000,
    radius_km=2.0,
    concentration_factor=0.8  # 80%数据集中在中心
)
```

### 2. 六边形网格处理
```python
from data_processor import DroneSignalProcessor
from signal_mapper import SignalMapper

processor = DroneSignalProcessor()
mapper = SignalMapper()

# 处理数据
hexagons = processor.process_data_with_hexagonal_grid(
    data=sample_data,
    center_lat=39.9042,
    center_lon=116.4074,
    radius_km=5.0,
    hex_size_km=0.1
)

# 生成地图
map_4g = mapper.create_hexagonal_grid_map(hexagons, '4g_signal_mean', 39.9042, 116.4074)
mapper.save_map(map_4g, '4g_signal_map.html')
```

### 3. 正方形网格处理（推荐）
```python
# 处理数据
squares = processor.process_data_with_square_grid(
    data=sample_data,
    center_lat=39.9042,
    center_lon=116.4074,
    radius_km=5.0,
    square_size_km=0.05
)

# 生成地图
map_4g = mapper.create_square_grid_map(squares, '4g_signal_mean', 39.9042, 116.4074)
mapper.save_map(map_4g, 'square_4g_signal_map.html')
```

## 输出文件说明

### 生成的文件类型
- **HTML地图文件** - 交互式信号地图，可在浏览器中查看
- **CSV数据文件** - 网格化后的数据，包含统计信息
- **PNG图表文件** - 静态统计图表

### 文件命名规则
- `4g_signal_map.html` - 六边形网格4G信号地图
- `square_4g_signal_map.html` - 正方形网格4G信号地图
- `hexagonal_grid_data.csv` - 六边形网格数据
- `square_grid_data.csv` - 正方形网格数据

## 性能优化建议

1. **使用正方形网格** - 相比六边形网格，性能提升约10倍
2. **调整网格大小** - 根据数据密度调整网格大小，平衡精度和性能
3. **数据集中度** - 使用 `concentration_factor` 参数控制数据分布
4. **内存管理** - 大数据集建议分批处理

## 故障排除

### 常见问题
1. **依赖包安装失败** - 确保Python版本为3.8+
2. **数据格式错误** - 检查CSV文件格式和必需字段
3. **内存不足** - 减少数据点数量或增加网格大小
4. **地图显示异常** - 检查坐标范围是否合理

### 日志文件
系统会生成 `signal_analysis.log` 日志文件，包含详细的处理信息和错误信息。

## 更新日志

### v2.0.0 (当前版本)
- ✅ 移除Web仪表板功能，专注命令行工具
- ✅ 添加正方形网格支持，性能提升10倍
- ✅ 优化数据生成，支持集中度配置
- ✅ 简化项目结构，删除冗余文件
- ✅ 更新文档和示例

### v1.0.0
- ✅ 基础信号地图功能
- ✅ 六边形网格支持
- ✅ Web仪表板功能

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。
