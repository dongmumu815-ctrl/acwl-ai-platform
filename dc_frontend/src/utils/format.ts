/**
 * 格式化工具函数
 */

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm:ss 格式
 * @param date - 日期字符串、Date对象或时间戳
 * @param format - 格式化模式，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期时间字符串
 */
export function formatDateTime(
  date: string | Date | number | null | undefined,
  format: string = "YYYY-MM-DD HH:mm:ss",
): string {
  if (!date) return "-";

  try {
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) return "-";

    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const day = String(dateObj.getDate()).padStart(2, "0");
    const hours = String(dateObj.getHours()).padStart(2, "0");
    const minutes = String(dateObj.getMinutes()).padStart(2, "0");
    const seconds = String(dateObj.getSeconds()).padStart(2, "0");

    // 根据格式参数返回不同格式
    switch (format) {
      case "YYYY-MM-DD":
        return `${year}-${month}-${day}`;
      case "YYYY-MM-DD HH:mm":
        return `${year}-${month}-${day} ${hours}:${minutes}`;
      case "YYYY-MM-DD HH:mm:ss":
      default:
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }
  } catch (error) {
    console.error("日期时间格式化错误:", error);
    return "-";
  }
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param date - 日期字符串、Date对象或时间戳
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  date: string | Date | number | null | undefined,
): string {
  return formatDateTime(date, "YYYY-MM-DD");
}

/**
 * 格式化时间为 HH:mm:ss 格式
 * @param date - 日期字符串、Date对象或时间戳
 * @returns 格式化后的时间字符串
 */
export function formatTime(
  date: string | Date | number | null | undefined,
): string {
  if (!date) return "-";

  try {
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) return "-";

    const hours = String(dateObj.getHours()).padStart(2, "0");
    const minutes = String(dateObj.getMinutes()).padStart(2, "0");
    const seconds = String(dateObj.getSeconds()).padStart(2, "0");

    return `${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error("时间格式化错误:", error);
    return "-";
  }
}

/**
 * 格式化文件大小
 * @param bytes - 字节数
 * @param decimals - 小数位数，默认为2
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(
  bytes: number | null | undefined,
  decimals: number = 2,
): string {
  if (!bytes || bytes === 0) return "0 B";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

/**
 * 格式化数字，添加千分位分隔符
 * @param num - 数字
 * @param decimals - 小数位数，默认为0
 * @returns 格式化后的数字字符串
 */
export function formatNumber(
  num: number | null | undefined,
  decimals: number = 0,
): string {
  if (num === null || num === undefined) return "-";

  return num.toLocaleString("zh-CN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * 格式化百分比
 * @param value - 数值（0-1之间的小数或0-100之间的整数）
 * @param decimals - 小数位数，默认为1
 * @param isDecimal - 输入值是否为小数形式（0-1），默认为true
 * @returns 格式化后的百分比字符串
 */
export function formatPercentage(
  value: number | null | undefined,
  decimals: number = 1,
  isDecimal: boolean = true,
): string {
  if (value === null || value === undefined) return "-";

  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * 格式化货币
 * @param amount - 金额
 * @param currency - 货币符号，默认为'¥'
 * @param decimals - 小数位数，默认为2
 * @returns 格式化后的货币字符串
 */
export function formatCurrency(
  amount: number | null | undefined,
  currency: string = "¥",
  decimals: number = 2,
): string {
  if (amount === null || amount === undefined) return "-";

  return `${currency}${formatNumber(amount, decimals)}`;
}

/**
 * 格式化手机号码
 * @param phone - 手机号码
 * @returns 格式化后的手机号码字符串
 */
export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return "-";

  // 移除所有非数字字符
  const cleaned = phone.replace(/\D/g, "");

  // 中国手机号格式：138-1234-5678
  if (cleaned.length === 11) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7)}`;
  }

  return phone;
}

/**
 * 格式化身份证号码（脱敏）
 * @param idCard - 身份证号码
 * @returns 脱敏后的身份证号码
 */
export function formatIdCard(idCard: string | null | undefined): string {
  if (!idCard) return "-";

  if (idCard.length === 18) {
    return `${idCard.slice(0, 6)}********${idCard.slice(-4)}`;
  } else if (idCard.length === 15) {
    return `${idCard.slice(0, 6)}*****${idCard.slice(-4)}`;
  }

  return idCard;
}

/**
 * 格式化邮箱（脱敏）
 * @param email - 邮箱地址
 * @returns 脱敏后的邮箱地址
 */
export function formatEmail(email: string | null | undefined): string {
  if (!email) return "-";

  const atIndex = email.indexOf("@");
  if (atIndex > 0) {
    const username = email.slice(0, atIndex);
    const domain = email.slice(atIndex);

    if (username.length <= 3) {
      return `${username.slice(0, 1)}**${domain}`;
    } else {
      return `${username.slice(0, 2)}***${username.slice(-1)}${domain}`;
    }
  }

  return email;
}
