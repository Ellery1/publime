"""
Python 示例文件
演示Python语法高亮效果
"""

import os
import sys
from typing import List, Dict, Optional
from datetime import datetime


class DataProcessor:
    """数据处理器类"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.data = []
    
    def process(self, items: List[str]) -> List[str]:
        """
        处理数据项
        
        Args:
            items: 输入数据列表
            
        Returns:
            处理后的数据列表
        """
        result = []
        for item in items:
            # 过滤空值
            if not item:
                continue
            
            # 转换为大写
            processed = item.upper()
            result.append(processed)
        
        return result
    
    @staticmethod
    def validate(data: str) -> bool:
        """验证数据"""
        return len(data) > 0 and data.isalnum()
    
    @property
    def count(self) -> int:
        """获取数据数量"""
        return len(self.data)


def main():
    """主函数"""
    processor = DataProcessor("test")
    
    # 测试数据
    test_data = ["hello", "world", "", "python"]
    
    # 处理数据
    result = processor.process(test_data)
    
    # 输出结果
    for item in result:
        print(f"Processed: {item}")
    
    # Lambda表达式
    squared = list(map(lambda x: x ** 2, range(10)))
    print(f"Squared numbers: {squared}")
    
    # 列表推导式
    even_numbers = [x for x in range(20) if x % 2 == 0]
    print(f"Even numbers: {even_numbers}")


if __name__ == "__main__":
    main()
