import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import json
from datetime import datetime
import logging
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import math

class DroneSignalProcessor:
    """无人机信号数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_flight_data(self, file_path: str) -> pd.DataFrame:
        """
        加载无人机飞行数据
        
        Args:
            file_path: 数据文件路径 (支持CSV, JSON格式)
            
        Returns:
            包含飞行数据的DataFrame
        """
        try:
            if file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                data = pd.read_json(file_path)
            else:
                raise ValueError("不支持的文件格式，请使用CSV或JSON格式")
                
            # 验证必要的数据列
            required_columns = ['timestamp', 'latitude', 'longitude', 'altitude']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                raise ValueError(f"缺少必要的数据列: {missing_columns}")
                
            self.logger.info(f"成功加载飞行数据，共{len(data)}条记录")
            return data
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {str(e)}")
            raise
    
    def load_signal_data(self, file_path: str) -> pd.DataFrame:
        """
        加载信号质量数据
        
        Args:
            file_path: 信号数据文件路径
            
        Returns:
            包含信号数据的DataFrame
        """
        try:
            if file_path.endswith('.csv'):
                signal_data = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                signal_data = pd.read_json(file_path)
            else:
                raise ValueError("不支持的文件格式，请使用CSV或JSON格式")
                
            # 验证信号数据列
            signal_columns = ['timestamp', '4g_signal', 'sdr_signal']
            missing_columns = [col for col in signal_columns if col not in signal_data.columns]
            
            if missing_columns:
                raise ValueError(f"缺少信号数据列: {missing_columns}")
                
            self.logger.info(f"成功加载信号数据，共{len(signal_data)}条记录")
            return signal_data
            
        except Exception as e:
            self.logger.error(f"加载信号数据失败: {str(e)}")
            raise
    
    def merge_flight_and_signal_data(self, flight_data: pd.DataFrame, signal_data: pd.DataFrame) -> pd.DataFrame:
        """
        合并飞行数据和信号数据
        
        Args:
            flight_data: 飞行轨迹数据
            signal_data: 信号质量数据
            
        Returns:
            合并后的完整数据集
        """
        try:
            # 确保时间戳格式一致
            flight_data['timestamp'] = pd.to_datetime(flight_data['timestamp'])
            signal_data['timestamp'] = pd.to_datetime(signal_data['timestamp'])
            
            # 基于时间戳合并数据
            merged_data = pd.merge_asof(
                flight_data.sort_values('timestamp'),
                signal_data.sort_values('timestamp'),
                on='timestamp',
                direction='nearest',
                tolerance=pd.Timedelta(seconds=5)  # 5秒容差
            )
            
            # 清理缺失值
            merged_data = merged_data.dropna(subset=['latitude', 'longitude'])
            
            self.logger.info(f"成功合并数据，共{len(merged_data)}条有效记录")
            return merged_data
            
        except Exception as e:
            self.logger.error(f"合并数据失败: {str(e)}")
            raise
    
    def filter_data_by_area(self, data: pd.DataFrame, center_lat: float, center_lon: float, 
                           radius_km: float = 10.0) -> pd.DataFrame:
        """
        根据指定区域过滤数据
        
        Args:
            data: 输入数据
            center_lat: 中心点纬度
            center_lon: 中心点经度
            radius_km: 半径（公里）
            
        Returns:
            过滤后的数据
        """
        try:
            from geopy.distance import geodesic
            
            def distance_from_center(row):
                point = (row['latitude'], row['longitude'])
                center = (center_lat, center_lon)
                return geodesic(center, point).kilometers
            
            # 计算每个点到中心的距离
            data['distance_from_center'] = data.apply(distance_from_center, axis=1)
            
            # 过滤在指定半径内的数据
            filtered_data = data[data['distance_from_center'] <= radius_km].copy()
            filtered_data = filtered_data.drop('distance_from_center', axis=1)
            
            self.logger.info(f"区域过滤完成，保留{len(filtered_data)}条记录")
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"区域过滤失败: {str(e)}")
            raise
    
    def create_hexagonal_grid(self, center_lat: float, center_lon: float, 
                             radius_km: float, hex_size_km: float) -> List[Dict]:
        """
        创建正六边形网格
        
        Args:
            center_lat: 中心点纬度
            center_lon: 中心点经度
            radius_km: 分析半径（公里）
            hex_size_km: 正六边形边长（公里）
            
        Returns:
            正六边形网格列表，每个元素包含网格信息和统计结果
        """
        try:
            # 正六边形的外接圆半径 = 边长
            hex_radius = hex_size_km
            
            # 计算网格层数
            max_layers = int(radius_km / hex_radius) + 1
            
            hexagons = []
            
            # 创建中心六边形
            hexagons.append(self._create_hexagon(center_lat, center_lon, hex_radius, 0))
            
            # 创建外围六边形层
            for layer in range(1, max_layers):
                # 计算当前层的半径（从中心到六边形中心的距离）
                # 对于正六边形网格，相邻层的距离是 sqrt(3) * hex_radius
                layer_radius = layer * hex_radius * math.sqrt(3)
                
                # 每层有 6 * layer 个六边形
                hexagons_in_layer = 6 * layer
                
                for i in range(hexagons_in_layer):
                    # 计算角度，确保六边形正确排列
                    angle = (2 * math.pi * i) / hexagons_in_layer
                    
                    # 计算六边形中心位置
                    # 使用大圆距离计算偏移
                    lat_offset = (layer_radius * math.cos(angle)) / 111.0  # 转换为度
                    lon_offset = (layer_radius * math.sin(angle)) / (111.0 * np.cos(np.radians(center_lat)))  # 转换为度
                    
                    hex_center_lat = center_lat + lat_offset
                    hex_center_lon = center_lon + lon_offset
                    
                    # 计算到中心的距离
                    distance = math.sqrt(lat_offset**2 + lon_offset**2) * 111.0  # 转换为公里
                    
                    if distance <= radius_km:
                        # 创建六边形
                        hexagon = self._create_hexagon(hex_center_lat, hex_center_lon, hex_radius, layer)
                        hexagons.append(hexagon)
            
            self.logger.info(f"创建正六边形网格完成，共{len(hexagons)}个网格")
            return hexagons
            
        except Exception as e:
            self.logger.error(f"创建正六边形网格失败: {str(e)}")
            raise
    
    def _create_hexagon(self, center_lat: float, center_lon: float, 
                       radius_km: float, layer: int) -> Dict:
        """
        创建单个正六边形
        
        Args:
            center_lat: 六边形中心纬度
            center_lon: 六边形中心经度
            radius_km: 六边形边长（公里）
            layer: 网格层数
            
        Returns:
            六边形信息字典
        """
        # 计算六边形的六个顶点
        vertices = []
        for i in range(6):
            angle = (2 * math.pi * i) / 6
            
            # 计算顶点位置
            lat_offset = (radius_km * math.cos(angle)) / 111.0  # 转换为度
            lon_offset = (radius_km * math.sin(angle)) / (111.0 * math.cos(math.radians(center_lat)))  # 转换为度
            
            vertex_lat = center_lat + lat_offset
            vertex_lon = center_lon + lon_offset
            vertices.append((vertex_lon, vertex_lat))  # shapely使用(经度,纬度)顺序
        
        # 创建shapely多边形
        hexagon_polygon = Polygon(vertices)
        
        return {
            'id': f"hex_{layer}_{len(vertices)}",
            'center_lat': center_lat,
            'center_lon': center_lon,
            'radius_km': radius_km,
            'layer': layer,
            'polygon': hexagon_polygon,
            'vertices': vertices,
            'data_count': 0,
            '4g_signal_mean': None,
            '4g_signal_max': None,
            '4g_signal_min': None,
            'sdr_signal_mean': None,
            'sdr_signal_max': None,
            'sdr_signal_min': None
        }
    
    def assign_data_to_hexagons(self, data: pd.DataFrame, hexagons: List[Dict]) -> List[Dict]:
        """
        将数据点分配到正六边形网格中
        
        Args:
            data: 无人机数据
            hexagons: 正六边形网格列表
            
        Returns:
            包含统计信息的六边形网格列表
        """
        try:
            # 创建数据点的几何对象
            data_points = []
            for _, row in data.iterrows():
                point = Point(row['longitude'], row['latitude'])  # shapely使用(经度,纬度)
                data_points.append({
                    'point': point,
                    'row': row
                })
            
            # 为每个六边形分配数据点
            for hexagon in hexagons:
                hex_polygon = hexagon['polygon']
                hex_data = []
                
                # 检查哪些数据点在当前六边形内
                for data_point in data_points:
                    if hex_polygon.contains(data_point['point']):
                        hex_data.append(data_point['row'])
                
                # 更新六边形统计信息
                hexagon['data_count'] = len(hex_data)
                
                if len(hex_data) > 0:
                    # 计算4G信号统计
                    if '4g_signal' in data.columns:
                        hex_4g_signals = [row['4g_signal'] for row in hex_data if pd.notna(row['4g_signal'])]
                        if hex_4g_signals:
                            hexagon['4g_signal_mean'] = np.mean(hex_4g_signals)
                            hexagon['4g_signal_max'] = np.max(hex_4g_signals)
                            hexagon['4g_signal_min'] = np.min(hex_4g_signals)
                    
                    # 计算SDR信号统计
                    if 'sdr_signal' in data.columns:
                        hex_sdr_signals = [row['sdr_signal'] for row in hex_data if pd.notna(row['sdr_signal'])]
                        if hex_sdr_signals:
                            hexagon['sdr_signal_mean'] = np.mean(hex_sdr_signals)
                            hexagon['sdr_signal_max'] = np.max(hex_sdr_signals)
                            hexagon['sdr_signal_min'] = np.min(hex_sdr_signals)
            
            # 统计信息
            total_hexagons = len(hexagons)
            hexagons_with_data = sum(1 for h in hexagons if h['data_count'] > 0)
            
            self.logger.info(f"数据分配到网格完成:")
            self.logger.info(f"  总网格数: {total_hexagons}")
            self.logger.info(f"  有数据的网格数: {hexagons_with_data}")
            self.logger.info(f"  数据覆盖率: {hexagons_with_data/total_hexagons*100:.1f}%")
            
            return hexagons
            
        except Exception as e:
            self.logger.error(f"数据分配到网格失败: {str(e)}")
            raise
    
    def process_data_with_hexagonal_grid(self, data: pd.DataFrame, center_lat: float, 
                                       center_lon: float, radius_km: float = 10.0, 
                                       hex_size_km: float = 1.0) -> List[Dict]:
        """
        使用正六边形网格处理数据
        
        Args:
            data: 无人机数据
            center_lat: 机场中心纬度
            center_lon: 机场中心经度
            radius_km: 分析半径（公里）
            hex_size_km: 正六边形边长（公里）
            
        Returns:
            包含统计信息的六边形网格列表
        """
        try:
            # 1. 区域过滤
            filtered_data = self.filter_data_by_area(data, center_lat, center_lon, radius_km)
            
            # 2. 创建正六边形网格
            hexagons = self.create_hexagonal_grid(center_lat, center_lon, radius_km, hex_size_km)
            
            # 3. 将数据分配到网格
            hexagons_with_stats = self.assign_data_to_hexagons(filtered_data, hexagons)
            
            return hexagons_with_stats
            
        except Exception as e:
            self.logger.error(f"正六边形网格数据处理失败: {str(e)}")
            raise
    
    def export_hexagonal_grid_data(self, hexagons: List[Dict], output_file: str) -> None:
        """
        导出正六边形网格数据为CSV文件
        
        Args:
            hexagons: 六边形网格列表
            output_file: 输出文件路径
        """
        try:
            # 准备导出数据
            export_data = []
            for hexagon in hexagons:
                export_row = {
                    'hex_id': hexagon['id'],
                    'center_lat': hexagon['center_lat'],
                    'center_lon': hexagon['center_lon'],
                    'radius_km': hexagon['radius_km'],
                    'layer': hexagon['layer'],
                    'data_count': hexagon['data_count'],
                    '4g_signal_mean': hexagon['4g_signal_mean'],
                    '4g_signal_max': hexagon['4g_signal_max'],
                    '4g_signal_min': hexagon['4g_signal_min'],
                    'sdr_signal_mean': hexagon['sdr_signal_mean'],
                    'sdr_signal_max': hexagon['sdr_signal_max'],
                    'sdr_signal_min': hexagon['sdr_signal_min']
                }
                export_data.append(export_row)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(export_data)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            self.logger.info(f"正六边形网格数据已导出到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"导出正六边形网格数据失败: {str(e)}")
            raise
    
    def normalize_signal_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        标准化信号数据
        
        Args:
            data: 包含信号数据的DataFrame
            
        Returns:
            标准化后的数据
        """
        try:
            # 复制数据避免修改原始数据
            normalized_data = data.copy()
            
            # 标准化4G信号强度 (假设范围是-120到-50 dBm)
            if '4g_signal' in normalized_data.columns:
                normalized_data['4g_signal_normalized'] = (
                    (normalized_data['4g_signal'] + 120) / 70 * 100
                ).clip(0, 100)
            
            # 标准化SDR信号强度 (假设范围是0到100)
            if 'sdr_signal' in normalized_data.columns:
                normalized_data['sdr_signal_normalized'] = normalized_data['sdr_signal'].clip(0, 100)
            
            self.logger.info("信号数据标准化完成")
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"信号数据标准化失败: {str(e)}")
            raise
    
    def generate_sample_data(self, center_lat: float = 39.9042, center_lon: float = 116.4074, 
                           num_points: int = 1000, radius_km: float = 2.0, 
                           concentration_factor: float = 0.7) -> pd.DataFrame:
        """
        生成示例数据用于测试
        
        Args:
            center_lat: 中心点纬度
            center_lon: 中心点经度
            num_points: 数据点数量
            radius_km: 数据分布半径（公里）
            concentration_factor: 集中度因子（0-1），越大越集中在中心
            
        Returns:
            生成的示例数据
        """
        try:
            np.random.seed(42)
            
            # 生成随机飞行轨迹，使用更集中的分布
            angles = np.random.uniform(0, 2*np.pi, num_points)
            
            # 使用Beta分布来创建更集中的距离分布
            # concentration_factor越大，数据点越集中在中心
            beta_a = 2.0
            beta_b = 2.0 / concentration_factor - 2.0
            distances = np.random.beta(beta_a, beta_b, num_points) * radius_km
            
            # 转换为经纬度偏移
            lat_offset = distances * np.cos(angles) / 111.0  # 1度纬度约等于111公里
            lon_offset = distances * np.sin(angles) / (111.0 * np.cos(np.radians(center_lat)))
            
            latitudes = center_lat + lat_offset
            longitudes = center_lon + lon_offset
            altitudes = np.random.uniform(50, 200, num_points)
            
            # 生成时间戳
            start_time = datetime.now()
            timestamps = [start_time + pd.Timedelta(seconds=i*2) for i in range(num_points)]
            
            # 生成信号数据（模拟真实情况）
            # 4G信号强度随距离衰减
            distances_from_center = np.sqrt(lat_offset**2 + lon_offset**2) * 111.0
            base_4g_signal = -70 - distances_from_center * 2 + np.random.normal(0, 5, num_points)
            base_4g_signal = np.clip(base_4g_signal, -120, -50)
            
            # SDR信号质量
            base_sdr_signal = 80 - distances_from_center * 3 + np.random.normal(0, 10, num_points)
            base_sdr_signal = np.clip(base_sdr_signal, 0, 100)
            
            # 创建DataFrame
            sample_data = pd.DataFrame({
                'timestamp': timestamps,
                'latitude': latitudes,
                'longitude': longitudes,
                'altitude': altitudes,
                '4g_signal': base_4g_signal,
                'sdr_signal': base_sdr_signal
            })
            
            self.logger.info(f"生成示例数据完成，共{len(sample_data)}条记录")
            return sample_data
            
        except Exception as e:
            self.logger.error(f"生成示例数据失败: {str(e)}")
            raise
    
    def create_square_grid(self, center_lat: float, center_lon: float, 
                          radius_km: float, square_size_km: float) -> List[Dict]:
        """
        创建正方形网格
        
        Args:
            center_lat: 中心点纬度
            center_lon: 中心点经度
            radius_km: 分析半径（公里）
            square_size_km: 正方形边长（公里）
            
        Returns:
            正方形网格列表
        """
        try:
            # 计算网格数量
            grid_radius = int(radius_km / square_size_km)
            
            squares = []
            
            # 创建正方形网格
            for i in range(-grid_radius, grid_radius + 1):
                for j in range(-grid_radius, grid_radius + 1):
                    # 计算正方形中心位置
                    lat_offset = i * square_size_km / 111.0
                    lon_offset = j * square_size_km / (111.0 * math.cos(math.radians(center_lat)))
                    
                    square_center_lat = center_lat + lat_offset
                    square_center_lon = center_lon + lon_offset
                    
                    # 计算到中心的距离
                    distance = math.sqrt(lat_offset**2 + lon_offset**2) * 111.0
                    
                    if distance <= radius_km:
                        # 创建正方形
                        square = self._create_square(square_center_lat, square_center_lon, square_size_km, i, j)
                        squares.append(square)
            
            self.logger.info(f"创建正方形网格完成，共{len(squares)}个网格")
            return squares
            
        except Exception as e:
            self.logger.error(f"创建正方形网格失败: {str(e)}")
            raise
    
    def _create_square(self, center_lat: float, center_lon: float, 
                      size_km: float, grid_i: int, grid_j: int) -> Dict:
        """
        创建单个正方形
        
        Args:
            center_lat: 正方形中心纬度
            center_lon: 正方形中心经度
            size_km: 正方形边长（公里）
            grid_i: 网格行索引
            grid_j: 网格列索引
            
        Returns:
            正方形信息字典
        """
        # 计算正方形的四个顶点
        half_size = size_km / 2
        
        # 转换为经纬度偏移
        lat_offset = half_size / 111.0
        lon_offset = half_size / (111.0 * math.cos(math.radians(center_lat)))
        
        # 四个顶点坐标
        vertices = [
            (center_lon - lon_offset, center_lat - lat_offset),  # 左下
            (center_lon + lon_offset, center_lat - lat_offset),  # 右下
            (center_lon + lon_offset, center_lat + lat_offset),  # 右上
            (center_lon - lon_offset, center_lat + lat_offset)   # 左上
        ]
        
        # 创建shapely多边形
        square_polygon = Polygon(vertices)
        
        return {
            'id': f"square_{grid_i}_{grid_j}",
            'center_lat': center_lat,
            'center_lon': center_lon,
            'size_km': size_km,
            'grid_i': grid_i,
            'grid_j': grid_j,
            'polygon': square_polygon,
            'vertices': vertices,
            'data_count': 0,
            '4g_signal_mean': None,
            '4g_signal_max': None,
            '4g_signal_min': None,
            'sdr_signal_mean': None,
            'sdr_signal_max': None,
            'sdr_signal_min': None
        }
    
    def assign_data_to_squares_fast(self, data: pd.DataFrame, squares: List[Dict]) -> List[Dict]:
        """
        快速将数据点分配到正方形网格中（优化版本）
        
        Args:
            data: 无人机数据
            squares: 正方形网格列表
            
        Returns:
            包含统计信息的正方形网格列表
        """
        try:
            # 创建数据点的几何对象
            data_points = []
            for _, row in data.iterrows():
                point = Point(row['longitude'], row['latitude'])
                data_points.append({
                    'point': point,
                    'row': row
                })
            
            # 使用空间索引优化查询
            from shapely.strtree import STRtree
            
            # 创建空间索引
            square_polygons = [s['polygon'] for s in squares]
            tree = STRtree(square_polygons)
            
            # 为每个数据点找到包含它的正方形
            for data_point in data_points:
                point = data_point['point']
                # 使用空间索引快速找到候选正方形
                candidates = tree.query(point)
                
                for idx in candidates:
                    if square_polygons[idx].contains(point):
                        # 将数据点添加到对应的正方形
                        if 'data' not in squares[idx]:
                            squares[idx]['data'] = []
                        squares[idx]['data'].append(data_point['row'])
                        break  # 一个点只会被一个正方形包含
            
            # 计算每个正方形的统计信息
            for square in squares:
                if 'data' in square:
                    square_data = square['data']
                    square['data_count'] = len(square_data)
                    
                    if len(square_data) > 0:
                        # 计算4G信号统计
                        if '4g_signal' in data.columns:
                            square_4g_signals = [row['4g_signal'] for row in square_data if pd.notna(row['4g_signal'])]
                            if square_4g_signals:
                                square['4g_signal_mean'] = np.mean(square_4g_signals)
                                square['4g_signal_max'] = np.max(square_4g_signals)
                                square['4g_signal_min'] = np.min(square_4g_signals)
                        
                        # 计算SDR信号统计
                        if 'sdr_signal' in data.columns:
                            square_sdr_signals = [row['sdr_signal'] for row in square_data if pd.notna(row['sdr_signal'])]
                            if square_sdr_signals:
                                square['sdr_signal_mean'] = np.mean(square_sdr_signals)
                                square['sdr_signal_max'] = np.max(square_sdr_signals)
                                square['sdr_signal_min'] = np.min(square_sdr_signals)
                    
                    # 清理临时数据
                    del square['data']
                else:
                    square['data_count'] = 0
            
            # 统计信息
            total_squares = len(squares)
            squares_with_data = sum(1 for s in squares if s['data_count'] > 0)
            
            self.logger.info(f"数据分配到正方形网格完成:")
            self.logger.info(f"  总网格数: {total_squares}")
            self.logger.info(f"  有数据的网格数: {squares_with_data}")
            self.logger.info(f"  数据覆盖率: {squares_with_data/total_squares*100:.1f}%")
            
            return squares
            
        except Exception as e:
            self.logger.error(f"数据分配到正方形网格失败: {str(e)}")
            raise
    
    def process_data_with_square_grid(self, data: pd.DataFrame, center_lat: float, 
                                    center_lon: float, radius_km: float = 10.0, 
                                    square_size_km: float = 1.0) -> List[Dict]:
        """
        使用正方形网格处理数据
        
        Args:
            data: 无人机数据
            center_lat: 机场中心纬度
            center_lon: 机场中心经度
            radius_km: 分析半径（公里）
            square_size_km: 正方形边长（公里）
            
        Returns:
            包含统计信息的正方形网格列表
        """
        try:
            # 1. 区域过滤
            filtered_data = self.filter_data_by_area(data, center_lat, center_lon, radius_km)
            
            # 2. 创建正方形网格
            squares = self.create_square_grid(center_lat, center_lon, radius_km, square_size_km)
            
            # 3. 将数据分配到网格（使用优化版本）
            squares_with_stats = self.assign_data_to_squares_fast(filtered_data, squares)
            
            return squares_with_stats
            
        except Exception as e:
            self.logger.error(f"正方形网格数据处理失败: {str(e)}")
            raise
    
    def export_square_grid_data(self, squares: List[Dict], output_file: str) -> None:
        """
        导出正方形网格数据为CSV文件
        
        Args:
            squares: 正方形网格列表
            output_file: 输出文件路径
        """
        try:
            # 准备导出数据
            export_data = []
            for square in squares:
                export_row = {
                    'square_id': square['id'],
                    'center_lat': square['center_lat'],
                    'center_lon': square['center_lon'],
                    'size_km': square['size_km'],
                    'grid_i': square['grid_i'],
                    'grid_j': square['grid_j'],
                    'data_count': square['data_count'],
                    '4g_signal_mean': square['4g_signal_mean'],
                    '4g_signal_max': square['4g_signal_max'],
                    '4g_signal_min': square['4g_signal_min'],
                    'sdr_signal_mean': square['sdr_signal_mean'],
                    'sdr_signal_max': square['sdr_signal_max'],
                    'sdr_signal_min': square['sdr_signal_min']
                }
                export_data.append(export_row)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(export_data)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            self.logger.info(f"正方形网格数据已导出到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"导出正方形网格数据失败: {str(e)}")
            raise
