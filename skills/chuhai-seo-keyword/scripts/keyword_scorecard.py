# -*- coding: utf-8 -*-
"""Keyword feasibility scorecard for overseas SEO / 建站决策.

Encodes the empirical rules from the Web.Cafe corpus (2024-2026). All numbers are
community heuristics, NOT Google formulas. GSC measured data always wins.

Usage:
  python keyword_scorecard.py --keyword "ai face swap" --volume-daily 20000 \
      --kd 55 --kgr 0.2 --cpc 1.2 --serp-innerpages 7 --serp-homepages 3 \
      --dr-max 38 --trend rising --stage new
  python keyword_scorecard.py --demo
  python keyword_scorecard.py ... --json
"""
import argparse, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# KD -> approx. referring domains needed to reach top10 [id=106, 经验估算]
KD_REF = {0: 0, 10: 10, 20: 22, 30: 36, 40: 56, 50: 84, 60: 129, 70: 202, 80: 353, 90: 500}
# position -> CTR baseline [id=106, 行业聚合均值]
CTR = {1: 0.30, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 6: 0.03, 7: 0.025, 8: 0.025, 9: 0.02, 10: 0.02, 15: 0.01}


def kd_to_refs(kd):
    ks = sorted(KD_REF)
    if kd <= ks[0]:
        return KD_REF[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if a <= kd <= b:
            r = (kd - a) / float(b - a)
            return round(KD_REF[a] + r * (KD_REF[b] - KD_REF[a]))
    return KD_REF[ks[-1]]


def interp_ctr(pos):
    if pos in CTR:
        return CTR[pos]
    ks = sorted(CTR)
    for a, b in zip(ks, ks[1:]):
        if a <= pos <= b:
            r = (pos - a) / float(b - a)
            return CTR[a] + r * (CTR[b] - CTR[a])
    return 0.01


def evaluate(a):
    vol = a.volume_monthly or (a.volume_daily * 30.4 if a.volume_daily else 0)
    daily = vol / 30.4 if vol else 0
    kgr = a.kgr
    if kgr is None and a.intitle is not None and vol:
        kgr = a.intitle / vol
    refs = kd_to_refs(a.kd) if a.kd is not None else None

    reasons, blockers, positives, cautions = [], [], [], []
    score = 0

    # --- hard blockers ---
    if a.trend in ("fad", "seasonal"):
        blockers.append("趋势为%s：热度不可持续（昙花一现/季节词），追上去也拿不到长期流量 [id=893]" % a.trend)
    if a.brand_or_news:
        blockers.append("品牌名/公司名/新闻事件词：不能注册域名建站（会被视为假冒官网），只能做媒体专题 [id=47]")
    if vol and vol < 1000 and not a.high_ticket:
        blockers.append("月搜索量 %d < 1000：即使排第一，日流量也支撑不了变现 [id=893]" % vol)
    if kgr is not None and kgr > 1.0:
        blockers.append("KGR %.2f > 1.0：网页供应量过大（多为老词），新人版 SOP 判弃 [id=106]" % kgr)
    if a.dr_max and a.dr_max >= 40 and a.strict:
        blockers.append("SERP 前 10 最高 DR %d >= 40：新人版 SOP 视为够不着 [id=106]（哥飞原文更宽松，见 cautions）" % a.dr_max)
    if a.official and a.strict:
        blockers.append("前 10 含厂商官方页/大平台/垂类权威站：新人版 SOP 判弃 [id=106]")

    # --- positives ---
    if a.trend in ("new", "rising"):
        score += 2
        positives.append("趋势 %s：新词窗口，高权重站未及覆盖，新站超车机会 [id=893][id=300]" % a.trend)
    if a.word_age_months is not None and a.word_age_months < 6:
        score += 1
        positives.append("词龄 < 6 个月：符合「刚出现不到半年的新词」最佳切入点 [id=893]")
    inner = a.serp_innerpages or 0
    home = a.serp_homepages or 0
    if inner >= 6:
        score += 2
        positives.append("前 10 有 %d 个大站内页：可注册 EMD 用首页打内页（田忌赛马），权重更集中 [id=893][id=47]" % inner)
    elif inner >= 4:
        score += 1
        positives.append("前 10 内页 %d 个：内页居多偏向可做，但需逐个人肉看 SERP" % inner)
    if home >= 7:
        score -= 2
        cautions.append("前 10 首页占 %d 个：多是同行整站 All-in 该词，正面硬碰，新站劣势 [id=47]" % home)
    if a.serp_weak and a.serp_weak >= 3:
        score += 2
        positives.append("前 3 有 %d 个低 DR/弱站占位：说明门槛低 [id=893]" % a.serp_weak)
    if a.kd is not None:
        if a.kd <= 20:
            score += 2
            positives.append("KD %d 低：约需 %d 个引荐域可进前 10" % (a.kd, refs))
        elif a.kd <= 50:
            score += 1
            positives.append("KD %d 中等：约需 %d 个引荐域，配合产品力与用户体验可做" % (a.kd, refs))
        elif a.kd <= 70:
            score -= 1
            cautions.append("KD %d 偏高（约需 %d 引荐域）：2024 年后哥飞已把 KD 50~70、日搜索量 10 万以内的词列入可做范围，但要预留 3~5 个月和外链预算 [id=3]" % (a.kd, refs))
        else:
            score -= 3
            cautions.append("KD %d 很高（约需 %d 引荐域）：除非有外链资源与老站权重，否则放弃 [id=893][id=106]" % (a.kd, refs))
    if kgr is not None and kgr < 0.25:
        score += 2
        positives.append("KGR %.3f < 0.25 优：网页供应量小，即使 KD 高也可能靠用户体验和举全站之力拿下 [id=79][id=940]" % kgr)
    elif kgr is not None and kgr <= 1.0:
        cautions.append("KGR %.3f 在 0.25~1.0 中等档：适合已有长尾词进前 10、DR 10+ 的扩张期站点，纯新站建议先做 KGR < 0.25 的词 [id=932]" % kgr)
    if a.cpc is not None:
        if a.cpc >= 1.0:
            score += 2
            positives.append("CPC $%.2f：商业价值高，AdSense / 付费转化都好算账 [id=893]" % a.cpc)
        elif a.cpc >= 0.1:
            score += 1
            positives.append("CPC $%.2f：及格线以上（> $0.1）" % a.cpc)
        else:
            score -= 2
            cautions.append("CPC $%.3f 极低：流量不值钱，除非有订阅/高客单变现，否则收入惨淡 [id=893]" % a.cpc)
    if a.volume_daily and a.volume_daily <= 100000:
        positives.append("日搜索量 %d 在「10 万以内」区间：即使只吃一小块也够精准变现 [id=3]" % a.volume_daily)
    if a.stage == "new" and refs and refs > 120:
        score -= 1
        cautions.append("新站 + 约需 %d 个引荐域：外链投入大，建议先用老站内页试水 [id=76]" % refs)

    # --- reachable traffic & revenue ---
    traffic = {}
    if vol:
        for label, pos in (("保守(#8)", 8), ("中性(#5)", 5), ("乐观(#2)", 2)):
            uv = vol * interp_ctr(pos)
            traffic[label] = {
                "position": pos,
                "monthly_uv": round(uv),
                "monthly_adsense_usd": round(uv * a.pv_per_uv * (a.rpm or 0) / 1000.0, 1),
            }

    # --- verdict ---
    if blockers:
        verdict = "不做 / 换词"
    elif score >= 5 and (inner >= 6 or (a.kd is not None and a.kd <= 30)):
        verdict = "做（可注册域名单独建站）"
    elif score >= 2:
        verdict = "慎做（先用老站内页验证，再决定是否单独建站）" if a.stage == "new" else "可做（需配资源与迭代周期）"
    elif score >= 0:
        verdict = "先做内页验证"
    else:
        verdict = "不做 / 换词"

    next_steps = []
    if verdict.startswith("做"):
        next_steps = [
            "人肉搜一次该词，逐条记录前 10：首页/内页、域名注册时间、DR、引荐域数、页面质量、是否官方页 [id=47]",
            "Similarweb 看排名内页实际流量，Ahrefs 看前三名页面外链，算「流量 ÷ 外链数」的投入产出 [id=47]",
            "用 Google Trends 对比同义/单复数词形，确认真正的用户搜索词，避免优化错词 [id=893]",
            "确认可用 EMD 域名后，用首页 All-in 该词，正文做词形落位 + 内链合围 [id=79][id=321]",
            "上线后 1~4 周冻结 TDH，等 GSC 出实测数据再改 [id=106]",
        ]
    elif "内页" in verdict:
        next_steps = [
            "先在已有站做一个内页满足该需求，观察 2~4 周 GSC 曝光/出词与 ChatGPT 推荐流量 [id=76]",
            "同时用 Google Trends 持续看 5 天以上同向趋势再决定是否投入 [id=106]",
            "若内页能出词且点击稳定，再注册域名单独建站并用首页打",
        ]
    else:
        next_steps = ["回到找词环节（见 references/02-sourcing.md），用赢家反推法换一批候选词"]

    kdroi = None
    if vol and a.cpc is not None and a.kd:
        kdroi = round(vol * a.cpc / a.kd, 1)
        cautions.append("KDRoi = 搜索量 × CPC ÷ KD = %.1f（仅用于多个候选词横向排序，绝对值无意义）[id=792][id=893]" % kdroi)

    return {
        "keyword": a.keyword,
        "verdict": verdict,
        "score": score,
        "inputs": {"monthly_volume": round(vol), "daily_volume": round(daily), "kd": a.kd,
                   "kgr": round(kgr, 4) if kgr is not None else None, "cpc": a.cpc,
                   "kdroi": kdroi, "rpm": a.rpm, "pv_per_uv": a.pv_per_uv,
                   "approx_referring_domains_for_top10": refs, "stage": a.stage},
        "blockers": blockers,
        "positives": positives,
        "cautions": cautions,
        "traffic_estimate": traffic,
        "next_steps": next_steps,
        "disclaimer": "阈值为社群经验值（2024-2026，观点有演进）；KD→引荐域、位次 CTR 均为估算，非 Google 公式。上线后一律以 GSC 实测为准。",
    }


def show(r):
    print("\n" + "=" * 70)
    print("关键词评估：%s" % r["keyword"])
    print("结论：%s   （内部打分 %+d）" % (r["verdict"], r["score"]))
    print("=" * 70)
    i = r["inputs"]
    print("\n[输入与换算] 月搜索量≈%s / 日≈%s | KD=%s | KGR=%s | KDRoi=%s | CPC=%s | 进前10约需引荐域≈%s | 站点阶段=%s" %
          (i["monthly_volume"], i["daily_volume"], i["kd"], i["kgr"], i["kdroi"], i["cpc"],
           i["approx_referring_domains_for_top10"], i["stage"]))
    for label, lines in (("[否决项]", r["blockers"]), ("[可做信号]", r["positives"]), ("[风险与冲突]", r["cautions"])):
        if lines:
            print("\n%s" % label)
            for x in lines:
                print("  - " + x)
    if r["traffic_estimate"]:
        print("\n[流量与 Adsense 粗估]（位次 CTR 基线；RPM=$%s，PV/UV=%s）" % (i["rpm"], i["pv_per_uv"]))
        for k, v in r["traffic_estimate"].items():
            print("  %-10s 月 UV≈%-9s 月广告收入≈$%s" % (k, v["monthly_uv"], v["monthly_adsense_usd"]))
    print("\n[下一步]")
    for n, s in enumerate(r["next_steps"], 1):
        print("  %d. %s" % (n, s))
    print("\n注：%s\n" % r["disclaimer"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyword", default="(未命名关键词)")
    ap.add_argument("--volume-monthly", type=float)
    ap.add_argument("--volume-daily", type=float)
    ap.add_argument("--kd", type=float)
    ap.add_argument("--kgr", type=float, help="KGR = intitle 结果数 / 月搜索量")
    ap.add_argument("--intitle", type=float, help="Google intitle: 结果数，配合月搜索量自动算 KGR")
    ap.add_argument("--cpc", type=float)
    ap.add_argument("--rpm", type=float, default=8.0)
    ap.add_argument("--pv-per-uv", type=float, default=1.5)
    ap.add_argument("--serp-homepages", type=int, default=0, help="SERP 前10 中首页数量")
    ap.add_argument("--serp-innerpages", type=int, default=0, help="SERP 前10 中大站内页数量")
    ap.add_argument("--serp-weak", type=int, default=0, help="前3 中低 DR 弱站数量")
    ap.add_argument("--dr-max", type=float, help="SERP 前10 最高 DR")
    ap.add_argument("--official", action="store_true", help="前10 含官方页/大平台")
    ap.add_argument("--trend", choices=["new", "rising", "flat", "seasonal", "fad", "decaying"], default="flat")
    ap.add_argument("--word-age-months", type=float)
    ap.add_argument("--stage", choices=["new", "growing", "authority"], default="new")
    ap.add_argument("--ref-domains", type=int, default=0, help="自己站点现有引荐域数")
    ap.add_argument("--brand-or-news", action="store_true")
    ap.add_argument("--high-ticket", action="store_true", help="高客单价 B2B，可放宽搜索量底线")
    ap.add_argument("--strict", action="store_true", help="启用新人版 SOP 硬红线（DR>=40 / 官方页即弃）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        a = ap.parse_args(["--keyword", "ai face swap", "--volume-daily", "20000", "--kd", "55",
                           "--kgr", "0.2", "--cpc", "1.2", "--serp-innerpages", "7",
                           "--serp-homepages", "3", "--dr-max", "38", "--trend", "rising",
                           "--word-age-months", "4", "--stage", "new"])
    r = evaluate(a)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        show(r)


if __name__ == "__main__":
    main()
