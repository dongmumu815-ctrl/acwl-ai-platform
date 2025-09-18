import asyncio
import aiohttp
import json

async def test_ollama_direct():
    """直接测试ollama API调用"""
    url = "http://acepiec-ai.acoming.net:11868/api/chat"
    
    payload = {
        "model": "qwen2.5:7b",
        "messages": [
            {"role": "user", "content": "你好，请简单回复一下"}
        ],
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"状态码: {response.status}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"完整响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    print(f"数据类型: {type(data)}")
                    
                    # 检查message字段
                    if "message" in data:
                        message = data["message"]
                        print(f"message字段类型: {type(message)}")
                        print(f"message内容: {message}")
                        
                        if isinstance(message, dict) and "content" in message:
                            content = message["content"]
                            print(f"content: {content}")
                        else:
                            print("message不是字典或没有content字段")
                    else:
                        print("响应中没有message字段")
                else:
                    error_text = await response.text()
                    print(f"错误响应: {error_text}")
                    
    except Exception as e:
        print(f"请求异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())