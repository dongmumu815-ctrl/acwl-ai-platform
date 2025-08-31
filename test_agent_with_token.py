import asyncio
import aiohttp
import json

async def test_agent_chat_with_token():
    """
    使用提供的 access_token 测试 Agent 聊天 API
    """
    # 使用用户提供的 access_token
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU2NDY1MjQ1fQ.rKwu3wkMTw-9kwA945IrYJIhXK679z9oW0gXb5b95cM"
    
    # API 端点
    base_url = "http://localhost:3000"
    chat_url = f"{base_url}/api/v1/agents/32/chat"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 聊天请求数据
    chat_data = {
        "message": "你好，请介绍一下自己",
        "conversation_id": None
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"发送聊天请求到: {chat_url}")
            print(f"请求数据: {json.dumps(chat_data, ensure_ascii=False, indent=2)}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            
            async with session.post(chat_url, json=chat_data, headers=headers) as response:
                print(f"\n响应状态码: {response.status}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"\n响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    print(f"\n响应数据类型: {type(response_data)}")
                    
                    # 检查响应结构
                    if isinstance(response_data, dict):
                        print(f"\n响应字段: {list(response_data.keys())}")
                        if 'message' in response_data:
                            print(f"message 字段类型: {type(response_data['message'])}")
                            print(f"message 内容: {response_data['message']}")
                else:
                    error_text = await response.text()
                    print(f"\n错误响应: {error_text}")
                    
    except Exception as e:
        print(f"\n请求异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_chat_with_token())