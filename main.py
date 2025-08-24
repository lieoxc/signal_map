#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无人机信号地图分析系统
主程序入口
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from data_processor import DroneSignalProcessor
from signal_mapper import SignalMapper
# Web仪表板功能已移除

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_analysis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def create_sample_data():
    """创建示例数据文件"""
    try:
        processor = DroneSignalProcessor()
        
        # 生成示例数据
        logger.info("正在生成示例数据...")
        sample_data = processor.generate_sample_data(
            center_lat=39.9042,  # 北京天安门
            center_lon=116.4074,
            num_points=1000
        )
        
        # 保存为CSV文件
        output_file = 'sample_drone_data.csv'
        sample_data.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"示例数据已保存到: {output_file}")
        
        # 显示数据统计
        logger.info(f"数据统计:")
        logger.info(f"  总记录数: {len(sample_data)}")
        logger.info(f"  纬度范围: {sample_data['latitude'].min():.4f} - {sample_data['latitude'].max():.4f}")
        logger.info(f"  经度范围: {sample_data['longitude'].min():.4f} - {sample_data['longitude'].max():.4f}")
        logger.info(f"  4G信号范围: {sample_data['4g_signal'].min():.1f} - {sample_data['4g_signal'].max():.1f} dBm")
        logger.info(f"  SDR信号范围: {sample_data['sdr_signal'].min():.1f} - {sample_data['sdr_signal'].max():.1f}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"创建示例数据失败: {str(e)}")
        raise

def process_data_file(data_file, center_lat=None, center_lon=None, radius=10.0, use_hexagonal_grid=False, hex_size=1.0):
    """处理数据文件并生成地图"""
    try:
        processor = DroneSignalProcessor()
        mapper = SignalMapper()
        
        # 加载数据
        logger.info(f"正在加载数据文件: {data_file}")
        data = processor.load_flight_data(data_file)
        
        # 确定中心点
        if center_lat is None:
            center_lat = data['latitude'].mean()
        if center_lon is None:
            center_lon = data['longitude'].mean()
        
        logger.info(f"分析中心点: ({center_lat:.4f}, {center_lon:.4f})")
        
        # 创建输出目录
        output_dir = Path('output_maps')
        output_dir.mkdir(exist_ok=True)
        
        if use_hexagonal_grid:
            # 使用正六边形网格处理
            logger.info(f"使用正六边形网格处理数据 (网格大小: {hex_size}km)")
            hexagons = processor.process_data_with_hexagonal_grid(
                data=data,
                center_lat=center_lat,
                center_lon=center_lon,
                radius_km=radius,
                hex_size_km=hex_size
            )
            
            # 生成正六边形网格地图
            logger.info("正在生成正六边形网格地图...")
            
            # 4G信号平均值地图
            map_4g_mean = mapper.create_hexagonal_grid_map(
                hexagons, '4g_signal_mean', center_lat, center_lon
            )
            mapper.save_map(map_4g_mean, output_dir / 'hexagonal_4g_mean_map.html')
            
            # 4G信号最大值地图
            map_4g_max = mapper.create_hexagonal_grid_map(
                hexagons, '4g_signal_max', center_lat, center_lon
            )
            mapper.save_map(map_4g_max, output_dir / 'hexagonal_4g_max_map.html')
            
            # 4G信号最小值地图
            map_4g_min = mapper.create_hexagonal_grid_map(
                hexagons, '4g_signal_min', center_lat, center_lon
            )
            mapper.save_map(map_4g_min, output_dir / 'hexagonal_4g_min_map.html')
            
            # SDR信号平均值地图
            map_sdr_mean = mapper.create_hexagonal_grid_map(
                hexagons, 'sdr_signal_mean', center_lat, center_lon
            )
            mapper.save_map(map_sdr_mean, output_dir / 'hexagonal_sdr_mean_map.html')
            
            # 双信号对比地图
            map_dual = mapper.create_dual_hexagonal_grid_map(
                hexagons, center_lat, center_lon
            )
            mapper.save_map(map_dual, output_dir / 'hexagonal_dual_signal_map.html')
            
            # 生成统计图表
            logger.info("正在生成正六边形网格统计图表...")
            mapper.create_hexagonal_grid_statistics_plot(hexagons, output_dir / 'hexagonal_grid_statistics.png')
            
            # 导出网格数据
            processor.export_hexagonal_grid_data(hexagons, output_dir / 'hexagonal_grid_data.csv')
            
        else:
            # 使用传统热力图处理
            # 区域过滤
            if radius > 0:
                data = processor.filter_data_by_area(data, center_lat, center_lon, radius)
                logger.info(f"区域过滤完成，保留{len(data)}条记录")
            
            # 标准化信号数据
            data = processor.normalize_signal_data(data)
            
            # 生成4G信号地图
            logger.info("正在生成4G信号地图...")
            map_4g = mapper.create_signal_heatmap(data, '4g_signal', center_lat, center_lon)
            mapper.save_map(map_4g, output_dir / '4g_signal_map.html')
            
            # 生成SDR信号地图
            logger.info("正在生成SDR信号地图...")
            map_sdr = mapper.create_signal_heatmap(data, 'sdr_signal', center_lat, center_lon)
            mapper.save_map(map_sdr, output_dir / 'sdr_signal_map.html')
            
            # 生成双信号对比地图
            logger.info("正在生成双信号对比地图...")
            map_dual = mapper.create_dual_signal_map(data, center_lat, center_lon)
            mapper.save_map(map_dual, output_dir / 'dual_signal_map.html')
            
            # 生成统计图表
            logger.info("正在生成统计图表...")
            mapper.create_signal_statistics_plot(data, output_dir / 'signal_statistics.png')
            
            # 生成等高线图
            logger.info("正在生成等高线图...")
            mapper.create_signal_contour_plot(data, '4g_signal', output_dir / '4g_signal_contour.png')
            mapper.create_signal_contour_plot(data, 'sdr_signal', output_dir / 'sdr_signal_contour.png')
        
        logger.info(f"所有地图和图表已保存到: {output_dir}")
        
        return output_dir
        
    except Exception as e:
        logger.error(f"处理数据文件失败: {str(e)}")
        raise

def run_web_dashboard(host='127.0.0.1', port=8050):
    """启动Web仪表板（功能已移除）"""
    logger.warning("Web仪表板功能已被移除，请使用命令行功能")
    raise NotImplementedError("Web仪表板功能已被移除")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='无人机信号地图分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 生成示例数据
  python main.py --sample
  
  # 处理数据文件（传统热力图）
  python main.py --data sample_drone_data.csv --center-lat 39.9042 --center-lon 116.4074 --radius 5.0 --process
  
  # 使用正六边形网格处理数据
  python main.py --data sample_drone_data.csv --center-lat 39.9042 --center-lon 116.4074 --radius 5.0 --hexagonal-grid --hex-size 1.0 --process
  
  # Web仪表板功能已移除
  
  # 完整流程：生成示例数据并使用正六边形网格处理
  python main.py --sample --hexagonal-grid --process
        """
    )
    
    parser.add_argument('--sample', action='store_true',
                       help='生成示例数据文件')
    
    parser.add_argument('--data', type=str,
                       help='输入数据文件路径 (CSV或JSON格式)')
    
    parser.add_argument('--center-lat', type=float,
                       help='机场中心纬度')
    
    parser.add_argument('--center-lon', type=float,
                       help='机场中心经度')
    
    parser.add_argument('--radius', type=float, default=10.0,
                       help='分析半径 (公里，默认10.0)')
    
    parser.add_argument('--hexagonal-grid', action='store_true',
                       help='使用正六边形网格处理数据')
    
    parser.add_argument('--hex-size', type=float, default=1.0,
                       help='正六边形网格边长 (公里，默认1.0)')
    
    parser.add_argument('--process', action='store_true',
                       help='处理数据并生成地图')
    
    parser.add_argument('--web', action='store_true',
                       help='启动Web仪表板')
    
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Web仪表板主机地址 (默认127.0.0.1)')
    
    parser.add_argument('--port', type=int, default=8050,
                       help='Web仪表板端口 (默认8050)')
    
    args = parser.parse_args()
    
    try:
        if args.sample:
            create_sample_data()
        
        if args.data and args.process:
            process_data_file(args.data, args.center_lat, args.center_lon, args.radius, 
                            args.hexagonal_grid, args.hex_size)
        
        if args.web:
            run_web_dashboard(args.host, args.port)
        
        # 如果没有指定任何操作，显示帮助信息
        if not any([args.sample, args.data, args.web]):
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
