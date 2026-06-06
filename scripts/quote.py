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

def fetch_financials(json_url):
    # 财务数据只在下载的 JSON 里，result 不含；短链公开可读，无需鉴权。任何失败返回 None，不阻塞主报价。
    try:
        with urllib.request.urlopen(json_url, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def render_profit(data):
    fin = (data or {}).get("internal_financials")
    if not fin:
        return ""
    lines = ["## 报价利润评估（内部）\n"]
    lines.append(f"- 报价总额：¥{fin['quote_total']:,}    成本总额：¥{fin['cost_total']:,}")
    lines.append(f"- 利润总额：¥{fin['profit_total']:,}    利润率：{fin['profit_rate']}%\n")
    items = data.get("报价项目") or []
    if items:
        lines.append("| 项目 | 数量 | 报价小计 | 成本小计 | 利润 | 利润率 |")
        lines.append("|------|------|---------|---------|------|--------|")
        for it in items:
            lines.append(
                f"| {it.get('商品名称', '')} | {it.get('数量', '')} "
                f"| ¥{it.get('报价小计', 0):,} | ¥{it.get('成本小计', 0):,} "
                f"| ¥{it.get('利润', 0):,} | {it.get('利润率', 0)}% |")
    return "\n".join(lines)

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
    print("> 链接请整段原样复制到回复，勿缩写或加省略号。\n")
    print("报价单 PDF")
    print(f"{f['pdf']['url']}\n")
    print("报价单 Excel")
    print(f"{f['xlsx']['url']}\n")
    print("报价配置 JSON")
    print(f"{f['json']['url']}\n")
    print(f"_报价版本：{result['pricing_version']}_")
    block = render_profit(fetch_financials(f["json"]["url"]))
    if block:
        print(f"\n{block}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    args = ap.parse_args()
    render(call_server(json.loads(open(args.form, encoding="utf-8").read())))

if __name__ == "__main__":
    main()
