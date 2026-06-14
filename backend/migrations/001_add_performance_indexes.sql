-- 性能索引迁移 - 针对高频查询优化

-- 1. results 表与 reports 的 JOIN（所有 dashboard 和趋势查询的核心）
CREATE INDEX idx_results_report_id ON results(report_id);

-- 2. 指标名称查询（趋势图、指标搜索）
CREATE INDEX idx_results_metric_name ON results(metric_name);

-- 3. 异常指标过滤（首页异常卡片、异常详情列表）
CREATE INDEX idx_results_is_abnormal ON results(report_id, is_abnormal);

-- 4. 按患者+检查日期查询报告（报告列表、趋势查询）
CREATE INDEX idx_reports_patient_date ON reports(patient_id, exam_date);

-- 5. 患者用药记录查询
CREATE INDEX idx_medication_records_patient ON medication_records(patient_id);

-- 6. 用药项目按记录查询
CREATE INDEX idx_medication_items_record ON medication_items(record_id);

-- 7. share_tokens 按患者查询
CREATE INDEX idx_share_tokens_patient ON share_tokens(patient_id);
