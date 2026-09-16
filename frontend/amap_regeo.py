"""
高德逆地理编码(regeo)接口请求脚本

接口地址: https://ditu.amap.com/service/regeo
请求方式: GET
请求参数: longitude(经度), latitude(纬度)
返回格式: JSON

功能:
    - 根据经纬度查询所在 国家/省/市/区/详细描述/周边道路 等
    - 支持命令行传参, 也支持不传参时使用默认坐标
    - 打印原始JSON, 并对关键字段做友好展示

用法示例:
    python amap_regeo.py                            # 默认坐标
    python amap_regeo.py -l 121.049 -t 31.315        # 指定经纬度
    python amap_regeo.py --longitude 116.397 --latitude 39.909 --raw
    python amap_regeo.py -l 121.049 -t 31.315 -o result.json
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

API_URL = "https://ditu.amap.com/service/regeo"


def regeo(longitude, latitude, timeout=10):
    """向高德 regeo 接口发起 GET 请求, 返回解析后的 dict。

    参数:
        longitude: 经度 (可以是数字或字符串)
        latitude : 纬度
    返回:
        dict : 接口返回的 JSON 数据
    异常:
        RuntimeError : 网络错误 / 返回非 JSON 时抛出
    """
    params = {
        "longitude": longitude,
        "latitude": latitude,
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)

    # 高德对没有 UA 的请求可能拒绝, 带上浏览器 UA
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError("网络请求失败: {}".format(e))

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("返回内容不是合法 JSON:\n" + text[:500])


def pretty_print(data, longitude, latitude):
    """对返回结果做友好展示。"""
    print("=" * 52)
    print(" 请求坐标: longitude={}, latitude={}".format(longitude, latitude))
    print("=" * 52)

    # 顶层状态
    status = data.get("status")
    if str(status) != "1":
        print("[!] 接口返回状态异常: status={}".format(status))
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    d = data.get("data", {})

    def g(key, default="-"):
        return d.get(key, default)

    print("国家    :", g("country"))
    print("省份    :", g("province"), "(adcode:", g("provinceadcode"), ")")
    print("城市    :", g("city"), "(adcode:", g("cityadcode"), ")")
    print("区县    :", g("district"), "(adcode:", g("districtadcode"), ")")
    print("完整描述:", g("desc"))
    print("区号    :", g("areacode"), " 电话区号:", g("tel"))

    roads = d.get("road_list") or []
    print("周边道路: 共 {} 条".format(len(roads)))
    for i, road in enumerate(roads[:5], 1):
        print("  {}. {:<12} 方向{:<10} 距离{}米 ({}°N, {}°E)".format(
            i,
            road.get("name", ""),
            road.get("direction", ""),
            road.get("distance", ""),
            road.get("latitude", ""),
            road.get("longitude", ""),
        ))
    if len(roads) > 5:
        print("  ... 其余 {} 条省略".format(len(roads) - 5))


def main():
    ap = argparse.ArgumentParser(
        description="高德逆地理编码(regeo)接口请求脚本")
    ap.add_argument("-l", "--longitude", default="121.049",
                    help="经度, 默认 121.049")
    ap.add_argument("-t", "--latitude", default="31.315",
                    help="纬度, 默认 31.315")
    ap.add_argument("--raw", action="store_true",
                    help="只打印原始 JSON 整段")
    ap.add_argument("-o", "--output",
                    help="把返回的 JSON 保存到指定文件")
    args = ap.parse_args()
    long = input("经度：" )
    lati = input("纬度：" )
    try:
        data = regeo(long, lati)
    except RuntimeError as e:
        print("[错误] {}".format(e), file=sys.stderr)
        sys.exit(1)

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        pretty_print(data, args.longitude, args.latitude)
        print("\n--- 原始 JSON ---")
        print(json.dumps(data, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n已保存到:", args.output)


if __name__ == "__main__":
    main()
