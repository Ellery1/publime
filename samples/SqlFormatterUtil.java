package com.xyd.luban.util.dep;

import com.xyd.luban.result.Result;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * @author zhangsheng
 */
public class SqlFormatterUtil {

    public static Result<Object> processLogToSql(String logWithSql, String paramLog) {
        try {
            // Validate inputs
            if (logWithSql == null || paramLog == null) {
                return Result.failure("Input logs cannot be null");
            }

            String rawSql = extractSqlFromLog(logWithSql);
            String processedSql = removeCountWrapper(rawSql);
            String[] parameters = extractParameters(paramLog);

            // 参数校验
            validateParameters(processedSql, parameters);

            String executableSql = replaceParameters(processedSql, parameters);
            String formattedSql = formatSql(executableSql);

            return Result.ok(formattedSql);
        } catch (IllegalArgumentException e) {
            return Result.failure("参数验证失败: " + e.getMessage());
        } catch (Exception e) {
            return Result.failure("SQL处理异常: " + e.getMessage());
        }
    }

        // 参数个数校验方法
        private static void validateParameters(String sql, String[] parameters) throws IllegalArgumentException {
            int paramCount = countQuestionMarks(sql);
            if (paramCount != parameters.length) {
                throw new IllegalArgumentException(
                        String.format("参数个数不匹配。SQL需要%d个参数，但提供了%d个参数",
                                paramCount, parameters.length)
                );
            }
        }

        // 统计SQL中的问号数量
        private static int countQuestionMarks(String sql) {
            Matcher matcher = Pattern.compile("\\?").matcher(sql);
            int count = 0;
            while (matcher.find()) {
                count++;
            }
            return count;
        }

    private static String extractSqlFromLog(String log) {
        // 情况1：处理带"执行sql:"前缀的日志
        if (log.contains("执行sql:")) {
            int start = log.indexOf("执行sql:") + "执行sql:".length();
            return log.substring(start).trim();
        }
        // 情况2：处理带"Preparing:"前缀的MyBatis日志
        else if (log.contains("Preparing:")) {
            int start = log.indexOf("Preparing:") + "Preparing:".length();
            return log.substring(start).trim();
        }
        // 未知格式
        throw new IllegalArgumentException("无法识别的SQL日志格式，必须包含'执行sql:'或'Preparing:'前缀");
    }

        private static String removeCountWrapper(String sql) {
            String prefix = "SELECT COUNT(1) as total FROM (";
            String suffix = ") TMP";

            if (sql.startsWith(prefix)) {
                sql = sql.substring(prefix.length());
            }
            if (sql.endsWith(suffix)) {
                sql = sql.substring(0, sql.length() - suffix.length());
            }
            return sql.trim();
        }

//    private static String[] extractParameters(String paramLog) {
//        // 情况1：处理JSON数组格式 "执行参数:["value1","value2"]"
//        if (paramLog.contains("执行参数:")) {
//            String paramStr = paramLog.substring(paramLog.indexOf("执行参数:") + "执行参数:".length())
//                    .trim()
//                    .replaceAll("^\\[|]$", "");
//            return Pattern.compile("\"([^\"]*)\"")
//                    .matcher(paramStr)
//                    .results()
//                    .map(m -> m.group(1))
//                    .toArray(String[]::new);
//        }
//        // 情况2：处理新格式 "Parameters: value1(String), value2(String)"
//        else if (paramLog.contains("Parameters:")) {
//            String paramStr = paramLog.substring(paramLog.indexOf("Parameters:") + "Parameters:".length())
//                    .trim();
//            // 直接按逗号拆分，并去除类型声明（如(String)）和前后空格
//            // 使用负向零宽断言确保不分割括号内的逗号
//            // 移除类型声明
//            return Arrays.stream(paramStr.split(",(?![^()]*\\))"))
//                    .map(s -> s.replaceAll("\\(.*\\)", "").trim())
//                    .toArray(String[]::new);
//        }
//        throw new IllegalArgumentException("无法识别的参数格式: " + paramLog);
//    }

    private static String[] extractParameters(String paramLog) {
        // 情况1：处理JSON数组格式 "执行参数:["value1","value2",123,true]"
        if (paramLog.contains("执行参数:")) {
            String paramStr = paramLog.substring(paramLog.indexOf("执行参数:") + "执行参数:".length())
                    .trim()
                    .replaceAll("^\\[|]$", "");

            // 使用更灵活的正则表达式匹配JSON数组中的元素
            List<String> params = new ArrayList<>();
            Pattern pattern = Pattern.compile("\"([^\"]*)\"|([^,]+)");
            Matcher matcher = pattern.matcher(paramStr);

            while (matcher.find()) {
                if (matcher.group(1) != null) {
                    // 匹配到带引号的字符串
                    params.add(matcher.group(1));
                } else if (matcher.group(2) != null) {
                    // 匹配到不带引号的值（数字、布尔值等）
                    params.add(matcher.group(2).trim());
                }
            }

            return params.toArray(new String[0]);
        }
        // 情况2：处理新格式 "Parameters: value1(String), value2(String)"
        else if (paramLog.contains("Parameters:")) {
            String paramStr = paramLog.substring(paramLog.indexOf("Parameters:") + "Parameters:".length())
                    .trim();
            // 直接按逗号拆分，并去除类型声明（如(String)）和前后空格
            // 使用负向零宽断言确保不分割括号内的逗号
            // 移除类型声明
            return Arrays.stream(paramStr.split(",(?![^()]*\\))"))
                    .map(s -> s.replaceAll("\\(.*\\)", "").trim())
                    .toArray(String[]::new);
        }
        throw new IllegalArgumentException("无法识别的参数格式: " + paramLog);
    }

        private static String replaceParameters(String sql, String[] params) {
            StringBuilder sb = new StringBuilder();
            int paramIndex = 0;
            int lastPos = 0;

            Matcher matcher = Pattern.compile("\\?").matcher(sql);
            while (matcher.find()) {
                sb.append(sql, lastPos, matcher.start());

                String param = params[paramIndex++];
                if (isDateTimeParam(param) || !isNumeric(param)) {
                    sb.append("'").append(param).append("'");
                } else {
                    sb.append(param);
                }

                lastPos = matcher.end();
            }
            sb.append(sql.substring(lastPos));
            return sb.toString();
        }

    private static String formatSql(String sql) {
        // 1. 基础清理：压缩多余空格但保留换行
        sql = sql.replaceAll("(?m)\\s+", " ").trim();

        // 2. 关键子句换行处理（保留原有换行基础）
        sql = sql.replaceAll("(?i)\\b(SELECT|FROM|WHERE|JOIN|ON|AND|OR|ORDER BY|GROUP BY|UNION ALL|LEFT JOIN|INNER JOIN)\\b", "\n$1");

        // 3. 字段列表处理（保持垂直对齐）
        sql = sql.replaceAll("(?i)(SELECT\\s+)", "$1\n  ")
                .replaceAll(",", ",\n  ");

        // 4. 括号处理（不再强制括号换行）
        // 左括号前保留一个空格, 右括号后保留一个空格
        sql = sql.replaceAll("\\s*\\(", " (")
                .replaceAll("\\)\\s*", ") ");

        // 5. 特定函数处理（DATE_FORMAT, parse_json等保持紧凑）
        sql = sql.replaceAll("(?i)(DATE_FORMAT|parse_json|concat|least|date|ifnull)\\s*\\(", "$1(");

        // 6. 清理多余空行
        sql = sql.replaceAll("(?m)^\\s*$[\n\r]+", "\n");

        // 7. 统一缩进（2空格）
        String[] lines = sql.split("\n");
        StringBuilder result = new StringBuilder();
        int indent = 0;

        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }

            // 减少缩进的情况
            if (line.startsWith(")") || line.matches("(?i).*\\b(ON|AND|OR)\\b.*")) {
                indent = Math.max(0, indent - 2);
            }

            // 添加行
            result.append(" ".repeat(indent)).append(line).append("\n");

            // 增加缩进的情况
            if (line.matches("(?i).*\\b(SELECT|FROM|WHERE|JOIN|GROUP BY|ORDER BY)\\b.*")) {
                indent += 2;
            }
        }

        return result.toString()
                .trim()
                .replaceAll("\n", " ")
                .replaceAll("\\s+", " ")
                .replaceAll("\\s*\\(", " (")
                .replaceAll("\\)\\s*", ") ");
    }

        private static boolean isDateTimeParam(String param) {
            return param.matches("\\d{4}-\\d{2}-\\d{2}( \\d{2}:\\d{2}:\\d{2})?");
        }

        private static boolean isNumeric(String str) {
            return str.matches("-?\\d+(\\.\\d+)?");
        }

}
