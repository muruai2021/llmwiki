import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { X, MessageSquare } from "lucide-react";
import { CITIES, CITY_BY_SLUG, type CityMeta } from "../data/cities";
import { useCompareStore, COMPARE_MAX } from "../store/useCompareStore";
import { useChatStore } from "../store/useChatStore";

const ATTRIBUTES: { label: string; render: (c: CityMeta) => string }[] = [
  { label: "区域", render: (c) => c.region },
  { label: "省/直辖市", render: (c) => c.province },
  { label: "行政等级", render: (c) => c.tier },
  { label: "标签", render: (c) => c.tags.join("、") },
  { label: "一句话简介", render: (c) => c.tagline },
];

export function ComparePage() {
  const slugs = useCompareStore((s) => s.slugs);
  const add = useCompareStore((s) => s.add);
  const remove = useCompareStore((s) => s.remove);
  const clear = useCompareStore((s) => s.clear);
  const cities = slugs.map((s) => CITY_BY_SLUG[s]).filter(Boolean);
  const candidates = CITIES.filter((c) => !slugs.includes(c.slug));
  const [pickerOpen, setPickerOpen] = useState(false);

  return (
    <div className="compare-page">
      <div className="sec-num">§ 003 · TERMINAL</div>
      <h1 className="sec-title">城市对比</h1>
      <p className="sec-sub">
        最多 {COMPARE_MAX} 城并排比较。点详情页"加入对比"，或在这里直接选。
      </p>

      <div className="term-grid">
        <aside className="term-sidebar">
          <h3>对比列表</h3>
          <div className="hint">CITIES · {COMPARE_MAX} MAX</div>
          <div className="count">{cities.length} / {COMPARE_MAX} SELECTED</div>

          <div className="term-list">
            {cities.length === 0 && (
              <div style={{ color: "var(--mute-2)", fontSize: 12, fontFamily: "var(--mono)", letterSpacing: ".06em", padding: 8 }}>
                （未选）
              </div>
            )}
            {cities.map((c) => (
              <div key={c.slug} className="term-chip on">
                <span className="nm">{c.name}</span>
                <span className="rm" onClick={() => remove(c.slug)} title="移除">
                  <X size={11} />
                </span>
              </div>
            ))}
          </div>

          <div className="term-actions">
            {cities.length < COMPARE_MAX && (
              <>
                <button
                  type="button"
                  className="term-btn"
                  onClick={() => setPickerOpen((v) => !v)}
                >
                  {pickerOpen ? "关闭选择" : "+ 添加城市"}
                </button>
                {pickerOpen && (
                  <select
                    className="term-btn"
                    style={{ appearance: "none", cursor: "pointer" }}
                    onChange={(e) => {
                      if (e.target.value) {
                        add(e.target.value);
                        e.target.value = "";
                      }
                    }}
                    defaultValue=""
                  >
                    <option value="" disabled>— 选一个 —</option>
                    {candidates.map((c) => (
                      <option key={c.slug} value={c.slug}>
                        {c.name}（{c.region}）
                      </option>
                    ))}
                  </select>
                )}
              </>
            )}
            {cities.length > 0 && (
              <button type="button" className="term-btn" onClick={clear}>
                清空
              </button>
            )}
          </div>
        </aside>

        <section className="term-main">
          {cities.length === 0 ? (
            <div className="term-empty">
              <div className="icon">⊕</div>
              <p>还没选城市</p>
              <span>点上面"+ 添加城市"或详情页"加入对比"</span>
            </div>
          ) : (
            <table className="term-table">
              <thead>
                <tr>
                  <th>维度</th>
                  {cities.map((c, i) => (
                    <th key={c.slug} className={i === 0 ? "featured" : ""}>{c.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ATTRIBUTES.map((row) => (
                  <tr key={row.label}>
                    <td>{row.label}</td>
                    {cities.map((c) => (
                      <td key={c.slug}>{row.render(c)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      {cities.length > 0 && <AskChatButton cities={cities} />}
    </div>
  );
}

function AskChatButton({ cities }: { cities: CityMeta[] }) {
  const navigate = useNavigate();
  const sendMessage = useChatStore((s) => s.sendMessage);
  const onClick = async () => {
    const names = cities.map((c) => c.name);
    const question =
      names.length === 2
        ? `对比 ${names[0]} 和 ${names[1]} 的招商政策差异（人才/税收/产业/区域）`
        : `对比 ${names.slice(0, -1).join("、")} 和 ${names[names.length - 1]} 的招商政策差异`;
    await sendMessage(question);
    navigate("/chat");
  };
  return (
    <div className="compare-ask-chat">
      <button type="button" className="ask-btn" onClick={onClick}>
        <MessageSquare size={12} /> 让 AI 对比这些城市 →
      </button>
      <span className="hint">跳转到 chat 并自动发送对比问句</span>
    </div>
  );
}
