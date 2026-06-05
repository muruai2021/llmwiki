import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CITIES, REGIONS, type CityMeta, type Region } from "../data/cities";

type TierFilter = "all" | "省级+" | "新区";

// Hardcoded coordinates for the 50 cities — same format as the 18°N index.html hero.
const COORDS: Record<string, string> = {
  "三亚市": "18°14′N · 109°31′E",
  "海口市": "20°02′N · 110°20′E",
  "香港特别行政区": "22°18′N · 114°10′E",
  "澳门特别行政区": "22°11′N · 113°32′E",
  "北京市": "39°54′N · 116°23′E",
  "上海市": "31°14′N · 121°29′E",
  "重庆市": "29°33′N · 106°33′E",
  "天津市": "39°08′N · 117°11′E",
  "深圳市": "22°33′N · 114°05′E",
  "广州市": "23°08′N · 113°16′E",
  "东莞市": "23°02′N · 113°43′E",
  "佛山市": "23°01′N · 113°07′E",
  "珠海市": "22°16′N · 113°34′E",
  "汕头市": "23°21′N · 116°40′E",
  "南宁市": "22°49′N · 108°22′E",
  "苏州市": "31°18′N · 120°37′E",
  "南京市": "32°03′N · 118°46′E",
  "无锡市": "31°34′N · 120°18′E",
  "杭州市": "30°16′N · 120°09′E",
  "宁波市": "29°52′N · 121°33′E",
  "温州市": "27°59′N · 120°40′E",
  "厦门市": "24°28′N · 118°05′E",
  "福州市": "26°04′N · 119°18′E",
  "泉州市": "24°52′N · 118°40′E",
  "合肥市": "31°49′N · 117°13′E",
  "南昌市": "28°41′N · 115°52′E",
  "青岛市": "36°04′N · 120°22′E",
  "济南市": "36°39′N · 117°01′E",
  "烟台市": "37°32′N · 121°24′E",
  "郑州市": "34°45′N · 113°37′E",
  "武汉市": "30°35′N · 114°17′E",
  "长沙市": "28°13′N · 112°56′E",
  "石家庄市": "38°02′N · 114°30′E",
  "唐山市": "39°37′N · 118°10′E",
  "太原市": "37°52′N · 112°34′E",
  "呼和浩特市": "40°48′N · 111°41′E",
  "沈阳市": "41°48′N · 123°25′E",
  "大连市": "38°56′N · 121°37′E",
  "长春市": "43°53′N · 125°19′E",
  "哈尔滨市": "45°48′N · 126°32′E",
  "西安市": "34°16′N · 108°56′E",
  "兰州市": "36°03′N · 103°49′E",
  "银川市": "38°27′N · 106°13′E",
  "西宁市": "36°37′N · 101°46′E",
  "乌鲁木齐市": "43°49′N · 87°36′E",
  "成都市": "30°34′N · 104°04′E",
  "贵阳市": "26°38′N · 106°42′E",
  "昆明市": "24°52′N · 102°42′E",
  "拉萨市": "29°39′N · 91°07′E",
  "雄安新区": "39°00′N · 115°58′E",
};

export function CitiesGridPage() {
  const [region, setRegion] = useState<"all" | Region>("all");
  const [tier, setTier] = useState<TierFilter>("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    return CITIES.filter((c) => {
      if (region !== "all" && c.region !== region) return false;
      if (tier === "省级+" && !["直辖市", "特别行政区", "省会", "副省级", "计划单列"].includes(c.tier)) return false;
      if (tier === "新区" && c.tier !== "国家级新区") return false;
      if (query) {
        const q = query.toLowerCase();
        const hay = `${c.name} ${c.province} ${c.tagline} ${c.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [region, tier, query]);

  return (
    <div className="cities-page">
      <div className="sec-num">§ 002 · CITIES</div>
      <h1 className="sec-title">50 城</h1>
      <p className="sec-sub">
        覆盖 {CITIES.length} 城 / {REGIONS.length} 个区域。点击进入城市详情，或加入对比。
      </p>

      <div className="cities-filters">
        <span>区域：</span>
        {(["all", ...REGIONS] as const).map((v) => (
          <button
            key={v}
            type="button"
            className={`filter-chip ${region === v ? "active" : ""}`}
            onClick={() => setRegion(v)}
          >
            {v === "all" ? "全部" : v}
          </button>
        ))}
        <span style={{ marginLeft: 12 }}>等级：</span>
        {(["all", "省级+", "新区"] as const).map((v) => (
          <button
            key={v}
            type="button"
            className={`filter-chip ${tier === v ? "active" : ""}`}
            onClick={() => setTier(v)}
          >
            {v === "all" ? "全部" : v === "省级+" ? "省级+" : "新区"}
          </button>
        ))}
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索城市 / 标签…"
        />
        <span className="cities-count">
          {filtered.length} / {CITIES.length}
        </span>
      </div>

      <div className="cities-grid">
        {filtered.map((c, i) => (
          <CityCard key={c.slug} city={c} index={i} />
        ))}
      </div>

      {filtered.length === 0 && (
        <p style={{ marginTop: 32, color: "var(--mute)", fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase" }}>
          没找到符合条件的城市
        </p>
      )}
    </div>
  );
}

interface CityCardProps {
  city: CityMeta;
  index: number;
}

function CityCard({ city, index }: CityCardProps) {
  const isFeatured = city.slug === "三亚市";
  const coord = COORDS[city.slug] || "—";
  const idx = String(index + 1).padStart(2, "0");
  return (
    <Link
      to={`/cities/${encodeURIComponent(city.slug)}`}
      className={`city-card ${isFeatured ? "featured" : ""}`}
    >
      {isFeatured && <div className="cc-stars">★ 招商旗舰</div>}
      <div className="cc-coord">
        {coord}
        <br />
        {city.province} · CHN
      </div>
      <div className="cc-idx">{idx} · {city.region.toUpperCase()}</div>
      <h3>{city.name}</h3>
      <div className="cc-en">{city.tier} · {city.province}</div>
      <p className="cc-tagline">{city.tagline}</p>
      <div className="cc-tag-row">
        {city.tags.slice(0, 3).map((t) => (
          <span key={t} className="cc-tag">{t}</span>
        ))}
      </div>
    </Link>
  );
}
