#!/usr/bin/env python3
"""quote.py — 全来店报价薄客户端"""
import argparse, json, os, sys, urllib.request, urllib.error

API   = os.environ.get("QUOTE_API_URL", "https://<your-api-host>/v1/quote")
TOKEN = os.environ.get("QUOTE_API_TOKEN")

def call_server(form):
    if not TOKEN:
        sys.exit("配置缺失：环境变量 QUOTE_API_TOKEN 未设置")
    req = urllib.request.Request(
        API,
        data=json.dumps(form, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"服务端错误 {e.code}：{body}")
    except urllib.error.URLError as e:
        sys.exit(f"网络异常：{e.reason}")

def render(result):
    p, f = result["preview"], result["files"]
    print("## 本次配置摘要\n")
    print(f"- 品牌：{p['brand']}")
    print(f"- 餐饮类型：{p['meal_type']}    门店数：{p['stores']}")
    print(f"- 套餐：{p['package']}")
    print(f"- 总价：¥{p['totals']['final']:,}\n")
    info = result.get("pricing_info") or {}
    requested = info.get("original_requested_store_count")
    effective = info.get("effective_store_count")
    if requested and effective and requested != effective:
        print(f"> 输入 {requested} 店落在大客户段，主报价按 {effective} 店方案生成；")
        print(f"> PDF/Excel 附相邻两档阶梯对比页，供客户做规模决策参考。\n")
    print("## 下载文件\n")
    print(f"- [报价单 PDF]({f['pdf']['url']})")
    print(f"- [报价单 Excel]({f['xlsx']['url']})")
    print(f"- [报价配置 JSON]({f['json']['url']})")
    print(f"\n_报价版本：{result['pricing_version']}_")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    args = ap.parse_args()
    render(call_server(json.loads(open(args.form, encoding="utf-8").read())))

if __name__ == "__main__":
    main()
