/**
 * JavaScript 示例文件
 * 演示JavaScript语法高亮效果
 */

// ES6 类定义
class DataProcessor {
    constructor(name, config = {}) {
        this.name = name;
        this.config = config;
        this.data = [];
    }
    
    /**
     * 处理数据项
     * @param {Array} items - 输入数据列表
     * @returns {Array} 处理后的数据列表
     */
    process(items) {
        const result = [];
        
        for (const item of items) {
            // 过滤空值
            if (!item) {
                continue;
            }
            
            // 转换为大写
            const processed = item.toUpperCase();
            result.push(processed);
        }
        
        return result;
    }
    
    /**
     * 使用函数式编程处理数据
     */
    processWithFunctional(items) {
        return items
            .filter(item => item && item.length > 0)
            .map(item => item.toUpperCase());
    }
    
    /**
     * 异步处理数据
     */
    async processAsync(items) {
        return new Promise((resolve, reject) => {
            try {
                const result = this.process(items);
                resolve(result);
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * 验证数据
     */
    static validate(data) {
        return data && data.length > 0;
    }
    
    /**
     * 获取数据数量
     */
    get count() {
        return this.data.length;
    }
}

// 箭头函数
const square = (x) => x * x;
const add = (a, b) => a + b;

// 解构赋值
const { name, age } = { name: 'John', age: 30 };
const [first, second, ...rest] = [1, 2, 3, 4, 5];

// 模板字符串
const greeting = `Hello, ${name}! You are ${age} years old.`;

// Promise和async/await
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
}

// 主函数
function main() {
    const processor = new DataProcessor('test');
    
    // 测试数据
    const testData = ['hello', 'world', '', 'javascript'];
    
    // 处理数据
    const result = processor.process(testData);
    
    // 输出结果
    result.forEach(item => console.log(`Processed: ${item}`));
    
    // 数组方法
    const numbers = [1, 2, 3, 4, 5];
    const squared = numbers.map(x => x * x);
    const sum = numbers.reduce((acc, x) => acc + x, 0);
    
    console.log('Squared:', squared);
    console.log('Sum:', sum);
    
    // 对象展开
    const obj1 = { a: 1, b: 2 };
    const obj2 = { ...obj1, c: 3 };
    
    console.log('Merged object:', obj2);
}

// 执行主函数
main();

// 导出模块
export { DataProcessor, square, add };
export default DataProcessor;
