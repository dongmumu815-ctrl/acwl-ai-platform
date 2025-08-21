// 测试认证状态的简单脚本
// 在浏览器控制台中运行

console.log('=== 认证状态检查 ===');

// 检查localStorage中的token
const localToken = localStorage.getItem('acwl_token');
console.log('localStorage token:', localToken ? localToken.substring(0, 50) + '...' : 'null');

// 检查cookie中的token
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

const cookieToken = getCookie('acwl_token');
console.log('Cookie token:', cookieToken ? cookieToken.substring(0, 50) + '...' : 'null');

// 检查token是否过期
function isTokenExpired(token) {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // 转换为毫秒
    const now = Date.now();
    console.log('Token expires at:', new Date(exp));
    console.log('Current time:', new Date(now));
    return now >= exp;
  } catch (error) {
    console.error('解析token失败:', error);
    return true;
  }
}

const currentToken = localToken || cookieToken;
if (currentToken) {
  console.log('Token expired:', isTokenExpired(currentToken));
} else {
  console.log('No token found - user needs to login');
}

// 测试API调用
if (currentToken) {
  console.log('\n=== 测试API调用 ===');
  
  fetch('/api/v1/auth/me', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${currentToken}`,
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    console.log('API Response status:', response.status);
    if (response.status === 401) {
      console.log('❌ 401 Unauthorized - Token invalid or expired');
    } else if (response.status === 200) {
      console.log('✅ 200 OK - Token is valid');
      return response.json();
    } else {
      console.log('⚠️ Unexpected status:', response.status);
    }
    return response.text();
  })
  .then(data => {
    console.log('API Response data:', data);
  })
  .catch(error => {
    console.error('API call failed:', error);
  });
}

console.log('\n=== 建议解决方案 ===');
if (!currentToken) {
  console.log('1. 用户需要重新登录');
  console.log('2. 访问 http://localhost:3000/login');
} else if (isTokenExpired(currentToken)) {
  console.log('1. Token已过期，需要重新登录');
  console.log('2. 清除本地存储: localStorage.removeItem("acwl_token")');
  console.log('3. 访问 http://localhost:3000/login');
} else {
  console.log('1. Token看起来有效，可能是后端问题');
  console.log('2. 检查后端服务是否正常运行');
  console.log('3. 检查数据库连接');
}