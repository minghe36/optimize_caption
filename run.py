import sys
import os
import requests
import json
import time

# Dify API 密钥
DIFY_API_KEY1 = 'app-3O5o13APhVCRwfKEa5byRwD2'
DIFY_API_KEY2 = 'app-iOIszLBwytwwjN6i1V697a5U'

def call_dify_api(srtText, title, api_key):
    url = 'https://api.dify.ai/v1/workflows/run'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "inputs": {
            "caption": srtText,
            "title": title
        },
        "response_mode": "streaming",
        "user": "local"
    }
    
    print("正在调用 Dify API...")
    response = requests.post(url, headers=headers, json=data, stream=True)
    response.raise_for_status()
    
    result = ""
    start_time = time.time()
    timeout = 300  # 5分钟超时
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data:'):
                try:
                    json_data = json.loads(decoded_line[5:])
                    if json_data.get('event') == 'text_chunk':
                        result += json_data['data']['text']
                    elif json_data.get('event') == 'workflow_finished':
                        if 'outputs' in json_data['data'] and 'result' in json_data['data']['outputs']:
                            result = json_data['data']['outputs']['result']
                        break
                except json.JSONDecodeError:
                    print(f"警告: 无法解析JSON数据")
        
        if time.time() - start_time > timeout:
            print("警告: API 请求超时")
            break
    
    return result

def main(file_path, title, bilingual):
    if not file_path.lower().endswith('.srt'):
        print("错误: 只支持 .srt 后缀的文件")
        sys.exit(1)
    
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        sys.exit(1)
    
    print(f"处理文件: {file_path}")
    print(f"文稿主题: {title}")
    print(f"双语字幕模式: {'是' if bilingual else '否'}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            srtText = file.read()
        print(f"成功读取文件内容,共 {len(srtText)} 个字符")
        
        if bilingual:
            api_key = DIFY_API_KEY2
        else:
            api_key = DIFY_API_KEY1    
        
        new_content = call_dify_api(srtText, title, api_key)
     
        new_file_path = os.path.splitext(file_path)[0] + '.new.srt'
        with open(new_file_path, 'w', encoding='utf-8') as new_file:
            new_file.write(new_content)
        print(f"已生成新文件: {new_file_path}")
        
    except IOError as e:
        print(f"错误: 无法读取或写入文件. {str(e)}")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"错误: 文件 '{file_path}' 编码不是 UTF-8,请检查文件编码")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"错误: 调用 Dify API 失败. {str(e)}")
        sys.exit(1)

def merge_subtitles(original, translated):
    original_lines = original.split('\n')
    translated_lines = translated.split('\n')
    merged = []
    
    i, j = 0, 0
    while i < len(original_lines) and j < len(translated_lines):
        # 添加字幕序号和时间戳
        merged.append(original_lines[i])
        merged.append(original_lines[i+1])
        
        # 添加原文和翻译
        merged.append(original_lines[i+2])
        merged.append(translated_lines[j+2])
        
        # 添加空行
        merged.append('')
        
        i += 4
        j += 4
    
    return '\n'.join(merged)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python run.py <文件路径> <文稿主题> <bilingual>")
        print("bilingual: 输入 'true' 使用双语字幕模式，其他输入使用默认模式")
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2]
    bilingual = sys.argv[3].lower() == 'true'
    main(file_path, title, bilingual)