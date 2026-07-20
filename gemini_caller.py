import sys
import json
import google.generativeai as genai

def main():
    if len(sys.argv) < 2:
        print("Error: No input file provided", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        api_key = data.get("api_key")
        prompt = data.get("prompt")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        print(resp.text)
    except Exception as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
