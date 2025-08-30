#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞行记录解析系统
主程序入口
"""

import argparse
import logging
import sys
from pathlib import Path

from data_processor import FlightRecordParser
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flight_record_parse.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_flight_record(json_file_path: str, output_csv_path: str = None):
    """解析飞行记录文件并输出到CSV"""
    try:
        parser = FlightRecordParser()
        
        # 解析飞行记录文件
        logger.info(f"开始解析飞行记录文件: {json_file_path}")
        df = parser.parse_flight_record_json(json_file_path, output_csv_path)
        
        if len(df) > 0:
            logger.info("✅ 解析完成！")
            logger.info(f"总记录数: {len(df)}")
            logger.info(f"时间范围: {df['timestamp'].min()} - {df['timestamp'].max()}")
            logger.info(f"纬度范围: {df['latitude'].min():.6f} - {df['latitude'].max():.6f}")
            logger.info(f"经度范围: {df['longitude'].min():.6f} - {df['longitude'].max():.6f}")
            
            if 'sdr_signal' in df.columns:
                sdr_data = df['sdr_signal'].dropna()
                if len(sdr_data) > 0:
                    logger.info(f"SDR信号范围: {sdr_data.min():.1f} - {sdr_data.max():.1f}")
            
            if output_csv_path:
                logger.info(f"数据已保存到: {output_csv_path}")
            else:
                logger.info("数据已保存到: parsed_flight_data.csv")
        else:
            logger.warning("⚠️ 解析完成，但没有找到有效数据")
            
    except Exception as e:
        logger.error(f"❌ 解析失败: {str(e)}")
        raise

def parse_and_aggregate_to_h3(json_file_path: str, resolution: int = 13, 
                             output_raw_csv: str = None, output_h3_csv: str = None):
    """解析飞行记录并聚合到H3网格"""
    try:
        parser = FlightRecordParser()
        
        # 解析飞行记录并聚合到H3网格
        logger.info(f"开始解析飞行记录并聚合到H3网格（分辨率{resolution}）")
        df, h3_df = parser.parse_and_aggregate_to_h3(
            json_file_path, resolution, output_raw_csv, output_h3_csv
        )
        
        if len(df) > 0:
            logger.info("✅ 解析和H3聚合完成！")
            logger.info(f"原始记录数: {len(df)}")
            logger.info(f"H3网格数: {len(h3_df)}")
            
            if len(h3_df) > 0:
                logger.info(f"平均每个网格点数: {h3_df['point_count'].mean():.1f}")
                # 网格面积信息已移除
                logger.info(f"平均SDR信号: {h3_df['avg_sdr_signal'].mean():.2f}")
            
            if output_raw_csv:
                logger.info(f"原始数据已保存到: {output_raw_csv}")
            if output_h3_csv:
                logger.info(f"H3聚合数据已保存到: {output_h3_csv}")
        else:
            logger.warning("⚠️ 解析完成，但没有找到有效数据")
            
    except Exception as e:
        logger.error(f"❌ 解析和H3聚合失败: {str(e)}")
        raise



def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='飞行记录解析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 解析飞行记录文件
  python main.py --input data/flight_replay_8UUDMAQ00A0202
  
  # 解析飞行记录文件并指定输出文件
  python main.py --input data/flight_replay_8UUDMAQ00A0202 --output my_flight_data.csv
  
  # 解析飞行记录并聚合到H3网格（分辨率13）
  python main.py --input data/flight_replay_8UUDMAQ00A0202 --h3 --resolution 13
  
  # 解析飞行记录并聚合到H3网格，指定输出文件
  python main.py --input data/flight_replay_8UUDMAQ00A0202 --h3 --resolution 13 --output-raw raw_data.csv --output-h3 h3_data.csv
        """
    )
    
    parser.add_argument('--input', type=str,
                       help='输入飞行记录JSON文件路径')
    
    parser.add_argument('--output', type=str,
                       help='输出CSV文件路径（仅解析模式）')
    
    parser.add_argument('--h3', action='store_true',
                       help='启用H3网格聚合功能')
    
    parser.add_argument('--resolution', type=int, default=13,
                       help='H3分辨率级别（0-15，默认13）')
    
    parser.add_argument('--output-raw', type=str,
                       help='原始数据输出CSV文件路径（H3模式）')
    
    parser.add_argument('--output-h3', type=str,
                       help='H3聚合数据输出CSV文件路径（H3模式）')
    

    
    args = parser.parse_args()
    
    try:
        # 检查输入文件是否存在
        if args.input and not Path(args.input).exists():
            logger.error(f"输入文件不存在: {args.input}")
            sys.exit(1)
        

        
        # 检查H3分辨率范围
        if args.h3 and (args.resolution < 0 or args.resolution > 15):
            logger.error(f"H3分辨率必须在0-15之间，当前值: {args.resolution}")
            sys.exit(1)
        
        # 执行相应的功能
        if args.h3:
            # H3聚合模式
            parse_and_aggregate_to_h3(
                args.input, 
                args.resolution, 
                args.output_raw, 
                args.output_h3
            )
        elif args.input:
            # 仅解析模式
            parse_flight_record(args.input, args.output)
        else:
            # 显示帮助信息
            parser.print_help()
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
