import pandas as pd
import json
import logging
import h3

class FlightRecordParser:
    """飞行记录解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_flight_record_json(self, json_file_path: str, output_csv_path: str = None) -> pd.DataFrame:
        """
        解析真实飞行记录JSON文件
        
        Args:
            json_file_path: JSON文件路径
            output_csv_path: 输出CSV文件路径，如果为None则自动生成
            
        Returns:
            解析后的DataFrame，包含时间戳、经纬度、信号数据
        """
        try:
            self.logger.info(f"开始解析飞行记录文件: {json_file_path}")
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                flight_data = json.load(f)
            
            # 解析机场位置（只取第一次，用于日志显示）
            airport_lat = None
            airport_lon = None
            
            # 解析飞行数据
            flight_records = []
            current_sdr_quality = None  # 保存当前的SDR信号质量
            
            # 检查是否有frameState数组
            if 'frameState' not in flight_data:
                self.logger.error("未找到frameState数据")
                return pd.DataFrame()
            
            frame_states = flight_data['frameState']
            
            for frame_state in frame_states:
                # 解析机场位置（只取第一次，用于日志显示）
                if airport_lat is None and 'dock' in frame_state:
                    dock = frame_state['dock']
                    if isinstance(dock, list) and len(dock) > 0:
                        dock_info = dock[0]
                        if 'latitude' in dock_info and 'longitude' in dock_info:
                            airport_lat = dock_info['latitude']
                            airport_lon = dock_info['longitude']
                            self.logger.info(f"解析到机场位置: ({airport_lat}, {airport_lon})")
                
                # 解析飞行数据
                if 'uav' in frame_state:
                    uav = frame_state['uav']
                    if isinstance(uav, list) and len(uav) > 0:
                        uav_info = uav[0]
                        
                        # 解析信号数据
                        if 'wireless_link' in uav_info:
                            wireless_link = uav_info['wireless_link']
                            if isinstance(wireless_link, list) and len(wireless_link) > 0:
                                wireless_info = wireless_link[0]
                                if 'sdr_quality' in wireless_info:
                                    # 更新SDR信号质量（只在变化时更新）
                                    new_sdr_quality = wireless_info['sdr_quality']
                                    if new_sdr_quality != current_sdr_quality:
                                        current_sdr_quality = new_sdr_quality
                        
                        # 解析经纬度
                        if 'fc' in uav_info:
                            fc = uav_info['fc']
                            if isinstance(fc, list) and len(fc) > 0:
                                fc_info = fc[0]
                                
                                # 检查是否有location字段（包含经纬度）
                                if 'location' in fc_info:
                                    location = fc_info['location']
                                    if 'latitude' in location and 'longitude' in location:
                                        lat = location['latitude']
                                        lon = location['longitude']
                                        
                                        # 记录数据（不包含机场位置）
                                        record = {
                                            'timestamp': frame_state.get('time', ''),
                                            'latitude': lat,
                                            'longitude': lon,
                                            'sdr_signal': current_sdr_quality
                                        }
                                        flight_records.append(record)
            
            # 创建DataFrame
            df = pd.DataFrame(flight_records)
            
            # 处理时间戳
            if 'timestamp' in df.columns and len(df) > 0:
                # 将时间戳从毫秒转换为datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 保存到CSV文件
            if output_csv_path is None:
                output_csv_path = 'parsed_flight_data.csv'
            
            df.to_csv(output_csv_path, index=False, encoding='utf-8')
            
            self.logger.info(f"解析完成，共解析 {len(df)} 条记录")
            self.logger.info(f"数据已保存到: {output_csv_path}")
            
            # 显示数据统计
            if len(df) > 0:
                self.logger.info(f"数据统计:")
                self.logger.info(f"  时间范围: {df['timestamp'].min()} - {df['timestamp'].max()}")
                self.logger.info(f"  纬度范围: {df['latitude'].min():.6f} - {df['latitude'].max():.6f}")
                self.logger.info(f"  经度范围: {df['longitude'].min():.6f} - {df['longitude'].max():.6f}")
                if 'sdr_signal' in df.columns:
                    sdr_data = df['sdr_signal'].dropna()
                    if len(sdr_data) > 0:
                        self.logger.info(f"  SDR信号范围: {sdr_data.min():.1f} - {sdr_data.max():.1f}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"解析飞行记录JSON文件失败: {str(e)}")
            raise
    
    def aggregate_to_h3(self, df: pd.DataFrame, resolution: int = 13, output_csv_path: str = None) -> pd.DataFrame:
        """
        将飞行轨迹点聚合到H3网格中
        
        Args:
            df: 包含飞行数据的DataFrame
            resolution: H3分辨率级别（0-15）
            output_csv_path: 输出CSV文件路径，如果为None则自动生成
            
        Returns:
            聚合后的DataFrame，包含H3网格统计信息
        """
        try:
            self.logger.info(f"开始将数据聚合到H3网格（分辨率{resolution}）")
            
            # 添加H3索引列
            df['h3_index'] = df.apply(
                lambda row: h3.latlng_to_cell(row['latitude'], row['longitude'], resolution), 
                axis=1
            )
            
            # 聚合数据
            h3_aggregated = df.groupby('h3_index').agg({
                'timestamp': ['count'],  # 只保留计数，不保留时间戳
                'sdr_signal': ['mean', 'max', 'min']  # 排除标准差
            }).reset_index()
            
            # 重命名列
            h3_aggregated.columns = [
                'h3_index',
                'point_count',
                'avg_sdr_signal',
                'max_sdr_signal',
                'min_sdr_signal'
            ]
            
            # 添加H3网格边界（GeoJSON格式）
            h3_aggregated['h3_boundary'] = h3_aggregated['h3_index'].apply(
                lambda x: h3.cell_to_boundary(x)
            )
            
            # 保存到CSV文件
            if output_csv_path is None:
                output_csv_path = f'h3_aggregated_res{resolution}.csv'
            
            # 保存主要数据（不包含边界信息）
            h3_aggregated_simple = h3_aggregated.drop('h3_boundary', axis=1)
            h3_aggregated_simple.to_csv(output_csv_path, index=False, encoding='utf-8')
            
            self.logger.info(f"H3聚合完成，共生成 {len(h3_aggregated)} 个网格")
            self.logger.info(f"数据已保存到: {output_csv_path}")
            
            # 显示统计信息
            if len(h3_aggregated) > 0:
                self.logger.info(f"H3聚合统计:")
                self.logger.info(f"  网格数量: {len(h3_aggregated)}")
                self.logger.info(f"  平均每个网格点数: {h3_aggregated['point_count'].mean():.1f}")
                self.logger.info(f"  最大网格点数: {h3_aggregated['point_count'].max()}")
                self.logger.info(f"  最小网格点数: {h3_aggregated['point_count'].min()}")
                self.logger.info(f"  平均SDR信号: {h3_aggregated['avg_sdr_signal'].mean():.2f}")
                self.logger.info(f"  SDR信号范围: {h3_aggregated['avg_sdr_signal'].min():.1f} - {h3_aggregated['avg_sdr_signal'].max():.1f}")
            
            return h3_aggregated
            
        except Exception as e:
            self.logger.error(f"H3聚合失败: {str(e)}")
            raise
    
    def parse_and_aggregate_to_h3(self, json_file_path: str, resolution: int = 13, 
                                 output_raw_csv: str = None, output_h3_csv: str = None) -> tuple:
        """
        解析飞行记录并聚合到H3网格
        
        Args:
            json_file_path: JSON文件路径
            resolution: H3分辨率级别（0-15）
            output_raw_csv: 原始数据输出CSV文件路径
            output_h3_csv: H3聚合数据输出CSV文件路径
            
        Returns:
            (原始DataFrame, H3聚合DataFrame)
        """
        try:
            # 解析飞行记录
            df = self.parse_flight_record_json(json_file_path, output_raw_csv)
            
            if len(df) == 0:
                self.logger.warning("没有解析到有效数据，跳过H3聚合")
                return df, pd.DataFrame()
            
            # 聚合到H3网格
            h3_df = self.aggregate_to_h3(df, resolution, output_h3_csv)
            
            return df, h3_df
            
        except Exception as e:
            self.logger.error(f"解析并聚合失败: {str(e)}")
            raise
