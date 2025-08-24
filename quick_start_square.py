#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无人机信号地图分析系统 - 正方形网格快速开始
"""

import logging
import time
from data_processor import DroneSignalProcessor
from signal_mapper import SignalMapper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_start_square_example():
    """正方形网格快速开始示例"""
    print("=== 无人机信号地图分析系统 - 正方形网格快速开始 ===\n")
    
    start_time = time.time()
    
    # 1. 创建处理器和映射器
    processor = DroneSignalProcessor()
    mapper = SignalMapper()
    
    # 2. 生成示例数据
    print("1. 生成示例数据...")
    data_start = time.time()
    sample_data = processor.generate_sample_data(
        center_lat=39.9042,  # 北京天安门
        center_lon=116.4074,
        num_points=10000,
        radius_km=2.0,       # 2公里半径，更集中的范围
        concentration_factor=0.8  # 80%的数据集中在中心区域
    )
    data_time = time.time() - data_start
    print(f"   生成了 {len(sample_data)} 条数据记录 (耗时: {data_time:.2f}秒)\n")
    
    # 3. 使用正方形网格处理数据
    print("2. 正方形网格数据处理...")
    grid_start = time.time()
    squares = processor.process_data_with_square_grid(
        data=sample_data,
        center_lat=39.9042,
        center_lon=116.4074,
        radius_km=2.5,      # 2.5公里半径，匹配数据分布
        square_size_km=0.05   # 50米边长的正方形
    )
    grid_time = time.time() - grid_start
    
    squares_with_data = sum(1 for s in squares if s['data_count'] > 0)
    print(f"   创建了 {len(squares)} 个正方形网格")
    print(f"   有数据的网格数: {squares_with_data}")
    print(f"   数据覆盖率: {squares_with_data/len(squares)*100:.1f}%")
    print(f"   处理耗时: {grid_time:.2f}秒\n")
    
    # 4. 生成地图
    print("3. 生成4G信号地图...")
    map_start = time.time()
    
    # 4G信号平均值地图
    map_4g = mapper.create_square_grid_map(
        squares, '4g_signal_mean', 39.9042, 116.4074
    )
    mapper.save_map(map_4g, 'square_4g_signal_map.html')
    print("   ✅ 4G信号地图已保存: square_4g_signal_map.html")
    
    map_time = time.time() - map_start
    print(f"   地图生成耗时: {map_time:.2f}秒\n")
    
    # 5. 导出数据
    export_start = time.time()
    processor.export_square_grid_data(squares, 'square_grid_data.csv')
    export_time = time.time() - export_start
    print("   ✅ 网格数据已导出: square_grid_data.csv")
    print(f"   导出耗时: {export_time:.2f}秒\n")
    
    # 6. 显示统计信息
    print("4. 4G信号统计信息:")
    
    # 4G信号统计
    squares_with_4g = [s for s in squares if s['4g_signal_mean'] is not None]
    if squares_with_4g:
        avg_4g_means = [s['4g_signal_mean'] for s in squares_with_4g]
        print(f"   4G信号统计 (基于{len(squares_with_4g)}个有数据的网格):")
        print(f"     平均值范围: {min(avg_4g_means):.1f} ~ {max(avg_4g_means):.1f} dBm")
        print(f"     平均信号强度: {sum(avg_4g_means)/len(avg_4g_means):.1f} dBm")
    
    total_time = time.time() - start_time
    print(f"\n=== 正方形网格快速开始示例完成 ===")
    print(f"总耗时: {total_time:.2f}秒")
    print("生成的文件:")
    print("- square_4g_signal_map.html (4G信号正方形网格地图)")
    print("- square_grid_data.csv (正方形网格数据CSV文件)")
    print("\n您可以打开HTML文件查看交互式地图！")

if __name__ == '__main__':
    try:
        quick_start_square_example()
    except Exception as e:
        logger.error(f"正方形网格快速开始示例失败: {str(e)}")
        print(f"错误: {str(e)}")
