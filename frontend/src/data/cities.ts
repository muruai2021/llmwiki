// 50 城元数据 — 招商政策知识库覆盖范围。
// 字段来源：wiki/index.md 的城市条目 + 行政区划常识。
// 不与后端耦合；详情正文走 /api/vault/file。

export type Region =
  | "华北"
  | "东北"
  | "华东"
  | "华中"
  | "华南"
  | "西南"
  | "西北"
  | "海南"
  | "港澳";

export type Tier =
  | "直辖市"
  | "特别行政区"
  | "省会"
  | "副省级"
  | "计划单列"
  | "地级市"
  | "国家级新区";

export interface CityMeta {
  /** URL / 文件名 slug */
  slug: string;
  /** 显示名（与 slug 一致；为可读性显式列出） */
  name: string;
  /** 所属省 / 直辖市 / 特别行政区 */
  province: string;
  /** 7+1 区域 */
  region: Region;
  /** 城市行政等级 */
  tier: Tier;
  /** 政策/产业标签（用于筛选/搜索） */
  tags: string[];
  /** 一句话简介（来自 wiki/index.md 或常识） */
  tagline: string;
}

export const CITIES: CityMeta[] = [
  // ----- 海南（自贸港） -----
  { slug: "三亚市", name: "三亚市", province: "海南", region: "海南", tier: "地级市",
    tags: ["自贸港", "旅游", "免税"], tagline: "自贸港核心城市" },
  { slug: "海口市", name: "海口市", province: "海南", region: "海南", tier: "省会",
    tags: ["自贸港", "省会", "总部经济"], tagline: "海南省省会、自贸港核心城市" },

  // ----- 港澳 -----
  { slug: "香港特别行政区", name: "香港特别行政区", province: "香港", region: "港澳", tier: "特别行政区",
    tags: ["金融中心", "自由港", "普通法"], tagline: "全球第 3 大金融中心、自由港、普通法" },
  { slug: "澳门特别行政区", name: "澳门特别行政区", province: "澳门", region: "港澳", tier: "特别行政区",
    tags: ["中葡平台", "博彩", "横琴合作区"], tagline: "中葡平台、博彩 35%、单独关税区" },

  // ----- 直辖市 -----
  { slug: "北京市", name: "北京市", province: "北京", region: "华北", tier: "直辖市",
    tags: ["政治中心", "科创", "央企总部"], tagline: "政治/文化/国际交往/科技创新中心" },
  { slug: "上海市", name: "上海市", province: "上海", region: "华东", tier: "直辖市",
    tags: ["金融", "自贸区", "长三角龙头"], tagline: "长三角龙头城市" },
  { slug: "重庆市", name: "重庆市", province: "重庆", region: "西南", tier: "直辖市",
    tags: ["西部中心", "成渝双城", "西部大开发"], tagline: "西部中心、成渝双城、西部大开发" },
  { slug: "天津市", name: "天津市", province: "天津", region: "华北", tier: "直辖市",
    tags: ["京津冀", "自贸试验区", "北方航运"], tagline: "京津冀、自贸试验区、北方航运" },

  // ----- 华南（广东 + 广西 + 海南已在上面） -----
  { slug: "深圳市", name: "深圳市", province: "广东", region: "华南", tier: "副省级",
    tags: ["大湾区核心", "前海", "高新制造"], tagline: "粤港澳大湾区核心城市" },
  { slug: "广州市", name: "广州市", province: "广东", region: "华南", tier: "省会",
    tags: ["大湾区核心", "南沙自贸区", "省会"], tagline: "粤港澳大湾区核心城市" },
  { slug: "东莞市", name: "东莞市", province: "广东", region: "华南", tier: "地级市",
    tags: ["大湾区", "先进制造", "电子信息"], tagline: "粤港澳大湾区先进制造业基地" },
  { slug: "佛山市", name: "佛山市", province: "广东", region: "华南", tier: "地级市",
    tags: ["大湾区", "制造业名城", "工业上楼"], tagline: "粤港澳大湾区、制造业名城" },
  { slug: "珠海市", name: "珠海市", province: "广东", region: "华南", tier: "地级市",
    tags: ["经济特区", "大湾区", "横琴合作区"], tagline: "经济特区、粤港澳大湾区" },
  { slug: "汕头市", name: "汕头市", province: "广东", region: "华南", tier: "地级市",
    tags: ["经济特区", "华侨之乡", "粤东中心"], tagline: "5 经济特区之一（唯一缺）、粤东中心、华侨之乡" },
  { slug: "南宁市", name: "南宁市", province: "广西", region: "华南", tier: "省会",
    tags: ["东盟永久会址", "北部湾", "省会"], tagline: "广西省会、东盟永久会址、北部湾核心" },

  // ----- 华东（江浙 + 闽皖赣 + 山东 + 沪已在上面） -----
  { slug: "苏州市", name: "苏州市", province: "江苏", region: "华东", tier: "地级市",
    tags: ["长三角核心", "苏州工业园区", "半导体"], tagline: "长三角核心城市" },
  { slug: "南京市", name: "南京市", province: "江苏", region: "华东", tier: "省会",
    tags: ["江苏省会", "长三角创新", "紫金山"], tagline: "江苏省省会、长三角创新中心" },
  { slug: "无锡市", name: "无锡市", province: "江苏", region: "华东", tier: "地级市",
    tags: ["长三角几何中心", "IC 产业", "高新区"], tagline: "长三角几何中心、IC 产业" },
  { slug: "杭州市", name: "杭州市", province: "浙江", region: "华东", tier: "省会",
    tags: ["数字经济第一城", "长三角核心", "电商"], tagline: "长三角核心城市、数字经济第一城" },
  { slug: "宁波市", name: "宁波市", province: "浙江", region: "华东", tier: "计划单列",
    tags: ["计划单列市", "全球第一大港", "前湾新区"], tagline: "计划单列市、全球第一大港" },
  { slug: "温州市", name: "温州市", province: "浙江", region: "华东", tier: "地级市",
    tags: ["民营经济发源地", "温州湾新区", "金融人才"], tagline: "中国民营经济发源地、温州湾新区" },
  { slug: "厦门市", name: "厦门市", province: "福建", region: "华东", tier: "计划单列",
    tags: ["经济特区", "对台贸易", "计划单列"], tagline: "经济特区、计划单列市、对台贸易" },
  { slug: "福州市", name: "福州市", province: "福建", region: "华东", tier: "省会",
    tags: ["对台合作", "省会", "海上丝路"], tagline: "福建省会、对台合作窗口、海上丝路" },
  { slug: "泉州市", name: "泉州市", province: "福建", region: "华东", tier: "地级市",
    tags: ["福建第一城", "21 世纪海上丝路", "闽南"], tagline: "福建第一城、21 世纪海上丝路起点、闽南" },
  { slug: "合肥市", name: "合肥市", province: "安徽", region: "华东", tier: "省会",
    tags: ["长三角副中心", "国家科学中心", "科大硅谷"], tagline: "长三角副中心、综合性国家科学中心" },
  { slug: "南昌市", name: "南昌市", province: "江西", region: "华东", tier: "省会",
    tags: ["省会", "鄱阳湖生态", "VR 产业"], tagline: "江西省会、鄱阳湖生态经济区核心" },
  { slug: "青岛市", name: "青岛市", province: "山东", region: "华东", tier: "计划单列",
    tags: ["计划单列市", "海洋经济", "西海岸新区"], tagline: "计划单列市、海洋经济" },
  { slug: "济南市", name: "济南市", province: "山东", region: "华东", tier: "副省级",
    tags: ["省会", "黄河战略", "起步区"], tagline: "山东省会、黄河战略核心、副省级" },
  { slug: "烟台市", name: "烟台市", province: "山东", region: "华东", tier: "地级市",
    tags: ["山东第二城", "海洋经济", "中韩合作"], tagline: "山东第二城、海洋经济、中韩合作" },

  // ----- 华中（豫鄂湘） -----
  { slug: "郑州市", name: "郑州市", province: "河南", region: "华中", tier: "省会",
    tags: ["中部交通枢纽", "国家中心城市", "航空港"], tagline: "中部交通枢纽、国家中心城市" },
  { slug: "武汉市", name: "武汉市", province: "湖北", region: "华中", tier: "副省级",
    tags: ["中部崛起核心", "光谷", "长江中游"], tagline: "中部崛起核心城市" },
  { slug: "长沙市", name: "长沙市", province: "湖南", region: "华中", tier: "省会",
    tags: ["长株潭都市圈", "智能制造", "省会"], tagline: "长株潭都市圈核心" },

  // ----- 华北（北京/天津/河北/山西/内蒙古） — 北京天津已在直辖市 -----
  { slug: "石家庄市", name: "石家庄市", province: "河北", region: "华北", tier: "省会",
    tags: ["省会", "京津冀节点", "雄安联动"], tagline: "河北省会、京津冀重要节点" },
  { slug: "唐山市", name: "唐山市", province: "河北", region: "华北", tier: "地级市",
    tags: ["河北第一城", "京津冀", "曹妃甸"], tagline: "河北第一城、京津冀重要节点、曹妃甸" },
  { slug: "太原市", name: "太原市", province: "山西", region: "华北", tier: "省会",
    tags: ["省会", "能源革命", "转型综改区"], tagline: "山西省会、能源革命综合改革试点" },
  { slug: "呼和浩特市", name: "呼和浩特市", province: "内蒙古", region: "华北", tier: "省会",
    tags: ["中蒙俄走廊", "和林格尔新区", "省会"], tagline: "内蒙古首府、中蒙俄经济走廊重要节点" },

  // ----- 东北（辽吉黑） -----
  { slug: "沈阳市", name: "沈阳市", province: "辽宁", region: "东北", tier: "省会",
    tags: ["东北中心", "装备制造", "东北振兴"], tagline: "东北中心、装备制造" },
  { slug: "大连市", name: "大连市", province: "辽宁", region: "东北", tier: "计划单列",
    tags: ["东北亚航运中心", "东北振兴", "金普新区"], tagline: "东北亚航运中心、东北振兴" },
  { slug: "长春市", name: "长春市", province: "吉林", region: "东北", tier: "省会",
    tags: ["中国汽车摇篮", "省会", "东北振兴"], tagline: "吉林省会、中国汽车工业摇篮" },
  { slug: "哈尔滨市", name: "哈尔滨市", province: "黑龙江", region: "东北", tier: "省会",
    tags: ["对俄远东", "省会", "哈尔滨新区"], tagline: "黑龙江省会、对俄远东门户" },

  // ----- 西北（陕甘宁青新） -----
  { slug: "西安市", name: "西安市", province: "陕西", region: "西北", tier: "副省级",
    tags: ["丝绸之路核心", "硬科技之都", "西咸新区"], tagline: "丝绸之路核心城市、硬科技之都" },
  { slug: "兰州市", name: "兰州市", province: "甘肃", region: "西北", tier: "省会",
    tags: ["丝路经济带", "省会", "兰州新区"], tagline: "甘肃省会、丝绸之路经济带核心节点" },
  { slug: "银川市", name: "银川市", province: "宁夏", region: "西北", tier: "省会",
    tags: ["内陆开放型", "省会", "中阿博览会"], tagline: "宁夏首府、内陆开放型经济试验区核心" },
  { slug: "西宁市", name: "西宁市", province: "青海", region: "西北", tier: "省会",
    tags: ["清洁能源", "省会", "盐湖化工"], tagline: "青海省会、国家清洁能源示范省核心" },
  { slug: "乌鲁木齐市", name: "乌鲁木齐市", province: "新疆", region: "西北", tier: "省会",
    tags: ["丝路核心区", "省会", "中亚合作"], tagline: "新疆首府、丝绸之路经济带核心区首要节点" },

  // ----- 西南（川渝黔滇藏）— 重庆已在直辖市 -----
  { slug: "成都市", name: "成都市", province: "四川", region: "西南", tier: "副省级",
    tags: ["成渝双城核心", "高新区", "天府新区"], tagline: "成渝双城经济圈核心" },
  { slug: "贵阳市", name: "贵阳市", province: "贵州", region: "西南", tier: "省会",
    tags: ["大数据中心", "省会", "东数西算"], tagline: "贵州省会、大数据中心、东数西算枢纽" },
  { slug: "昆明市", name: "昆明市", province: "云南", region: "西南", tier: "省会",
    tags: ["南亚东南亚门户", "省会", "滇中新区"], tagline: "西南省会、面向南亚东南亚" },
  { slug: "拉萨市", name: "拉萨市", province: "西藏", region: "西南", tier: "省会",
    tags: ["南亚开放前沿", "省会", "15% 所得税"], tagline: "西藏首府、面向南亚开放前沿" },

  // ----- 国家级新区（独立条目） -----
  { slug: "雄安新区", name: "雄安新区", province: "河北", region: "华北", tier: "国家级新区",
    tags: ["千年大计", "央企二总部", "15% 双封顶"], tagline: "千年大计、北京非首都功能疏解集中承载地" },
];

/** 区域列表（用于筛选器 / 导航） */
export const REGIONS: Region[] = [
  "海南", "港澳", "华东", "华南", "华中", "华北", "东北", "西南", "西北",
];

/** 按区域索引城市 */
export const CITIES_BY_REGION: Record<Region, CityMeta[]> = REGIONS.reduce(
  (acc, r) => {
    acc[r] = CITIES.filter((c) => c.region === r);
    return acc;
  },
  {} as Record<Region, CityMeta[]>,
);

/** slug → CityMeta 索引（O(1) 查） */
export const CITY_BY_SLUG: Record<string, CityMeta> = CITIES.reduce(
  (acc, c) => {
    acc[c.slug] = c;
    return acc;
  },
  {} as Record<string, CityMeta>,
);
