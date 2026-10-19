# 0.2.0

- 支持 StarPlot 0.22.0，并保留 0.21.4 兼容性。
- 新增 Mercator、ObliqueMercator、PlateCarree、Robinson；覆盖全部 13 种官方投影。
- 用 SVG Canvas 接口检查替代固定版本字符串检查；安装依赖范围为 `starplot>=0.21.4,<0.23`。
- 渲染缓存区分 StarPlot 版本，避免跨版本复用。
- 新增 `run_demo_projections.py`，默认生成全部 13 种投影的 PNG。
- 增加原生 NakedEye 肉眼视场示例与 30°/50°/60° 验证（需要 StarPlot 0.22.0）；仍使用 OpticPlot。
- 五种绘图类、资源和 `ArtConfig` 用法保持一致。

Mercator 的天极奇点、各投影的适用范围和原生绘图类的限制仍然适用；测试代表性参数不等于验证所有参数组合。

---

- Support StarPlot 0.22.0, retaining compatibility with 0.21.4.
- Add Mercator, ObliqueMercator, PlateCarree and Robinson: all 13 documented projections.
- Check the SVG Canvas interface instead of an exact version string; dependency range: `starplot>=0.21.4,<0.23`.
- Separate render caches by StarPlot version.
- Add `run_demo_projections.py` to export PNG examples of all 13 projections.
- Add a native NakedEye demo and 30/50/60-degree validation (StarPlot 0.22.0 required), using OpticPlot.
- Keep the five plot classes, artwork assets and `ArtConfig` workflow.

Native projection domains and plot-class restrictions still apply. Validation covers representative configurations, not every possible parameter combination.
