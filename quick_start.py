#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无人机信号地图分析系统 - 快速开始
"""

import logging
from data_processor import DroneSignalProcessor
from signal_mapper import SignalMapper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_start_example():
    """快速开始示例"""
    print("=== 无人机信号地图分析系统 - 快速开始 ===\n")
    
    # 1. 创建处理器和映射器
    processor = DroneSignalProcessor()
    mapper = SignalMapper()
    
    # 2. 生成示例数据
    print("1. 生成示例数据...")
    sample_data = processor.generate_sample_data(
        center_lat=39.9042,  # 北京天安门
        center_lon=116.4074,
        num_points=10000,
        radius_km=2.0,       # 2公里半径，更集中的范围
        concentration_factor=0.8  # 80%的数据集中在中心区域
    )
    print(f"   生成了 {len(sample_data)} 条数据记录\n")
    
    # 3. 使用正六边形网格处理数据
    print("2. 正六边形网格数据处理...")
    hexagons = processor.process_data_with_hexagonal_grid(
        data=sample_data,
        center_lat=39.9042,
        center_lon=116.4074,
        radius_km=2.5,      # 2.5公里半径，匹配数据分布
        hex_size_km=0.05    # 100米边长的正六边形
    )
    
    hexagons_with_data = sum(1 for h in hexagons if h['data_count'] > 0)
    print(f"   创建了 {len(hexagons)} 个正六边形网格")
    print(f"   有数据的网格数: {hexagons_with_data}")
    print(f"   数据覆盖率: {hexagons_with_data/len(hexagons)*100:.1f}%\n")
    
    # 4. 生成地图
    print("3. 生成4G信号地图...")
    
    # 4G信号平均值地图
    map_4g = mapper.create_hexagonal_grid_map(
        hexagons, '4g_signal_mean', 39.9042, 116.4074
    )
    mapper.save_map(map_4g, '4g_signal_map.html')
    print("   ✅ 4G信号地图已保存: 4g_signal_map.html")
    
    # 5. 导出数据
    processor.export_hexagonal_grid_data(hexagons, 'hexagonal_grid_data.csv')
    print("   ✅ 网格数据已导出: hexagonal_grid_data.csv")
    
    # 6. 显示统计信息
    print("\n4. 4G信号统计信息:")
    
    # 4G信号统计
    hexagons_with_4g = [h for h in hexagons if h['4g_signal_mean'] is not None]
    if hexagons_with_4g:
        avg_4g_means = [h['4g_signal_mean'] for h in hexagons_with_4g]
        print(f"   4G信号统计 (基于{len(hexagons_with_4g)}个有数据的网格):")
        print(f"     平均值范围: {min(avg_4g_means):.1f} ~ {max(avg_4g_means):.1f} dBm")
        print(f"     平均信号强度: {sum(avg_4g_means)/len(avg_4g_means):.1f} dBm")
    
    print("\n=== 快速开始示例完成 ===")
    print("生成的文件:")
    print("- 4g_signal_map.html (4G信号网格地图)")
    print("- hexagonal_grid_data.csv (网格数据CSV文件)")
    print("\n您可以打开HTML文件查看交互式地图！")

def process_real_data_example():
    """处理真实数据示例"""
    print("\n=== 处理真实数据示例 ===")
    print("如果您有真实的无人机数据，可以按以下步骤处理：")
    print()
    print("1. 准备数据文件 (CSV格式):")
    print("   必需列: timestamp, latitude, longitude, altitude")
    print("   信号列: 4g_signal")
    print()
    print("2. 使用命令行处理:")
    print("   python main.py --hexagonal-grid --hex-size 1.0 your_data.csv")
    print()
    print("3. 启动Web仪表板:")
    print("   python main.py --web-dashboard")
    print()
    print("4. 程序化处理:")
    print("   from data_processor import DroneSignalProcessor")
    print("   from signal_mapper import SignalMapper")
    print("   # 加载数据")
    print("   data = processor.load_flight_data('your_data.csv')")
    print("   # 处理数据")
    print("   hexagons = processor.process_data_with_hexagonal_grid(data, lat, lon, radius, hex_size)")

if __name__ == '__main__':
    try:
        quick_start_example()
        process_real_data_example()
    except Exception as e:
        logger.error(f"快速开始示例失败: {str(e)}")
        print(f"错误: {str(e)}")
