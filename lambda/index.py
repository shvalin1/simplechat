# lambda/index.py
import json
import urllib.error
import urllib.request

# FastAPIエンドポイントのURL
FASTAPI_URL = "https://e5e8-34-126-131-45.ngrok-free.app"

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用してプロンプトを構築
        prompt = ""
        for msg in conversation_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                prompt += f"ユーザー: {content}\n"
            elif role == "assistant":
                prompt += f"アシスタント: {content}\n"
        
        # 最新のユーザーメッセージを追加
        prompt += f"ユーザー: {message}\nアシスタント: "
        
        print("Calling FastAPI endpoint with prompt:", prompt)
        
        # FastAPIサーバーへのリクエストデータ
        payload = {
            "prompt": prompt,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
        
        # URLリクエストを作成
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{FASTAPI_URL}/generate",
            data=data,
            headers={
                'Content-Type': 'application/json',
            },
            method='POST'
        )
        
        # タイムアウト設定でリクエストを実行
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                print("FastAPI response:", json.dumps(response_data))
        except urllib.error.HTTPError as e:
            raise Exception(f"API error: {e.code} - {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            raise Exception(f"URL error: {str(e)}")
        
        # アシスタントの応答を取得
        assistant_response = response_data["generated_text"]
        
        # アシスタントの応答を会話履歴に追加
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
