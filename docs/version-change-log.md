# 版本变更记录

该文档用于记录每个数字版本号对应的实质更新内容，便于后续回溯、比对和回退。

## 本次修改

说明：本区用于记录尚未分配版本号的未提交改动。待用户给出版本号并准备 Git 时，再将本区内容归档到正式版本条目中。`更新内容` 中的每一条都必须使用 `type: 中文描述` 格式。

- 日期：
- 分支：
- 影响范围：
- 更新内容：
  - `type: 中文描述`
- 验证方式：

## 模板

## 本次修改
- 日期：
- 分支：
- 影响范围：
- 更新内容：
  - `type: 中文描述`
- 验证方式：

## 0.0.0
- 日期：
- 分支：
- 影响范围：
- 更新内容：
  - `type: 中文描述`
- 验证方式：

## 版本记录

## 0.9.5.9
- 日期：`2026-04-08`
- 分支：`main`
- 影响范围：
  - `backend/game/utils/game_state_manager.py`
  - `backend/game/utils/frontend_state_types.py`
  - `frontend/src/views/GameView.vue`
  - `frontend/src/views/SetupView.vue`
  - `frontend/src/stores/gameState.js`
  - `docs/game_state_frontend_mapping.md`
  - `docs/version-change-log.md`
- 更新内容：
  - `fix: 初始阶段状态判断改为直接读取核心 game_state 的 setup_choice_is_completed 与 setup_build_is_completed 标志，避免在最后一次初始建筑摆放的立即子步骤中误显示为初始效果结算。`
  - `fix: 对局页对局状态改为直接根据 gameMeta 标志实时计算显示，不再接受独立 global_status 文案覆盖，确保 setup_choice_is_completed=true 且 setup_build_is_completed=false 时稳定显示初始建筑摆放阶段。`
  - `docs: 同步更新前端状态映射文档中的元信息提取示例，移除基于 action_history 推导初始建筑摆放完成态的旧实现。`
  - `ui: 调整对局页玩家标题栏中的宫殿板块编号圆圈为定宽对齐布局，固定“玩家 x”文本宽度以保证各玩家编号列垂直对齐，并将宫殿圆圈缩小到接近标题文字高度后放置于玩家名与派系胶囊之间。`
  - `ui: 基于 is_got_palace 为宫殿板块缩略圆圈和悬停大图增加激活/未激活状态表现，未激活时在圆圈右上角显示禁用图标，并在大图预览上叠加透明灰色遮罩与禁用图标。`
  - `ui: 将宫殿板块未激活禁用图标改为红色，并进一步压缩“玩家 x”到宫殿板块圆圈之间的预留宽度，使标题栏对齐更紧凑。`
  - `ui: 去除宫殿板块未激活禁用图标外围的额外圆形包裹，仅保留右上角红色禁用图标与大图遮罩中的红色禁用图标。`
  - `ui: 微调宫殿板块未激活禁用图标在标题栏圆圈右上角的位置为略向左下偏移，并将大图遮罩中的禁用图标进一步放大以增强状态识别。`
  - `ui: 轻微增加标题栏中“玩家 x”与宫殿板块圆圈之间的固定预留宽度，缓和两者过近的问题并保持跨玩家垂直对齐。`
  - `ui: 对局页回合助推板在翻面后按当前持有者的 planning_card_id 叠加对应颜色标记，标记固定显示于翻面板块的水平中心与垂直 25% 位置，并随 booster_ids 与规划卡增量更新实时同步。`
  - `ui: 将回合助推板翻面态玩家颜色标记进一步缩小到板面宽度的 30%，避免遮挡背面信息。`
  - `fix: 修正回合助推板翻面态颜色标记被 bonus-cell 通用图片尺寸规则覆盖的问题，改为使用更高优先级的独立尺寸样式。`
  - `ui: 将回合助推板翻面态玩家颜色标记继续上移 3%，使其更贴近翻面图片区上沿。`
  - `ui: 将回合助推板翻面态玩家颜色标记在当前位置基础上放大一倍，板面宽度占比从 30% 提升到 60%。`
  - `ui: 将回合助推板翻面态玩家颜色标记再上移 5% 到 17%，并将宽度从 60% 调整为 50%。`
  - `ui: 将回合助推板翻面态玩家颜色标记宽度调回 60%，并在当前垂直位置基础上整体向左偏移 5%。`
  - `ui: 将回合助推板翻面态玩家颜色标记水平位置向右回调 2%，避免左移过量。`
  - `ui: 将回合助推板翻面态玩家颜色标记再向右微调 0.5%，并继续上移 5% 以贴近翻面图区顶部。`
  - `ui: 将回合助推板翻面态玩家颜色标记垂直位置从 12% 回调到 15%。`
  - `ui: 将标题栏中的 player-name 宽度调整为 3.15rem，并将 player-title 的间距收窄到 3px。`
  - `ui: 初始板块配置弹窗左侧导航的完成对勾改为未完成时仅隐藏可见性但保留占位，避免先后选择派系与宫殿板块时文字发生横向位移，并保持现有布局尺寸不变。`
  - `ui: 对局页玩家标题栏中的宫殿板块徽章在未分配时改为隐藏内容但保留原位宽度，避免派系胶囊贴近“玩家 x”并保持现有标题布局不变。`
  - `feat: 在前端游戏状态 setup 中新增 round_booster_coin_counts，直接统计 game_state.all_available_object_dict['round_booster'][编号].immediate_effect 中精确匹配 ('money', 'get', 1) 的数量，并参与全量与增量同步。`
  - `ui: 对局页正面的回合助推板在右上角叠加金币角标，实时显示该助推板当前累计的 1 金币数量，数量为 0 时不显示。`
  - `docs: 同步更新前端状态映射文档中的 GameSetup 与状态提取示例，补充回合助推板累计金币计数字段与提取逻辑。`
  - `fix: 对局页地图增量更新改为按格子合并 controller、building_id、is_neutral 等主建筑字段后再统一重绘，避免中立塔楼落子时先短暂请求错误的玩家色建筑图片 3-6.png 再被 0-6.png 覆盖。`
- 验证方式：
  - `python -m py_compile backend/game/utils/frontend_state_types.py backend/game/utils/game_state_manager.py`
  - `cd frontend && npm run build`
  - `运行 200 局启动阶段脚本，逐步比对 GameStateManager._extract_meta 与 request.game_state 的 setup 标志，确认两者全程一致。`

## 0.9.5.8
- 日期：`2026-04-08`
- 分支：`main`
- 影响范围：
  - `backend/game/aoi_game/game_engine.py`
  - `backend/game/aoi_game/game_state.py`
  - `backend/game/utils/frontend_state_types.py`
  - `backend/game/utils/game_state_manager.py`
  - `frontend/src/views/GameView.vue`
  - `frontend/src/stores/gameState.js`
  - `docs/game_state_frontend_mapping.md`
  - `docs/TODO.md`
  - `docs/frontend_backend_alignment.md`
  - `docs/version-change-log.md`
- 更新内容：
  - `feat: 在核心 game_state 与前端状态元信息中补充 setup_build_is_completed，并同步暴露 setup_choice_is_completed，供前端区分初始板块选择、初始建筑摆放和初始效果结算阶段。`
  - `ui: 对局页回合信息框在 round=0 时按初始板块选择、初始建筑摆放、初始效果结算三个阶段显示状态文案，并在 round>=1 时恢复当前回合强调。`
  - `fix: 回合计分板结束后改为仅翻面不替换正面图片，已翻面的轮次支持悬停翻回查看正面计分内容，同时全量状态可按当前 round 还原历次翻面进度。`
  - `fix: 回合助推板改为基于 players[*].booster_ids 的全量/增量同步，拿取时翻背、归还时翻正，不再依赖旧的按索引盲翻事件。`
  - `fix: 修正对局页地图建筑图片映射，增量更新时土地只刷新六边形地块颜色，建筑改为按控制者颜色/建筑id/是否中立选择正确图片资源。`
  - `docs: 更新前端状态映射文档并移除不存在的 action_type: special 对齐项，避免继续沿用无效类型说明。`
  - `docs: 在待办文档中补充地图增量渲染拆分规则，记录侧楼应作为独立渲染单元并暂缓实现。`
  - `docs: 补充玩家标题栏分数与玩家状态面板全部可见数值的全量/增量对齐核查表，并将已打通项统一勾选。`
  - `docs: 明确对局页玩家标题栏分数对应后端 boardscore（板面分），不是 total final score。`
  - `docs: 将前后端对齐文档中的全量与增量更新流程修正为当前实际运行的 GameView.vue 直连 GET/SSE 链路。`
- 验证方式：
  - `python -m py_compile backend/game/aoi_game/game_engine.py backend/game/aoi_game/game_state.py backend/game/utils/frontend_state_types.py backend/game/utils/game_state_manager.py`
  - `cd frontend && npm run build`
  - `git diff -- docs/TODO.md docs/version-change-log.md`
  - `rg -n "2.3.1|boardscore|applyPlayerState|applyPlayerFieldChange|5.1 全量更新流程" docs/frontend_backend_alignment.md`
  - `git diff -- backend/game/aoi_game/game_engine.py backend/game/aoi_game/game_state.py backend/game/utils/frontend_state_types.py backend/game/utils/game_state_manager.py frontend/src/views/GameView.vue frontend/src/stores/gameState.js docs/game_state_frontend_mapping.md docs/frontend_backend_alignment.md docs/version-change-log.md`

## 0.9.5.7
- 日期：`2026-04-08`
- 分支：`main`
- 影响范围：
  - `frontend/src/views/GameView.vue`
  - `PROJECT_STRUCTURE.md`
  - `docs/PROJECT_STRUCTURE.md`
  - `docs/frontend_backend_alignment.md`
  - `backend/game/aoi_game/game_state.py`
  - `docs/version-change-log.md`
- 更新内容：
  - `fix: 对局页在应用后端全量玩家状态前先重置展示资源与规划卡相关默认值，避免同人数新局沿用上一局残留数据，确保 money、ore、bank_book、law_book、engineering_book、medical_book、meeples 的初始显示与后端默认值一致。`
  - `ui: 将对局页主布局重构为玩家面板、游戏区域、对局状态与可选行动、统一行动记录四列布局，压缩玩家面板与右侧操作区宽度，为最右侧新增行动记录列腾出空间。`
  - `refactor: 移除玩家卡片内的独立日志区，将玩家状态改为紧凑数字网格展示，并把 SSE log 消息统一汇总到最右侧行动记录列，便于后续继续扩展更多状态字段。`
  - `docs: 将项目架构文档从仓库根目录移动到 docs/PROJECT_STRUCTURE.md，统一项目文档存放位置。`
  - `fix: 删除 backend/game/aoi_game/game_state.py 中局部 adjust 函数错误的返回类型标注，避免类型定义与实际实现不一致。`
  - `ui: 将玩家状态区恢复为原有的分行图标加数字风格，并在移除独立玩家日志区后改为整块宽度承载全部状态行。`
  - `feat: 为玩家状态区新增五类建筑剩余数量显示，图标按 planning_card_id 切换到对应颜色建筑图，未选择规划卡时统一回退到 0-x.png。`
  - `ui: 进一步压缩玩家面板宽度与玩家卡片内边距，将玩家状态改为更高密度的四行布局，确保新增建筑剩余数量直接出现在可见区域内。`
  - `ui: 将对局页 map-container-full 的内边距调整为 20px，增加地图容器四周留白。`
  - `ui: 将对局页四栏宽度调整为 18% / 43% / 21% / 18%，并将 --game-section-inset 统一归零，移除区块额外内缩边距。`
  - `ui: 将回合助推板底部文字标签改为左下角圆形数字徽标，仅显示助推板编号。`
  - `ui: 细调回合助推板左下角数字徽标，缩小尺寸并进一步贴近左下角，改为半透明强调色圆标。`
  - `ui: 将回合助推板数字徽标进一步缩小到 20px，并收口为不透明强调色圆标。`
  - `ui: 将回合助推板左下角数字徽标尺寸回调到 24px，并同步放大数字字号。`
  - `ui: 重新排布玩家状态四行分组，将五种建筑剩余数量单独成行，资源区改为金币、矿石、米宝（附总剩余角标）与桥梁同列，四本书与三段魔力加城市/航海/铲力分别独立成行。`
  - `ui: 取消玩家卡片固定最小高度并继续压缩玩家面板宽度、卡片内边距和状态图标尺寸，避免展开后底部出现大面积留白。`
  - `ui: 调整玩家卡片标题区与状态区比例，缩短标题栏高度、抬高四行状态的行高，并将建筑剩余行与资源行顺序对调。`
  - `fix: 将玩家卡片折叠动效改为作用于状态区高度，恢复收起与展开的双向动画，同时移除状态分割线与色块差异，统一标题区和状态区背景。`
  - `ui: 统一玩家卡片内建筑图标、资源图标、魔力图标和同级数字字号，修正最后一行状态数值视觉偏小的问题。`
  - `ui: 继续压缩玩家卡片标题栏与四行状态的纵向高度，统一图标容器与 icon-数字 间距，并将桥梁图标替换为更贴近语义的桥型图标，同时放大建筑图标补齐视觉尺寸。`
  - `ui: 修正玩家卡片最后一行字体图标在固定图标容器内的垂直居中方式，消除 Font Awesome 图标基线造成的上下偏移。`
  - `fix: 将魔力状态图标从 Font Awesome 数字叠加改为白色圆底配居中文字，修正圆底、圈内 1/2/3 与右侧数值之间的对齐偏移。`
  - `docs: 勾选前后端对齐文档中已完成的 planning_card_id 前端显示映射项。`
- 验证方式：
  - `cd frontend && npm run build`
  - `git diff -- PROJECT_STRUCTURE.md docs/PROJECT_STRUCTURE.md backend/game/aoi_game/game_state.py docs/frontend_backend_alignment.md`
  - `git diff -- frontend/src/views/GameView.vue docs/version-change-log.md`

## 0.9.5.6
- 日期：`2026-04-08`
- 分支：`main`
- 影响范围：
  - `.gitignore`
  - `docs/version-change-log.md`
- 更新内容：
  - `chore: 补充 Git 忽略规则，排除本地会话目录与临时截图文件。`
- 验证方式：
  - `git status --short`

## 0.9.5.5
- 日期：`2026-04-08`
- 分支：`main`
- 影响范围：
  - `frontend/`
  - `backend/api/`
  - `backend/app.py`
  - `docs/`
  - `AGENTS.md`
- 更新内容：
  - `ui: 优化开始游戏倒计时数字背景动效，将原先较突兀的扩散效果改为更克制的蓝色柔光与光晕效果。`
  - `fix: 去除倒计时数字背景圆圈在 3 -> 2 -> 1 -> 0 过程中随数字切换而产生的缩放闪动，仅保留数字本身的切换动效。`
  - `chore: 更新 Agent 规范，移除已废弃的 WebIO 概念及相关约定。`
  - `docs: 更新版本记录维护规则，明确未给版本号前，所有改动统一写入本次修改区域，待后续分配版本号后再归档。`
  - `chore: 将版本记录文档名调整为更贴切的 version-change-log.md。`
  - `ui: 将对局页玩家监控卡片展开高度调整为 32.3%。`
  - `ui: 将对局页玩家监控卡片默认状态改为折叠。`
  - `docs: 规范版本变更记录中的更新内容格式，统一使用 type: 中文描述。`
  - `docs: 追溯修正现有版本条目的更新内容格式。`
  - `ui: 对局页玩家卡片按 planning_card_id 显示规划卡颜色圆点，并按 faction_id 在玩家名称旁显示派系徽章。`
  - `fix: 统一对局页玩家卡片在全量状态、单玩家推送和增量更新中的 planning_card_id 与 faction_id 显示映射。`
  - `ui: 调整派系徽章头像为中部放大裁切填满圆圈，并修正圆圈与左侧胶囊的几何对齐。`
  - `fix: 修复对局页点击可选行动后，增量更新未正确映射到页面扁平字段，导致必须刷新才能看到玩家资源、得分和可选行动变化的问题。`
  - `fix: 为对局页防御地图增量渲染添加本地快照，修复建筑相关增量更新分支引用未定义 mapState 而中断状态同步的问题。`
  - `fix: 在后端开局流程中为 GameController 补充 SSE 消息回调绑定，修复点击可选行动后后续 available_actions 和 incremental 更新未进入推送队列的断链问题。`
  - `ui: 精确按派系精灵图的 7104x338 实际尺寸计算中心正方形裁切和胶囊内边距，确保头像圆圈等距内嵌并完整铺满。`
  - `ui: 将派系徽章改为 grid 两列布局，按胶囊高度、边框和内边距公式精确计算圆圈直径，修复垂直居中对齐偏差。`
  - `ui: 支持在对局页派系徽章上悬停 2 秒后显示完整派系板块预览，便于快速确认全图。`
  - `ui: 将派系徽章头像剪裁基准从正中改为在原始板块基础上向右偏移 20px，并改为带有像素偏移常量的公式化计算。`
  - `fix: 将派系徽章头像剪裁从带边框外层改到无边框内层图片层，避免 background-origin 对可见裁切区域的干扰，确保 147/107 偏移真正生效。`
  - `ui: 将派系徽章头像右侧偏移进一步调整为 22px，将完整派系板块预览的悬停时间改为 1 秒，并移除派系徽章的原生 title 提示。`
  - `ui: 将派系徽章头像右侧偏移进一步调整为 24px，并将悬停预览延迟时间缩短为 300ms。`
  - `fix: 为对局页行动提交流程补充基于状态 version 的轮询兜底，同步在 SSE 丢失或后端未重连时主动拉取最新全量状态，避免点击后页面仍停留在旧行动与旧资源显示。`
  - `ui: 移除对局页玩家监控区与游戏区域内部内容容器的描边，并将外层容器背景统一调整为 #171717，使面板底色保持一致。`
  - `ui: 将对局页左侧标题文案从“玩家监控”统一调整为“玩家面板”。`
  - `docs: 勾选前后端对齐文档中已完成的派系徽章显示与玩家资源显示映射项。`
  - `ui: 移除对局页右下角已废弃的行动编号输入框与发送按钮，保留点击可选行动直接提交的交互。`
  - `ui: 将对局页派系徽章改为仅在圆形标识悬停或聚焦时显示完整派系板块预览，并移除原生文字提示。`
  - `ui: 适度增加对局页整体外边距、三栏间距与主要内容区留白，让页面布局更舒展。`
  - `ui: 继续上调对局页外层页边距与栏间距，同时将玩家面板和游戏区域内部留白回收一档，保持比初始布局更宽松但不显空。`
  - `ui: 将对局页派系与规划卡预览统一为上图下字卡片样式，保留仅圆形标识触发并移除圆圈上移动画。`
  - `ui: 将对局页通用预览浮层回调为无内框样式，恢复图片四角圆角与下方纯文字排布。`
  - `ui: 将对局页通用预览浮层的背景与兜底底色从蓝调改为纯灰系。`
  - `ui: 按照最新布局参数将对局页外层边距调整为 24px 48px 36px 48px，并将栏间距、内容区 inset 与内容 gap 校准为 18px、8px、16px。`
- 验证方式：
  - `cd frontend && npm run build`

## 0.9.5.4
- 日期：`2026-04-07`
- 分支：`main`
- 影响范围：
  - `frontend/src/views/SetupView.vue`
- 更新内容：
  - `feat: 将设置页开始游戏流程改为全屏分阶段弹窗。`
  - `ui: 在后端游戏状态真正就绪前，先显示加载动画与转圈图标。`
  - `feat: 在后端返回成功后，增加 3 -> 2 -> 1 -> 0 的动态倒计时提示，再进入游戏页面。`
  - `fix: 去除倒计时结束后、进入游戏前错误闪回转圈动画的问题。`
  - `fix: 增加倒计时定时器清理逻辑，并延长后端状态轮询等待时间。`
- 验证方式：
  - `cd frontend && npm run build`

