import argparse
import logging
import os

import highway_sim.config.args as config

# 当您执行 import config 时，整个 config 模块被导入，您需要通过 config.ENABLE_LOG 来访问和修改其中的变量。
# 当您执行 from config import ENABLE_LOG 时，ENABLE_LOG 变量被导入到当前模块的命名空间中，
# 成为一个独立的拷贝。此时，修改 ENABLE_LOG 只会影响当前模块的变量，不会影响 config 模块中的同名变量。

str2level = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


# todo: 使用文件配置

class Parser:
    """
    Parser类用于解析命令行参数，并更新全局配置
    参数包括：
    - --log: 是否开启日志记录
    - --log-level: 日志级别
    - --log-file: 日志文件路径
    - --d2: 是否开启2D动画
    - --d3: 是否开启3D动画
    """

    def __init__(self):
        parser = argparse.ArgumentParser(description='Highway Simulator')
        parser.add_argument('--log', action='store_true', help='Enable logging')
        parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
        parser.add_argument('--log-file', type=str, default='../log/statistics.log', help='Logging file')
        parser.add_argument('--d2', action='store_true', help='Enable 2D visualization')
        parser.add_argument('--d3', action='store_true', help='Enable 3D visualization')
        self.parser = parser
        args = parser.parse_args()
        self.__update_config(args)

    @classmethod
    def __update_config(cls, args: argparse.Namespace) -> None:
        if args.log:
            config.ENABLE_LOG = True
        else:
            print("test")
            config.ENABLE_LOG = False
        if args.log_level:
            if args.log_level in str2level:
                config.LOG_LEVEL = str2level[args.log_level]
            else:
                raise ValueError(f'Invalid logging level: {args.log_level}')
        if args.log_file:
            config.LOG_FILE = args.log_file
            # checkdir
            if not os.path.exists(os.path.dirname(config.LOG_FILE)):
                os.makedirs(os.path.dirname(config.LOG_FILE))
        if args.d2:
            config.ENABLE_2D = True
        else:
            config.ENABLE_2D = False
        if args.d3:
            config.ENABLE_3D = True
        else:
            config.ENABLE_3D = False
