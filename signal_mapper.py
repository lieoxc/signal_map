import pandas as pd
import numpy as np
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import griddata
from typing import Tuple, Optional, List, Dict
import logging
import os

class SignalMapper:
    """信号地图绘制器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文显示
        plt.rcParams['axes.unicode_minus'] = False
        
    def create_hexagonal_grid_map(self, hexagons: List[Dict], signal_type: str = '4g_signal_mean',
                                 center_lat: Optional[float] = None, 
                                 center_lon: Optional[float] = None,
                                 zoom: int = 13) -> folium.Map:
        """
        创建正六边形网格信号地图
        
        Args:
            hexagons: 正六边形网格数据
            signal_type: 信号类型 ('4g_signal_mean', '4g_signal_max', '4g_signal_min', 
                                  'sdr_signal_mean', 'sdr_signal_max', 'sdr_signal_min')
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom: 地图缩放级别
            
        Returns:
            Folium地图对象
        """
        try:
            # 确定地图中心点
            if center_lat is None or center_lon is None:
                center_lat = np.mean([h['center_lat'] for h in hexagons])
                center_lon = np.mean([h['center_lon'] for h in hexagons])
            
            # 创建基础地图
            hex_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # 获取信号值范围
            signal_values = []
            for hexagon in hexagons:
                if hexagon[signal_type] is not None:
                    signal_values.append(hexagon[signal_type])
            
            if not signal_values:
                self.logger.warning(f"没有有效的{signal_type}数据")
                return hex_map
            
            min_signal = min(signal_values)
            max_signal = max(signal_values)
            
            # 添加六边形到地图
            for hexagon in hexagons:
                if hexagon['data_count'] > 0 and hexagon[signal_type] is not None:
                    # 计算颜色
                    if signal_type.startswith('4g_signal'):
                        color = self._get_4g_signal_color(hexagon[signal_type])
                    else:
                        color = self._get_sdr_signal_color(hexagon[signal_type])
                    
                    # 创建六边形多边形
                    hex_coords = [(lat, lon) for lon, lat in hexagon['vertices']]
                    
                    # 添加六边形到地图
                    folium.Polygon(
                        locations=hex_coords,
                        color=color,
                        weight=1,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        popup=self._create_hexagon_popup(hexagon, signal_type)
                    ).add_to(hex_map)
            
            # 添加图例
            self._add_hexagonal_legend(hex_map, signal_type, min_signal, max_signal)
            
            self.logger.info(f"成功创建正六边形网格{signal_type}信号地图")
            return hex_map
            
        except Exception as e:
            self.logger.error(f"创建正六边形网格地图失败: {str(e)}")
            raise
    
    def create_dual_hexagonal_grid_map(self, hexagons: List[Dict], 
                                      center_lat: Optional[float] = None,
                                      center_lon: Optional[float] = None,
                                      zoom: int = 13) -> folium.Map:
        """
        创建双信号正六边形网格对比地图
        
        Args:
            hexagons: 正六边形网格数据
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom: 地图缩放级别
            
        Returns:
            Folium地图对象
        """
        try:
            # 确定地图中心点
            if center_lat is None or center_lon is None:
                center_lat = np.mean([h['center_lat'] for h in hexagons])
                center_lon = np.mean([h['center_lon'] for h in hexagons])
            
            # 创建基础地图
            dual_hex_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # 创建图层控制
            folium.LayerControl().add_to(dual_hex_map)
            
            # 添加4G信号图层
            fg_4g = folium.FeatureGroup(name="4G信号强度")
            for hexagon in hexagons:
                if hexagon['data_count'] > 0 and hexagon['4g_signal_mean'] is not None:
                    color = self._get_4g_signal_color(hexagon['4g_signal_mean'])
                    hex_coords = [(lat, lon) for lon, lat in hexagon['vertices']]
                    
                    folium.Polygon(
                        locations=hex_coords,
                        color=color,
                        weight=1,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.6,
                        popup=self._create_hexagon_popup(hexagon, '4g_signal_mean')
                    ).add_to(fg_4g)
            fg_4g.add_to(dual_hex_map)
            
            # 添加SDR信号图层
            fg_sdr = folium.FeatureGroup(name="SDR信号质量")
            for hexagon in hexagons:
                if hexagon['data_count'] > 0 and hexagon['sdr_signal_mean'] is not None:
                    color = self._get_sdr_signal_color(hexagon['sdr_signal_mean'])
                    hex_coords = [(lat, lon) for lon, lat in hexagon['vertices']]
                    
                    folium.Polygon(
                        locations=hex_coords,
                        color=color,
                        weight=1,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.6,
                        popup=self._create_hexagon_popup(hexagon, 'sdr_signal_mean')
                    ).add_to(fg_sdr)
            fg_sdr.add_to(dual_hex_map)
            
            self.logger.info("成功创建双信号正六边形网格对比地图")
            return dual_hex_map
            
        except Exception as e:
            self.logger.error(f"创建双信号正六边形网格地图失败: {str(e)}")
            raise
    
    def create_square_grid_map(self, squares: List[Dict], signal_type: str = '4g_signal_mean',
                              center_lat: Optional[float] = None, 
                              center_lon: Optional[float] = None,
                              zoom: int = 13) -> folium.Map:
        """
        创建正方形网格信号地图
        
        Args:
            squares: 正方形网格数据
            signal_type: 信号类型 ('4g_signal_mean', '4g_signal_max', '4g_signal_min', 
                                  'sdr_signal_mean', 'sdr_signal_max', 'sdr_signal_min')
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom: 地图缩放级别
            
        Returns:
            Folium地图对象
        """
        try:
            # 确定地图中心点
            if center_lat is None or center_lon is None:
                center_lat = np.mean([s['center_lat'] for s in squares])
                center_lon = np.mean([s['center_lon'] for s in squares])
            
            # 创建基础地图
            square_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # 获取信号值范围
            signal_values = []
            for square in squares:
                if square[signal_type] is not None:
                    signal_values.append(square[signal_type])
            
            if not signal_values:
                self.logger.warning(f"没有有效的{signal_type}数据")
                return square_map
            
            min_signal = min(signal_values)
            max_signal = max(signal_values)
            
            # 添加正方形到地图
            for square in squares:
                if square['data_count'] > 0 and square[signal_type] is not None:
                    # 计算颜色
                    if signal_type.startswith('4g_signal'):
                        color = self._get_4g_signal_color(square[signal_type])
                    else:
                        color = self._get_sdr_signal_color(square[signal_type])
                    
                    # 创建正方形多边形
                    square_coords = [(lat, lon) for lon, lat in square['vertices']]
                    
                    # 添加正方形到地图
                    folium.Polygon(
                        locations=square_coords,
                        color=color,
                        weight=1,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        popup=self._create_square_popup(square, signal_type)
                    ).add_to(square_map)
            
            # 添加图例
            self._add_square_legend(square_map, signal_type, min_signal, max_signal)
            
            self.logger.info(f"成功创建正方形网格{signal_type}信号地图")
            return square_map
            
        except Exception as e:
            self.logger.error(f"创建正方形网格地图失败: {str(e)}")
            raise
    
    def _get_4g_signal_color(self, signal_value: float) -> str:
        """根据4G信号强度获取颜色"""
        if signal_value > -70:
            return 'red'      # 强信号
        elif signal_value > -85:
            return 'orange'   # 中等信号
        elif signal_value > -100:
            return 'yellow'   # 弱信号
        else:
            return 'blue'     # 很弱信号
    
    def _get_sdr_signal_color(self, signal_value: float) -> str:
        """根据SDR信号质量获取颜色"""
        if signal_value > 80:
            return 'green'    # 高质量
        elif signal_value > 60:
            return 'yellow'   # 中等质量
        elif signal_value > 40:
            return 'orange'   # 低质量
        else:
            return 'red'      # 很低质量
    
    def _create_hexagon_popup(self, hexagon: Dict, signal_type: str) -> str:
        """创建六边形弹窗信息"""
        popup_html = f"""
        <div style="width: 200px;">
            <h4>网格信息</h4>
            <p><b>网格ID:</b> {hexagon['id']}</p>
            <p><b>数据点数:</b> {hexagon['data_count']}</p>
            <p><b>网格层数:</b> {hexagon['layer']}</p>
            <hr>
            <h5>4G信号统计</h5>
            <p>平均值: {hexagon['4g_signal_mean']:.1f} dBm</p>
            <p>最大值: {hexagon['4g_signal_max']:.1f} dBm</p>
            <p>最小值: {hexagon['4g_signal_min']:.1f} dBm</p>
            <hr>
            <h5>SDR信号统计</h5>
            <p>平均值: {hexagon['sdr_signal_mean']:.1f}</p>
            <p>最大值: {hexagon['sdr_signal_max']:.1f}</p>
            <p>最小值: {hexagon['sdr_signal_min']:.1f}</p>
        </div>
        """
        return popup_html
    
    def _create_square_popup(self, square: Dict, signal_type: str) -> str:
        """创建正方形弹出信息"""
        try:
            popup_html = f"""
            <div style="width: 200px;">
                <h4>正方形网格 {square['id']}</h4>
                <p><b>中心位置:</b> {square['center_lat']:.6f}, {square['center_lon']:.6f}</p>
                <p><b>网格大小:</b> {square['size_km']:.3f} km</p>
                <p><b>数据点数量:</b> {square['data_count']}</p>
            """
            
            if square[signal_type] is not None:
                if signal_type.startswith('4g_signal'):
                    popup_html += f"<p><b>4G信号强度:</b> {square[signal_type]:.1f} dBm</p>"
                else:
                    popup_html += f"<p><b>SDR信号质量:</b> {square[signal_type]:.1f}</p>"
            
            popup_html += "</div>"
            return popup_html
            
        except Exception as e:
            return f"正方形网格 {square['id']}"
    
    def _add_hexagonal_legend(self, map_obj: folium.Map, signal_type: str, 
                            min_signal: float, max_signal: float) -> None:
        """添加正六边形地图图例"""
        try:
            if signal_type.startswith('4g_signal'):
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 180px; height: 120px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>4G信号强度 (dBm)</b></p>
                <p><i class="fa fa-square" style="color:red"></i> 强信号 (>-70)</p>
                <p><i class="fa fa-square" style="color:orange"></i> 中等信号 (-85~-70)</p>
                <p><i class="fa fa-square" style="color:yellow"></i> 弱信号 (-100~-85)</p>
                <p><i class="fa fa-square" style="color:blue"></i> 很弱信号 (<-100)</p>
                <p><b>范围:</b> {min_signal:.1f} ~ {max_signal:.1f}</p>
                </div>
                '''
            else:
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 180px; height: 120px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>SDR信号质量</b></p>
                <p><i class="fa fa-square" style="color:green"></i> 高质量 (>80)</p>
                <p><i class="fa fa-square" style="color:yellow"></i> 中等质量 (60~80)</p>
                <p><i class="fa fa-square" style="color:orange"></i> 低质量 (40~60)</p>
                <p><i class="fa fa-square" style="color:red"></i> 很低质量 (<40)</p>
                <p><b>范围:</b> {min_signal:.1f} ~ {max_signal:.1f}</p>
                </div>
                '''
            
            map_obj.get_root().html.add_child(folium.Element(legend_html))
            
        except Exception as e:
            self.logger.warning(f"添加正六边形图例失败: {str(e)}")
    
    def _add_square_legend(self, map_obj: folium.Map, signal_type: str, min_signal: float, max_signal: float) -> None:
        """添加正方形网格图例"""
        try:
            if signal_type.startswith('4g_signal'):
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 180px; height: 120px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>4G信号强度 (正方形网格)</b></p>
                <p><i class="fa fa-square" style="color:red"></i> 强信号 ({min_signal:.1f} dBm)</p>
                <p><i class="fa fa-square" style="color:yellow"></i> 中等信号 ({(min_signal+max_signal)/2:.1f} dBm)</p>
                <p><i class="fa fa-square" style="color:blue"></i> 弱信号 ({max_signal:.1f} dBm)</p>
                </div>
                '''
            else:
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 180px; height: 120px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>SDR信号质量 (正方形网格)</b></p>
                <p><i class="fa fa-square" style="color:white"></i> 高质量 ({max_signal:.1f})</p>
                <p><i class="fa fa-square" style="color:pink"></i> 中等质量 ({(min_signal+max_signal)/2:.1f})</p>
                <p><i class="fa fa-square" style="color:purple"></i> 低质量 ({min_signal:.1f})</p>
                </div>
                '''
            
            map_obj.get_root().html.add_child(folium.Element(legend_html))
            
        except Exception as e:
            self.logger.warning(f"添加正方形网格图例失败: {str(e)}")
    
    def create_hexagonal_grid_statistics_plot(self, hexagons: List[Dict], 
                                            output_path: str = 'hexagonal_grid_stats.png') -> None:
        """
        创建正六边形网格统计图表
        
        Args:
            hexagons: 正六边形网格数据
            output_path: 输出文件路径
        """
        try:
            # 过滤有数据的网格
            hexagons_with_data = [h for h in hexagons if h['data_count'] > 0]
            
            if len(hexagons_with_data) == 0:
                self.logger.warning("没有有数据的网格，无法生成统计图表")
                return
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            
            # 4G信号统计
            if any(h['4g_signal_mean'] is not None for h in hexagons_with_data):
                # 平均值分布
                means_4g = [h['4g_signal_mean'] for h in hexagons_with_data if h['4g_signal_mean'] is not None]
                axes[0, 0].hist(means_4g, bins=20, alpha=0.7, color='blue', edgecolor='black')
                axes[0, 0].set_xlabel('4G信号平均值 (dBm)')
                axes[0, 0].set_ylabel('网格数量')
                axes[0, 0].set_title('4G信号平均值分布')
                axes[0, 0].grid(True, alpha=0.3)
                
                # 最大值分布
                maxs_4g = [h['4g_signal_max'] for h in hexagons_with_data if h['4g_signal_max'] is not None]
                axes[0, 1].hist(maxs_4g, bins=20, alpha=0.7, color='red', edgecolor='black')
                axes[0, 1].set_xlabel('4G信号最大值 (dBm)')
                axes[0, 1].set_ylabel('网格数量')
                axes[0, 1].set_title('4G信号最大值分布')
                axes[0, 1].grid(True, alpha=0.3)
                
                # 最小值分布
                mins_4g = [h['4g_signal_min'] for h in hexagons_with_data if h['4g_signal_min'] is not None]
                axes[0, 2].hist(mins_4g, bins=20, alpha=0.7, color='green', edgecolor='black')
                axes[0, 2].set_xlabel('4G信号最小值 (dBm)')
                axes[0, 2].set_ylabel('网格数量')
                axes[0, 2].set_title('4G信号最小值分布')
                axes[0, 2].grid(True, alpha=0.3)
            
            # SDR信号统计
            if any(h['sdr_signal_mean'] is not None for h in hexagons_with_data):
                # 平均值分布
                means_sdr = [h['sdr_signal_mean'] for h in hexagons_with_data if h['sdr_signal_mean'] is not None]
                axes[1, 0].hist(means_sdr, bins=20, alpha=0.7, color='purple', edgecolor='black')
                axes[1, 0].set_xlabel('SDR信号平均值')
                axes[1, 0].set_ylabel('网格数量')
                axes[1, 0].set_title('SDR信号平均值分布')
                axes[1, 0].grid(True, alpha=0.3)
                
                # 最大值分布
                maxs_sdr = [h['sdr_signal_max'] for h in hexagons_with_data if h['sdr_signal_max'] is not None]
                axes[1, 1].hist(maxs_sdr, bins=20, alpha=0.7, color='magenta', edgecolor='black')
                axes[1, 1].set_xlabel('SDR信号最大值')
                axes[1, 1].set_ylabel('网格数量')
                axes[1, 1].set_title('SDR信号最大值分布')
                axes[1, 1].grid(True, alpha=0.3)
                
                # 最小值分布
                mins_sdr = [h['sdr_signal_min'] for h in hexagons_with_data if h['sdr_signal_min'] is not None]
                axes[1, 2].hist(mins_sdr, bins=20, alpha=0.7, color='cyan', edgecolor='black')
                axes[1, 2].set_xlabel('SDR信号最小值')
                axes[1, 2].set_ylabel('网格数量')
                axes[1, 2].set_title('SDR信号最小值分布')
                axes[1, 2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"正六边形网格统计图表已保存到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"创建正六边形网格统计图表失败: {str(e)}")
            raise
    
    def create_signal_heatmap(self, data: pd.DataFrame, signal_type: str = '4g_signal',
                             center_lat: Optional[float] = None, 
                             center_lon: Optional[float] = None,
                             zoom: int = 13) -> folium.Map:
        """
        创建信号强度热力图
        
        Args:
            data: 包含位置和信号数据的DataFrame
            signal_type: 信号类型 ('4g_signal' 或 'sdr_signal')
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom: 地图缩放级别
            
        Returns:
            Folium地图对象
        """
        try:
            # 确定地图中心点
            if center_lat is None or center_lon is None:
                center_lat = data['latitude'].mean()
                center_lon = data['longitude'].mean()
            
            # 创建基础地图
            signal_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # 准备热力图数据
            heatmap_data = []
            for _, row in data.iterrows():
                if pd.notna(row[signal_type]):
                    heatmap_data.append([
                        row['latitude'], 
                        row['longitude'], 
                        row[signal_type]
                    ])
            
            if not heatmap_data:
                self.logger.warning(f"没有有效的{signal_type}数据")
                return signal_map
            
            # 添加热力图层
            folium.plugins.HeatMap(
                heatmap_data,
                radius=15,
                blur=10,
                max_zoom=13,
                gradient={
                    0.0: 'blue',    # 弱信号
                    0.3: 'cyan',
                    0.5: 'yellow',
                    0.7: 'orange',
                    1.0: 'red'       # 强信号
                }
            ).add_to(signal_map)
            
            # 添加图例
            self._add_legend(signal_map, signal_type)
            
            # 添加数据点标记
            self._add_data_points(signal_map, data, signal_type)
            
            self.logger.info(f"成功创建{signal_type}信号热力图")
            return signal_map
            
        except Exception as e:
            self.logger.error(f"创建信号热力图失败: {str(e)}")
            raise
    
    def create_dual_signal_map(self, data: pd.DataFrame, 
                              center_lat: Optional[float] = None,
                              center_lon: Optional[float] = None,
                              zoom: int = 13) -> folium.Map:
        """
        创建双信号对比地图
        
        Args:
            data: 包含位置和信号数据的DataFrame
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom: 地图缩放级别
            
        Returns:
            Folium地图对象
        """
        try:
            # 确定地图中心点
            if center_lat is None or center_lon is None:
                center_lat = data['latitude'].mean()
                center_lon = data['longitude'].mean()
            
            # 创建基础地图
            dual_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # 创建图层控制
            folium.LayerControl().add_to(dual_map)
            
            # 添加4G信号热力图
            if '4g_signal' in data.columns:
                fg_4g = folium.FeatureGroup(name="4G信号强度")
                heatmap_data_4g = []
                for _, row in data.iterrows():
                    if pd.notna(row['4g_signal']):
                        heatmap_data_4g.append([
                            row['latitude'], 
                            row['longitude'], 
                            row['4g_signal']
                        ])
                
                if heatmap_data_4g:
                    folium.plugins.HeatMap(
                        heatmap_data_4g,
                        radius=15,
                        blur=10,
                        max_zoom=13,
                        gradient={
                            0.0: 'blue',
                            0.3: 'cyan', 
                            0.5: 'yellow',
                            0.7: 'orange',
                            1.0: 'red'
                        }
                    ).add_to(fg_4g)
                    fg_4g.add_to(dual_map)
            
            # 添加SDR信号热力图
            if 'sdr_signal' in data.columns:
                fg_sdr = folium.FeatureGroup(name="SDR信号质量")
                heatmap_data_sdr = []
                for _, row in data.iterrows():
                    if pd.notna(row['sdr_signal']):
                        heatmap_data_sdr.append([
                            row['latitude'], 
                            row['longitude'], 
                            row['sdr_signal']
                        ])
                
                if heatmap_data_sdr:
                    folium.plugins.HeatMap(
                        heatmap_data_sdr,
                        radius=15,
                        blur=10,
                        max_zoom=13,
                        gradient={
                            0.0: 'purple',
                            0.3: 'magenta',
                            0.5: 'pink',
                            0.7: 'lightcoral',
                            1.0: 'white'
                        }
                    ).add_to(fg_sdr)
                    fg_sdr.add_to(dual_map)
            
            self.logger.info("成功创建双信号对比地图")
            return dual_map
            
        except Exception as e:
            self.logger.error(f"创建双信号对比地图失败: {str(e)}")
            raise
    
    def create_signal_contour_plot(self, data: pd.DataFrame, signal_type: str = '4g_signal',
                                  output_path: str = 'signal_contour.png') -> None:
        """
        创建信号强度等高线图
        
        Args:
            data: 包含位置和信号数据的DataFrame
            signal_type: 信号类型
            output_path: 输出文件路径
        """
        try:
            # 过滤有效数据
            valid_data = data.dropna(subset=['latitude', 'longitude', signal_type])
            
            if len(valid_data) < 10:
                self.logger.warning(f"数据点不足，无法生成等高线图")
                return
            
            # 创建网格
            x_min, x_max = valid_data['longitude'].min(), valid_data['longitude'].max()
            y_min, y_max = valid_data['latitude'].min(), valid_data['latitude'].max()
            
            xi = np.linspace(x_min, x_max, 100)
            yi = np.linspace(y_min, y_max, 100)
            xi_grid, yi_grid = np.meshgrid(xi, yi)
            
            # 插值
            points = valid_data[['longitude', 'latitude']].values
            values = valid_data[signal_type].values
            
            zi = griddata(points, values, (xi_grid, yi_grid), method='cubic')
            
            # 创建图形
            plt.figure(figsize=(12, 8))
            
            # 绘制等高线
            contour = plt.contourf(xi_grid, yi_grid, zi, levels=20, cmap='viridis')
            plt.colorbar(contour, label=f'{signal_type} 信号强度')
            
            # 绘制数据点
            plt.scatter(valid_data['longitude'], valid_data['latitude'], 
                       c=valid_data[signal_type], s=20, alpha=0.7, cmap='viridis')
            
            plt.xlabel('经度')
            plt.ylabel('纬度')
            plt.title(f'{signal_type.upper()} 信号强度等高线图')
            plt.grid(True, alpha=0.3)
            
            # 保存图片
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"等高线图已保存到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"创建等高线图失败: {str(e)}")
            raise
    
    def create_signal_statistics_plot(self, data: pd.DataFrame, output_path: str = 'signal_stats.png') -> None:
        """
        创建信号统计图表
        
        Args:
            data: 包含信号数据的DataFrame
            output_path: 输出文件路径
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 4G信号分布直方图
            if '4g_signal' in data.columns:
                valid_4g = data['4g_signal'].dropna()
                if len(valid_4g) > 0:
                    axes[0, 0].hist(valid_4g, bins=30, alpha=0.7, color='blue', edgecolor='black')
                    axes[0, 0].set_xlabel('4G信号强度 (dBm)')
                    axes[0, 0].set_ylabel('频次')
                    axes[0, 0].set_title('4G信号强度分布')
                    axes[0, 0].grid(True, alpha=0.3)
            
            # SDR信号分布直方图
            if 'sdr_signal' in data.columns:
                valid_sdr = data['sdr_signal'].dropna()
                if len(valid_sdr) > 0:
                    axes[0, 1].hist(valid_sdr, bins=30, alpha=0.7, color='purple', edgecolor='black')
                    axes[0, 1].set_xlabel('SDR信号质量')
                    axes[0, 1].set_ylabel('频次')
                    axes[0, 1].set_title('SDR信号质量分布')
                    axes[0, 1].grid(True, alpha=0.3)
            
            # 信号强度随距离变化
            if '4g_signal' in data.columns and 'sdr_signal' in data.columns:
                # 计算到中心的距离
                center_lat = data['latitude'].mean()
                center_lon = data['longitude'].mean()
                
                distances = np.sqrt(
                    (data['latitude'] - center_lat)**2 + 
                    (data['longitude'] - center_lon)**2
                ) * 111000  # 转换为米
                
                valid_dist = distances.dropna()
                valid_4g = data['4g_signal'].dropna()
                valid_sdr = data['sdr_signal'].dropna()
                
                if len(valid_dist) > 0 and len(valid_4g) > 0:
                    axes[1, 0].scatter(valid_dist[:len(valid_4g)], valid_4g, alpha=0.6, color='blue')
                    axes[1, 0].set_xlabel('距离中心点距离 (米)')
                    axes[1, 0].set_ylabel('4G信号强度 (dBm)')
                    axes[1, 0].set_title('4G信号强度随距离变化')
                    axes[1, 0].grid(True, alpha=0.3)
                
                if len(valid_dist) > 0 and len(valid_sdr) > 0:
                    axes[1, 1].scatter(valid_dist[:len(valid_sdr)], valid_sdr, alpha=0.6, color='purple')
                    axes[1, 1].set_xlabel('距离中心点距离 (米)')
                    axes[1, 1].set_ylabel('SDR信号质量')
                    axes[1, 1].set_title('SDR信号质量随距离变化')
                    axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"统计图表已保存到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"创建统计图表失败: {str(e)}")
            raise
    
    def _add_legend(self, map_obj: folium.Map, signal_type: str) -> None:
        """添加图例到地图"""
        try:
            if signal_type == '4g_signal':
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 150px; height: 90px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>4G信号强度</b></p>
                <p><i class="fa fa-circle" style="color:red"></i> 强信号 (-50dBm)</p>
                <p><i class="fa fa-circle" style="color:yellow"></i> 中等信号 (-85dBm)</p>
                <p><i class="fa fa-circle" style="color:blue"></i> 弱信号 (-120dBm)</p>
                </div>
                '''
            else:
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 150px; height: 90px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>SDR信号质量</b></p>
                <p><i class="fa fa-circle" style="color:white"></i> 高质量 (100%)</p>
                <p><i class="fa fa-circle" style="color:pink"></i> 中等质量 (50%)</p>
                <p><i class="fa fa-circle" style="color:purple"></i> 低质量 (0%)</p>
                </div>
                '''
            
            map_obj.get_root().html.add_child(folium.Element(legend_html))
            
        except Exception as e:
            self.logger.warning(f"添加图例失败: {str(e)}")
    
    def _add_data_points(self, map_obj: folium.Map, data: pd.DataFrame, signal_type: str) -> None:
        """添加数据点标记到地图"""
        try:
            for _, row in data.iterrows():
                if pd.notna(row[signal_type]):
                    # 根据信号强度设置颜色
                    if signal_type == '4g_signal':
                        if row[signal_type] > -70:
                            color = 'red'
                        elif row[signal_type] > -90:
                            color = 'yellow'
                        else:
                            color = 'blue'
                    else:  # sdr_signal
                        if row[signal_type] > 80:
                            color = 'white'
                        elif row[signal_type] > 50:
                            color = 'pink'
                        else:
                            color = 'purple'
                    
                    # 添加标记
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=3,
                        color=color,
                        fill=True,
                        popup=f"{signal_type}: {row[signal_type]:.2f}"
                    ).add_to(map_obj)
                    
        except Exception as e:
            self.logger.warning(f"添加数据点标记失败: {str(e)}")
    
    def save_map(self, map_obj: folium.Map, output_path: str) -> None:
        """
        保存地图到文件
        
        Args:
            map_obj: Folium地图对象
            output_path: 输出文件路径
        """
        try:
            map_obj.save(output_path)
            self.logger.info(f"地图已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存地图失败: {str(e)}")
            raise
