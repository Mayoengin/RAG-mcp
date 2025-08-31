#!/usr/bin/env python3
"""Test LM Studio connectivity"""

import asyncio
import aiohttp

async def test_lm_studio():
    print("🔍 Testing LM Studio connection...")
    
    try:
        async with aiohttp.ClientSession() as session:
            test_payload = {
                "model": "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
                "temperature": 0.1
            }
            async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                   json=test_payload, 
                                   timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Response data: {data}")
                    if 'choices' in data and len(data['choices']) > 0:
                        print("✅ LM Studio is running with your Llama model!")
                        return True
                    else:
                        print("⚠️  LM Studio responded but no choices available")
                        return False
                else:
                    print(f"❌ LM Studio returned status {response.status}")
                    response_text = await response.text()
                    print(f"Response text: {response_text}")
                    return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_lm_studio())