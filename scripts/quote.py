#!/usr/bin/env python3
"""quote.py — 全来店报价薄客户端（v2 资源流 / 可切回 legacy）"""
import argparse, json, os, sys, urllib.request, urllib.error

_ENV = (os.environ.get("QUOTE_API_URL") or "").rstrip("/")
for _s in ("/v1/quote", "/v1/quotes"):
    if _ENV.endswith(_s):
        _ENV = _ENV[: -len(_s)]
        break
API_BASE = _ENV
TOKEN    = os.environ.get("QUOTE_API_TOKEN")
FORMATS  = ("pdf", "xlsx", "json")
LABELS   = {"pdf": "报价单 PDF", "xlsx": "报价单 Excel", "json": "报价配置 JSON"}

def _call(method, path, body=None):
    if not API_BASE:
        sys.exit("配置缺失：环境变量 QUOTE_API_URL 未设置（UAT 示例：http://118.145.233.116:443）")
    if not TOKEN:
        sys.exit("配置缺失：环境变量 QUOTE_API_TOKEN 未设置")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        API_BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"服务端错误 {e.code}：{e.read().decode('utf-8', errors='replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"网络异常：{e.reason}")

def _preview(p):
    print("## 本次配置摘要\n")
    print(f"- 品牌：{p['brand']}")
    print(f"- 餐饮类型：{p['meal_type']}    门店数：{p['stores']}")
    print(f"- 套餐：{p['package']}    折扣：{p['discount']}")
    print(f"- 总价：¥{p['totals']['final']:,}（标价 ¥{p['totals']['list']:,}）\n")

def run_v2(form):
    created = _call("POST", "/v1/quotes", form)
    qid = created["quote_id"]
    _preview(created["preview"])
    ap = created["approval"]
    if ap["required"] and ap["state"] != "approved":
        print("## 待审批\n")
        print(f"- 报价 ID：`{qid}`")
        print(f"- 审批状态：{ap['state']}")
        print(f"- 触发原因：")
        for r in ap.get("reasons", []):
            print(f"  - {r}")
        print("\n配置已保存，暂不生成 PDF/Excel/JSON。请联系主管在 OpenClaw 内审批通过后，用同一个报价 ID 重新下发。")
        print(f"\n_报价版本：{created['pricing_version']}_")
        return
    print("## 下载文件\n")
    for fmt in FORMATS:
        r = _call("POST", f"/v1/quotes/{qid}/render/{fmt}")
        print(f"- [{LABELS[fmt]}]({r['url']})")
    print(f"\n_报价 ID：{qid}　报价版本：{created['pricing_version']}_")

def run_legacy(form):
    result = _call("POST", "/v1/quote", form)
    p, f = result["preview"], result["files"]
    _preview(p)
    print("## 下载文件\n")
    print(f"- [报价单 PDF]({f['pdf']['url']})")
    print(f"- [报价单 Excel]({f['xlsx']['url']})")
    print(f"- [报价配置 JSON]({f['json']['url']})")
    print(f"\n_报价版本：{result['pricing_version']}_")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--legacy", action="store_true",
                    help="走 POST /v1/quote 老接口；触发审批时服务端会返回 409")
    args = ap.parse_args()
    form = json.loads(open(args.form, encoding="utf-8").read())
    (run_legacy if args.legacy else run_v2)(form)

if __name__ == "__main__":
    main()
