/**
 * Java 示例文件
 * 演示Java语法高亮效果
 */

package com.example.demo;

import java.util.*;
import java.util.stream.Collectors;

public class DataProcessor {
    
    private String name;
    private Map<String, Object> config;
    private List<String> data;
    
    /**
     * 构造函数
     * @param name 处理器名称
     */
    public DataProcessor(String name) {
        this.name = name;
        this.config = new HashMap<>();
        this.data = new ArrayList<>();
    }
    
    /**
     * 处理数据项
     * @param items 输入数据列表
     * @return 处理后的数据列表
     */
    public List<String> process(List<String> items) {
        List<String> result = new ArrayList<>();
        
        for (String item : items) {
            // 过滤空值
            if (item == null || item.isEmpty()) {
                continue;
            }
            
            // 转换为大写
            String processed = item.toUpperCase();
            result.add(processed);
        }
        
        return result;
    }
    
    /**
     * 使用Stream API处理数据
     */
    public List<String> processWithStream(List<String> items) {
        return items.stream()
                .filter(item -> item != null && !item.isEmpty())
                .map(String::toUpperCase)
                .collect(Collectors.toList());
    }
    
    /**
     * 验证数据
     */
    public static boolean validate(String data) {
        return data != null && data.length() > 0;
    }
    
    /**
     * 获取数据数量
     */
    public int getCount() {
        return data.size();
    }
    
    /**
     * 主函数
     */
    public static void main(String[] args) {
        DataProcessor processor = new DataProcessor("test");
        
        // 测试数据
        List<String> testData = Arrays.asList("hello", "world", "", "java");
        
        // 处理数据
        List<String> result = processor.process(testData);
        
        // 输出结果
        result.forEach(item -> System.out.println("Processed: " + item));
        
        // Lambda表达式
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
        numbers.stream()
                .map(x -> x * x)
                .forEach(System.out::println);
    }
}
