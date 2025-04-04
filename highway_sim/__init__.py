"""
高速公路交通仿真系统（highway_sim）

一个基于离散事件仿真的高速公路车辆通行模拟系统，提供车辆路径选择、通行时间统计、2D/3D可视化等功能。
主要用于模拟车辆在高速公路网络中的行驶行为，收集门架通行数据，并进行交通流量统计分析。

子包结构说明：
    - components/      : 核心组件模块（车辆实体、车辆生成器等）
        - car.py         : 车辆行为模拟组件
        - car_generator.py: 车辆生成器组件
    - config/          : 配置管理模块
        - args.py        : 命令行参数解析
        - resources.py   : 资源路径配置
    - data_parser/     : 数据解析模块
        - road_network.py: 路网数据解析器
        - traffic.py     : 交通流量数据解析器
    - entity/          : 实体定义模块
        - location.py    : 位置实体（收费站/门架）定义
    - mySalabim/       : 可视化增强模块
        - d2_interface_enhanced.py : 2D可视化增强
        - d3_performance_enhanced.py: 3D可视化增强
    - stats/           : 统计模块
        - default.py     : 默认统计指标收集
    - util/            : 工具模块
        - distribution.py: 概率分布工具

运行方式：
export PYTHONPATH=/extend/school/projects/highwaysim:$PYTHONPATH
cd hiway_sim
python main.py

关键启动参数说明:
--log        : 启用日志记录（默认输出到../log/statistics.log）
--log-level  : 设置日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
--d2         : 启用2D可视化
--d3         : 启用3D可视化

典型工作流程:
1. 解析路网数据和交通流量数据
2. 初始化车辆生成器和仿真环境
3. 运行离散事件仿真
4. 收集通行时间和路径选择数据
5. 输出统计结果和可视化动画
"""
