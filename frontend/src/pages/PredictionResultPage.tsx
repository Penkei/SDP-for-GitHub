import { useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import type { PredictionResponse, PredictionResult } from "../types/prediction";
import PredictionTable from "../components/PredictionTable";
import MetricGuide from "../components/MetricGuide";
import { exportPredictionReport } from "../services/api";

export type ProbabilitySortDirection = "desc" | "asc";
type RiskFilter = "All" | "High" | "Medium" | "Low";
type PredictionFilter = "All" | "Defective" | "Non-defective";
type ExportFormat = "csv" | "pdf";

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

const getResultKey = (result: PredictionResult) =>
  [
    result.file_path,
    result.language,
    result.prediction_label,
    result.defect_risk_probability,
  ].join("|");

const escapeHtml = (value: unknown) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const formatSvgNumber = (value: number) => Number(value.toFixed(3));

const getTopLevelFolder = (filePath: string) => {
  const normalizedPath = filePath.replaceAll("\\", "/");
  const pathParts = normalizedPath.split("/").filter(Boolean);

  if (pathParts.length <= 1) {
    return "Repository root";
  }

  return pathParts[0];
};

const buildReportStats = (results: PredictionResult[]) => {
  const languageStats = new Map<string, { count: number; probabilitySum: number }>();

  const summary = results.reduce(
    (stats, result) => {
      const probability = result.defect_risk_probability;
      const language = result.language || "Unknown";

      if (result.risk_level === "High") {
        stats.highRiskCount += 1;
      } else if (result.risk_level === "Medium") {
        stats.mediumRiskCount += 1;
      } else {
        stats.lowRiskCount += 1;
      }

      if (result.prediction_label === "Defective") {
        stats.defectiveCount += 1;
      }

      stats.probabilitySum += probability;

      if (!stats.highestRiskFile || probability > stats.highestRiskFile.defect_risk_probability) {
        stats.highestRiskFile = result;
      }

      const languageItem = languageStats.get(language) || {
        count: 0,
        probabilitySum: 0,
      };
      languageItem.count += 1;
      languageItem.probabilitySum += probability;
      languageStats.set(language, languageItem);

      return stats;
    },
    {
      highRiskCount: 0,
      mediumRiskCount: 0,
      lowRiskCount: 0,
      defectiveCount: 0,
      probabilitySum: 0,
      highestRiskFile: null as PredictionResult | null,
    }
  );

  return {
    ...summary,
    totalFiles: results.length,
    averageProbability: results.length ? summary.probabilitySum / results.length : 0,
    languageBreakdown: Array.from(languageStats.entries())
      .map(([language, item]) => ({
        language,
        count: item.count,
        averageProbability: item.probabilitySum / item.count,
      }))
      .sort((a, b) => b.count - a.count),
  };
};

const buildPdfReportHtml = (
  predictionResponse: PredictionResponse,
  results: PredictionResult[]
) => {
  const stats = buildReportStats(results);
  const highPercent = stats.totalFiles ? (stats.highRiskCount / stats.totalFiles) * 100 : 0;
  const mediumPercent = stats.totalFiles ? (stats.mediumRiskCount / stats.totalFiles) * 100 : 0;
  const lowPercent = stats.totalFiles ? (stats.lowRiskCount / stats.totalFiles) * 100 : 0;
  const donutCircumference = 339.292;
  const highArc = (highPercent / 100) * donutCircumference;
  const mediumArc = (mediumPercent / 100) * donutCircumference;
  const lowArc = (lowPercent / 100) * donutCircumference;
  const donutSvg = `
    <svg class="donut-svg" viewBox="0 0 150 150" aria-label="Risk distribution">
      <circle class="donut-track" cx="75" cy="75" r="54"></circle>
      <circle class="donut-segment low" cx="75" cy="75" r="54"
        stroke-dasharray="${lowArc} ${donutCircumference - lowArc}"
        stroke-dashoffset="-${highArc + mediumArc}"></circle>
      <circle class="donut-segment medium" cx="75" cy="75" r="54"
        stroke-dasharray="${mediumArc} ${donutCircumference - mediumArc}"
        stroke-dashoffset="-${highArc}"></circle>
      <circle class="donut-segment high" cx="75" cy="75" r="54"
        stroke-dasharray="${highArc} ${donutCircumference - highArc}"
        stroke-dashoffset="0"></circle>
      <text x="75" y="71" text-anchor="middle" class="donut-value">${formatPercent(stats.averageProbability)}</text>
      <text x="75" y="91" text-anchor="middle" class="donut-label">Avg risk</text>
    </svg>
  `;
  const threshold =
    predictionResponse.prediction_threshold !== null &&
    predictionResponse.prediction_threshold !== undefined
      ? formatPercent(predictionResponse.prediction_threshold)
      : "Model default";

  const languageCards = stats.languageBreakdown
    .map((item) => {
      const countHeight = Math.max(
        12,
        (item.count / Math.max(stats.totalFiles, 1)) * 82
      );
      const riskHeight = Math.max(12, item.averageProbability * 82);

      return `
        <div class="language-card">
          <strong>${escapeHtml(item.language)}</strong>
          <span>${item.count} files</span>
          <svg class="mini-bars" viewBox="0 0 78 92" aria-label="Language risk">
            <line x1="8" y1="88" x2="70" y2="88"></line>
            <rect class="count-bar" x="22" y="${88 - countHeight}" width="16" height="${countHeight}" rx="5"></rect>
            <rect class="risk-bar" x="42" y="${88 - riskHeight}" width="16" height="${riskHeight}" rx="5"></rect>
          </svg>
          <small>${formatPercent(item.averageProbability)} avg risk</small>
        </div>
      `;
    })
    .join("");
  const maxLanguageCount = Math.max(
    ...stats.languageBreakdown.map((item) => item.count),
    1
  );
  const languageChartWidth = 760;
  const languageChartHeight = 260;
  const languagePlotTop = 24;
  const languagePlotBottom = 204;
  const languagePlotHeight = languagePlotBottom - languagePlotTop;
  const languageItems = stats.languageBreakdown.slice(0, 8);
  const languageSlotWidth = languageItems.length
    ? languageChartWidth / languageItems.length
    : languageChartWidth;
  const languageChartBars = languageItems
    .map((item, index) => {
      const countHeight = Math.max(
        8,
        (item.count / maxLanguageCount) * languagePlotHeight
      );
      const riskHeight = Math.max(8, item.averageProbability * languagePlotHeight);
      const groupX = index * languageSlotWidth + languageSlotWidth / 2 - 26;
      const label = escapeHtml(item.language);

      return `
        <g>
          <rect x="${formatSvgNumber(groupX)}" y="${formatSvgNumber(
            languagePlotBottom - countHeight
          )}" width="20" height="${formatSvgNumber(countHeight)}" rx="5" fill="#2563eb"></rect>
          <rect x="${formatSvgNumber(groupX + 28)}" y="${formatSvgNumber(
            languagePlotBottom - riskHeight
          )}" width="20" height="${formatSvgNumber(riskHeight)}" rx="5" fill="#dc2626"></rect>
          <text x="${formatSvgNumber(
            index * languageSlotWidth + languageSlotWidth / 2
          )}" y="230" text-anchor="middle" class="chart-label">${label}</text>
          <text x="${formatSvgNumber(
            index * languageSlotWidth + languageSlotWidth / 2
          )}" y="248" text-anchor="middle" class="chart-sub-label">${item.count} files | ${formatPercent(
        item.averageProbability
      )}</text>
        </g>
      `;
    })
    .join("");
  const languageChartSvg = `
    <svg class="report-chart language-report-chart" viewBox="0 0 ${languageChartWidth} ${languageChartHeight}" role="img" aria-label="Language risk overview">
      <line x1="24" y1="${languagePlotBottom}" x2="${languageChartWidth - 24}" y2="${languagePlotBottom}" stroke="#cbd5e1" stroke-width="1"></line>
      ${languageChartBars}
    </svg>
  `;
  const topRiskResults = [...results]
    .sort((a, b) => b.defect_risk_probability - a.defect_risk_probability)
    .slice(0, 8);
  const topRiskRows = topRiskResults
    .map((result) => {
      const probability = formatSvgNumber(
        Math.max(0.03, result.defect_risk_probability) * 100
      );
      const riskClass = escapeHtml(result.risk_level.toLowerCase());

      return `
        <div class="top-risk-row">
          <div>
            <strong>${escapeHtml(result.file_path)}</strong>
            <span>${escapeHtml(result.language || "Unknown")} | ${escapeHtml(result.prediction_label)}</span>
          </div>
          <div class="top-risk-track">
            <span class="${riskClass}" style="width: ${probability}%"></span>
          </div>
          <b>${formatPercent(result.defect_risk_probability)}</b>
        </div>
      `;
    })
    .join("");

  const resultRows = results
    .map(
      (result, index) => `
        <tr>
          <td>${index + 1}</td>
          <td class="file-path">${escapeHtml(result.file_path)}</td>
          <td>${escapeHtml(result.language || "Unknown")}</td>
          <td>${escapeHtml(result.prediction_label)}</td>
          <td>${formatPercent(result.defect_risk_probability)}</td>
          <td><span class="risk-badge ${escapeHtml(result.risk_level.toLowerCase())}">${escapeHtml(result.risk_level)}</span></td>
          <td>${escapeHtml(result.recommendation)}</td>
        </tr>
        <tr class="explanation-row">
          <td></td>
          <td colspan="6">${escapeHtml(result.readable_explanation || result.top_contributing_metrics || "No explanation available.")}</td>
        </tr>
      `
    )
    .join("");

  return `<!doctype html>
  <html>
    <head>
      <title>SDP for GitHub Prediction Report</title>
      <style>
        * { box-sizing: border-box; }
        html, body, * {
          print-color-adjust: exact;
          -webkit-print-color-adjust: exact;
        }
        body {
          margin: 0;
          padding: 28px;
          background: #f5f7fb;
          color: #111827;
          font-family: Arial, Helvetica, sans-serif;
        }
        .report-shell { max-width: 1120px; margin: 0 auto; }
        .hero, .panel, .stat-card {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .hero { padding: 24px; margin-bottom: 18px; }
        h1 { margin: 0 0 10px; font-size: 28px; }
        h2 { margin: 0 0 12px; font-size: 18px; }
        p { margin: 6px 0; color: #4b5563; line-height: 1.45; }
        .meta-grid, .stat-grid, .detail-grid, .language-grid {
          display: grid;
          gap: 12px;
        }
        .meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 16px; }
        .meta-item { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 11px; overflow-wrap: anywhere; }
        .meta-item span, .stat-card span { color: #64748b; display: block; font-size: 12px; font-weight: 700; text-transform: uppercase; }
        .meta-item strong { display: block; margin-top: 5px; }
        .stat-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); margin-bottom: 14px; }
        .stat-card { min-height: 96px; padding: 15px; border-top: 4px solid #2563eb; }
        .stat-card.high { border-top-color: #dc2626; }
        .stat-card.medium { border-top-color: #d97706; }
        .stat-card.low { border-top-color: #16a34a; }
        .stat-card.defective { border-top-color: #7c3aed; }
        .stat-card strong { display: block; font-size: 26px; margin: 8px 0 4px; }
        .stat-card small { color: #64748b; font-weight: 700; }
        .detail-grid { grid-template-columns: 1.2fr 1fr; margin-bottom: 14px; }
        .panel { padding: 18px; }
        .risk-layout { align-items: center; display: grid; grid-template-columns: 150px 1fr; gap: 20px; }
        .donut {
          height: 150px;
          width: 150px;
        }
        .donut-svg { height: 150px; width: 150px; }
        .donut-track {
          fill: #ffffff;
          stroke: #e5e7eb;
          stroke-width: 22;
        }
        .donut-segment {
          fill: none;
          stroke-linecap: butt;
          stroke-width: 22;
          transform: rotate(-90deg);
          transform-origin: 75px 75px;
        }
        .donut-segment.high { stroke: #dc2626; }
        .donut-segment.medium { stroke: #d97706; }
        .donut-segment.low { stroke: #16a34a; }
        .donut-value { fill: #111827; font-size: 18px; font-weight: 800; }
        .donut-label { fill: #64748b; font-size: 10px; font-weight: 700; }
        .risk-list { display: grid; gap: 8px; }
        .risk-list div { align-items: center; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; display: grid; grid-template-columns: 1fr auto auto; gap: 10px; padding: 9px; }
        .highest-file { color: #111827; font-family: Consolas, monospace; overflow-wrap: anywhere; }
        .visual-grid { display: grid; gap: 14px; grid-template-columns: 1.2fr 1fr; margin-bottom: 14px; }
        .report-chart { display: block; height: auto; max-width: 100%; width: 100%; }
        .chart-label { fill: #111827; font-size: 12px; font-weight: 800; }
        .chart-sub-label { fill: #64748b; font-size: 10px; font-weight: 700; }
        .chart-legend { align-items: center; display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; }
        .chart-legend span { align-items: center; color: #475569; display: inline-flex; font-size: 12px; font-weight: 800; gap: 7px; }
        .legend-box { border-radius: 4px; display: inline-block; height: 11px; width: 18px; }
        .legend-box.count { background: #2563eb; }
        .legend-box.risk { background: #dc2626; }
        .top-risk-list { display: grid; gap: 10px; }
        .top-risk-row { align-items: center; display: grid; gap: 10px; grid-template-columns: minmax(0, 1.4fr) minmax(140px, 0.9fr) auto; }
        .top-risk-row strong, .top-risk-row span { display: block; overflow-wrap: anywhere; }
        .top-risk-row strong { font-family: Consolas, monospace; font-size: 12px; }
        .top-risk-row span { color: #64748b; font-size: 11px; margin-top: 3px; }
        .top-risk-row b { font-size: 12px; }
        .top-risk-track { background: #e5e7eb; border-radius: 999px; height: 12px; overflow: hidden; }
        .top-risk-track span { display: block; height: 100%; }
        .top-risk-track .high { background: #dc2626; }
        .top-risk-track .medium { background: #d97706; }
        .top-risk-track .low { background: #16a34a; }
        .language-grid { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin-bottom: 14px; }
        .language-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; }
        .language-card strong, .language-card span, .language-card small { display: block; }
        .language-card span, .language-card small { color: #64748b; margin-top: 5px; }
        .mini-bars { height: 92px; margin: 8px 0; width: 78px; }
        .mini-bars line { stroke: #cbd5e1; stroke-width: 1; }
        .mini-bars .count-bar { fill: #2563eb; }
        .mini-bars .risk-bar { fill: #dc2626; }
        table { border-collapse: collapse; width: 100%; background: #ffffff; }
        th, td { border: 1px solid #e5e7eb; font-size: 12px; padding: 9px; text-align: left; vertical-align: top; }
        th { background: #f3f4f6; font-weight: 800; }
        .file-path { font-family: Consolas, monospace; overflow-wrap: anywhere; }
        .risk-badge { border-radius: 999px; display: inline-block; font-weight: 800; padding: 4px 8px; }
        .risk-badge.high { background: #fee2e2; color: #991b1b; }
        .risk-badge.medium { background: #fef3c7; color: #92400e; }
        .risk-badge.low { background: #dcfce7; color: #166534; }
        .explanation-row td { background: #f8fafc; color: #475569; line-height: 1.45; }
        @media print {
          body { background: #ffffff; padding: 0; }
          .hero, .panel, .stat-card { box-shadow: none; }
          .panel, .hero, .stat-card, tr { break-inside: avoid; }
        }
      </style>
    </head>
    <body>
      <main class="report-shell">
        <section class="hero">
          <h1>SDP for GitHub - Prediction Report</h1>
          <p>This report summarizes the selected prediction results and their risk distribution.</p>
          <div class="meta-grid">
            <div class="meta-item"><span>Repository</span><strong>${escapeHtml(predictionResponse.repo_url)}</strong></div>
            <div class="meta-item"><span>Commit</span><strong>${escapeHtml(predictionResponse.commit_sha)}</strong></div>
            <div class="meta-item"><span>Threshold</span><strong>${threshold}</strong></div>
            <div class="meta-item"><span>Exported Files</span><strong>${stats.totalFiles}</strong></div>
          </div>
        </section>

        <section class="stat-grid">
          <div class="stat-card high"><span>High Risk</span><strong>${stats.highRiskCount}</strong><small>${formatPercent(highPercent / 100)}</small></div>
          <div class="stat-card medium"><span>Medium Risk</span><strong>${stats.mediumRiskCount}</strong><small>${formatPercent(mediumPercent / 100)}</small></div>
          <div class="stat-card low"><span>Low Risk</span><strong>${stats.lowRiskCount}</strong><small>${formatPercent(lowPercent / 100)}</small></div>
          <div class="stat-card defective"><span>Defective</span><strong>${stats.defectiveCount}</strong><small>${formatPercent(stats.totalFiles ? stats.defectiveCount / stats.totalFiles : 0)}</small></div>
          <div class="stat-card"><span>Average Risk</span><strong>${formatPercent(stats.averageProbability)}</strong><small>Mean probability</small></div>
        </section>

        <section class="detail-grid">
          <div class="panel">
            <h2>Risk Distribution</h2>
            <div class="risk-layout">
              <div class="donut">${donutSvg}</div>
              <div class="risk-list">
                <div><span>High</span><strong>${stats.highRiskCount}</strong><small>${formatPercent(highPercent / 100)}</small></div>
                <div><span>Medium</span><strong>${stats.mediumRiskCount}</strong><small>${formatPercent(mediumPercent / 100)}</small></div>
                <div><span>Low</span><strong>${stats.lowRiskCount}</strong><small>${formatPercent(lowPercent / 100)}</small></div>
              </div>
            </div>
          </div>
          <div class="panel">
            <h2>Highest Risk File</h2>
            <p class="highest-file">${escapeHtml(stats.highestRiskFile?.file_path || "No file available")}</p>
            <p>${escapeHtml(stats.highestRiskFile?.language || "Unknown")} | ${escapeHtml(stats.highestRiskFile?.risk_level || "No risk")} | ${formatPercent(stats.highestRiskFile?.defect_risk_probability || 0)}</p>
          </div>
        </section>

        <section class="visual-grid">
          <div class="panel">
            <h2>Language Risk Overview</h2>
            ${languageChartSvg}
            <div class="chart-legend">
              <span><i class="legend-box count"></i>File volume</span>
              <span><i class="legend-box risk"></i>Average risk</span>
            </div>
          </div>
          <div class="panel">
            <h2>Top Risk Files</h2>
            <div class="top-risk-list">${topRiskRows}</div>
          </div>
        </section>

        <section class="language-grid">
          ${languageCards}
        </section>

        <section class="panel">
          <h2>Selected Results</h2>
          <table>
            <thead>
              <tr>
                <th>No.</th>
                <th>File</th>
                <th>Language</th>
                <th>Prediction</th>
                <th>Probability</th>
                <th>Risk</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>${resultRows}</tbody>
          </table>
        </section>
      </main>
      <script>
        window.addEventListener("load", () => {
          setTimeout(() => window.print(), 250);
        });
      </script>
    </body>
  </html>`;
};

function PredictionResultPage() {
  const location = useLocation();

  const predictionResponse = location.state?.predictionResponse as
    | PredictionResponse
    | undefined;

  const [probabilitySortDirection, setProbabilitySortDirection] =
    useState<ProbabilitySortDirection>("desc");

  const [isMetricGuideOpen, setIsMetricGuideOpen] = useState(false);
  const [fileSearch, setFileSearch] = useState("");
  const [languageFilter, setLanguageFilter] = useState("All");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("All");
  const [predictionFilter, setPredictionFilter] =
    useState<PredictionFilter>("All");
  const [minProbability, setMinProbability] = useState("");
  const [maxProbability, setMaxProbability] = useState("");
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | "">("");
  const [selectedResultKeys, setSelectedResultKeys] = useState<Set<string>>(
    () => new Set()
  );

  const availableLanguages = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    return Array.from(
      new Set(
        predictionResponse.results
          .map((result) => result.language)
          .filter(Boolean)
      )
    ).sort();
  }, [predictionResponse]);

  const dashboardStats = useMemo(() => {
    const emptyStats = {
      totalFiles: 0,
      highRiskCount: 0,
      mediumRiskCount: 0,
      lowRiskCount: 0,
      defectiveCount: 0,
      averageProbability: 0,
      highestRiskFile: null as PredictionResult | null,
      riskiestFolder: "No folder",
      riskiestFolderAverage: 0,
      languageBreakdown: [] as Array<{
        language: string;
        count: number;
        averageProbability: number;
      }>,
      riskDistribution: [] as Array<{
        label: string;
        count: number;
        percent: number;
        className: string;
      }>,
    };

    if (!predictionResponse || predictionResponse.results.length === 0) {
      return emptyStats;
    }

    const folderStats = new Map<string, { count: number; probabilitySum: number }>();
    const languageStats = new Map<string, { count: number; probabilitySum: number }>();

    const stats = predictionResponse.results.reduce(
      (summary, result) => {
        const probability = result.defect_risk_probability;
        const folder = getTopLevelFolder(result.file_path);
        const language = result.language || "Unknown";

        if (result.risk_level === "High") {
          summary.highRiskCount += 1;
        } else if (result.risk_level === "Medium") {
          summary.mediumRiskCount += 1;
        } else {
          summary.lowRiskCount += 1;
        }

        if (result.prediction_label === "Defective") {
          summary.defectiveCount += 1;
        }

        summary.probabilitySum += probability;

        if (
          !summary.highestRiskFile ||
          probability > summary.highestRiskFile.defect_risk_probability
        ) {
          summary.highestRiskFile = result;
        }

        const folderItem = folderStats.get(folder) || {
          count: 0,
          probabilitySum: 0,
        };
        folderItem.count += 1;
        folderItem.probabilitySum += probability;
        folderStats.set(folder, folderItem);

        const languageItem = languageStats.get(language) || {
          count: 0,
          probabilitySum: 0,
        };
        languageItem.count += 1;
        languageItem.probabilitySum += probability;
        languageStats.set(language, languageItem);

        return summary;
      },
      {
        ...emptyStats,
        probabilitySum: 0,
      }
    );

    const sortedFolders = Array.from(folderStats.entries()).sort((a, b) => {
      const averageA = a[1].probabilitySum / a[1].count;
      const averageB = b[1].probabilitySum / b[1].count;

      return averageB - averageA;
    });

    const languageBreakdown = Array.from(languageStats.entries())
      .map(([language, item]) => ({
        language,
        count: item.count,
        averageProbability: item.probabilitySum / item.count,
      }))
      .sort((a, b) => b.count - a.count);

    const riskiestFolder = sortedFolders[0];

    const totalFiles = predictionResponse.results.length;
    const riskDistribution = [
      {
        label: "High",
        count: stats.highRiskCount,
        percent: totalFiles ? stats.highRiskCount / totalFiles : 0,
        className: "high",
      },
      {
        label: "Medium",
        count: stats.mediumRiskCount,
        percent: totalFiles ? stats.mediumRiskCount / totalFiles : 0,
        className: "medium",
      },
      {
        label: "Low",
        count: stats.lowRiskCount,
        percent: totalFiles ? stats.lowRiskCount / totalFiles : 0,
        className: "low",
      },
    ];

    return {
      totalFiles: predictionResponse.results.length,
      highRiskCount: stats.highRiskCount,
      mediumRiskCount: stats.mediumRiskCount,
      lowRiskCount: stats.lowRiskCount,
      defectiveCount: stats.defectiveCount,
      averageProbability: stats.probabilitySum / predictionResponse.results.length,
      highestRiskFile: stats.highestRiskFile,
      riskiestFolder: riskiestFolder ? riskiestFolder[0] : "No folder",
      riskiestFolderAverage: riskiestFolder
        ? riskiestFolder[1].probabilitySum / riskiestFolder[1].count
        : 0,
      languageBreakdown,
      riskDistribution,
    };
  }, [predictionResponse]);

  const riskDonutBackground = useMemo(() => {
    if (dashboardStats.totalFiles === 0) {
      return "#e5e7eb";
    }

    const highEnd = dashboardStats.riskDistribution[0].percent * 100;
    const mediumEnd =
      highEnd + dashboardStats.riskDistribution[1].percent * 100;

    return `conic-gradient(#dc2626 0 ${highEnd}%, #d97706 ${highEnd}% ${mediumEnd}%, #16a34a ${mediumEnd}% 100%)`;
  }, [dashboardStats]);

  const filteredResults = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    const normalizedSearch = fileSearch.trim().toLowerCase();
    const parsedMinProbability =
      minProbability.trim() === "" ? null : Number(minProbability) / 100;
    const parsedMaxProbability =
      maxProbability.trim() === "" ? null : Number(maxProbability) / 100;

    return predictionResponse.results.filter((result) => {
      const matchesSearch =
        !normalizedSearch ||
        result.file_path.toLowerCase().includes(normalizedSearch);
      const matchesLanguage =
        languageFilter === "All" || result.language === languageFilter;
      const matchesRisk =
        riskFilter === "All" || result.risk_level === riskFilter;
      const matchesPrediction =
        predictionFilter === "All" ||
        result.prediction_label === predictionFilter;
      const matchesMinProbability =
        parsedMinProbability === null ||
        result.defect_risk_probability >= parsedMinProbability;
      const matchesMaxProbability =
        parsedMaxProbability === null ||
        result.defect_risk_probability <= parsedMaxProbability;

      return (
        matchesSearch &&
        matchesLanguage &&
        matchesRisk &&
        matchesPrediction &&
        matchesMinProbability &&
        matchesMaxProbability
      );
    });
  }, [
    predictionResponse,
    fileSearch,
    languageFilter,
    riskFilter,
    predictionFilter,
    minProbability,
    maxProbability,
  ]);

  const sortedResults = useMemo(() => {
    const copiedResults: PredictionResult[] = [...filteredResults];

    copiedResults.sort((a, b) => {
      if (probabilitySortDirection === "desc") {
        return b.defect_risk_probability - a.defect_risk_probability;
      }

      return a.defect_risk_probability - b.defect_risk_probability;
    });

    return copiedResults;
  }, [filteredResults, probabilitySortDirection]);

  const selectedResults = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    return predictionResponse.results.filter((result) =>
      selectedResultKeys.has(getResultKey(result))
    );
  }, [predictionResponse, selectedResultKeys]);

  const allShownSelected =
    sortedResults.length > 0 &&
    sortedResults.every((result) => selectedResultKeys.has(getResultKey(result)));

  const hasActiveFilters =
    fileSearch.trim() !== "" ||
    languageFilter !== "All" ||
    riskFilter !== "All" ||
    predictionFilter !== "All" ||
    minProbability.trim() !== "" ||
    maxProbability.trim() !== "";

  const resetFilters = () => {
    setFileSearch("");
    setLanguageFilter("All");
    setRiskFilter("All");
    setPredictionFilter("All");
    setMinProbability("");
    setMaxProbability("");
  };

  const handleToggleResultSelection = (resultKey: string) => {
    setSelectedResultKeys((currentKeys) => {
      const nextKeys = new Set(currentKeys);

      if (nextKeys.has(resultKey)) {
        nextKeys.delete(resultKey);
      } else {
        nextKeys.add(resultKey);
      }

      return nextKeys;
    });
  };

  const handleToggleAllShown = () => {
    setSelectedResultKeys((currentKeys) => {
      const nextKeys = new Set(currentKeys);

      if (allShownSelected) {
        sortedResults.forEach((result) => nextKeys.delete(getResultKey(result)));
      } else {
        sortedResults.forEach((result) => nextKeys.add(getResultKey(result)));
      }

      return nextKeys;
    });
  };

  const handleClearSelection = () => {
    setSelectedResultKeys(new Set());
  };

  const openPdfPrintReport = (
    exportPayload: PredictionResponse,
    exportResults: PredictionResult[]
  ) => {
    const reportHtml = buildPdfReportHtml(exportPayload, exportResults);
    const reportBlob = new Blob([reportHtml], {
      type: "text/html;charset=utf-8",
    });
    const reportUrl = URL.createObjectURL(reportBlob);
    const reportWindow = window.open(reportUrl, "_blank");

    if (!reportWindow) {
      URL.revokeObjectURL(reportUrl);
      return false;
    }

    window.setTimeout(() => URL.revokeObjectURL(reportUrl), 30000);
    return true;
  };

  const handleExportReport = async (format: ExportFormat) => {
    if (!predictionResponse) {
      return;
    }

    const exportResults = selectedResults;

    if (exportResults.length === 0) {
      return;
    }

    const exportPayload: PredictionResponse = {
      ...predictionResponse,
      total_files_scanned: exportResults.length,
      results: exportResults,
    };

    if (format === "pdf") {
      setExportingFormat(format);
      openPdfPrintReport(exportPayload, exportResults);
      window.setTimeout(() => setExportingFormat(""), 600);
      return;
    }

    setExportingFormat(format);

    try {
      const reportBlob = await exportPredictionReport(exportPayload);
      const downloadUrl = URL.createObjectURL(reportBlob);
      const link = document.createElement("a");

      link.href = downloadUrl;
      link.download = `defect_prediction_report_${predictionResponse.commit_sha.slice(
        0,
        8
      )}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);
    } finally {
      setExportingFormat("");
    }
  };

  if (!predictionResponse) {
    return (
      <div className="page">
        <div className="form-card">
          <h1>No Prediction Result</h1>
          <p>Please run a prediction first.</p>
          <Link to="/repository-input" className="primary-button">
            Go to Repository Input
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="result-header">
        <div className="result-header-top">
          <div>
            <h1>Prediction Result</h1>
            <p className="result-header-description">
              This page summarizes the model output for the selected commit.
              Use it to identify files that may need earlier review, then check
              the metric values and explanation before making a decision.
            </p>

            <p>
              Repository: <strong>{predictionResponse.repo_url}</strong>
            </p>

            <p>
              Commit: <strong>{predictionResponse.commit_sha}</strong>
            </p>

            <p>
<<<<<<< HEAD
=======
              Prediction Threshold:{" "}
              <strong>
                {predictionResponse.prediction_threshold !== null &&
                predictionResponse.prediction_threshold !== undefined
                  ? formatPercent(predictionResponse.prediction_threshold)
                  : "Model default"}
              </strong>
            </p>
            <p className="result-helper-text">
              Threshold means the cut-off for marking a file as defective. A
              file with risk probability equal to or above this value is labelled
              defective by the app.
            </p>

            <p>
>>>>>>> Refinement
              Total Supported Files Scanned:{" "}
              <strong>{predictionResponse.total_files_scanned}</strong>
            </p>
          </div>

          <div className="result-header-actions">
            <button
              className="metric-guide-open-button"
              onClick={() => setIsMetricGuideOpen(true)}
            >
              Metric Explanation Guide
            </button>
          </div>
        </div>
      </div>

      <section className="result-explainer-grid" aria-label="Result explanation">
        <div className="result-explainer-card">
          <span>Risk probability</span>
          <p>
            The percentage score for a file. Higher means the file looks more
            similar to files that were defective in the training data.
          </p>
        </div>

        <div className="result-explainer-card">
          <span>Risk level</span>
          <p>
            A simpler grouping of the probability into high, medium, or low so
            the result can be scanned quickly.
          </p>
        </div>

        <div className="result-explainer-card">
          <span>SHAP / metric values</span>
          <p>
            SHAP is used to explain the model decision. The metric values show
            which code or commit-history measurements pushed the prediction.
          </p>
        </div>

        <div className="result-explainer-card">
          <span>Recommendation</span>
          <p>
            A review priority suggestion based on the predicted risk. It should
            support code review, not replace developer judgement.
          </p>
        </div>
      </section>

      <section className="risk-dashboard" aria-label="Risk dashboard">
        <div className="dashboard-summary-grid">
          <div className="dashboard-stat high-risk-stat">
            <span>High Risk</span>
            <strong>{dashboardStats.highRiskCount}</strong>
            <small>
              {formatPercent(dashboardStats.riskDistribution[0]?.percent || 0)} of files
            </small>
          </div>

          <div className="dashboard-stat medium-risk-stat">
            <span>Medium Risk</span>
            <strong>{dashboardStats.mediumRiskCount}</strong>
            <small>
              {formatPercent(dashboardStats.riskDistribution[1]?.percent || 0)} of files
            </small>
          </div>

          <div className="dashboard-stat low-risk-stat">
            <span>Low Risk</span>
            <strong>{dashboardStats.lowRiskCount}</strong>
            <small>
              {formatPercent(dashboardStats.riskDistribution[2]?.percent || 0)} of files
            </small>
          </div>

          <div className="dashboard-stat defective-stat">
            <span>Defective</span>
            <strong>{dashboardStats.defectiveCount}</strong>
            <small>
              {formatPercent(
                dashboardStats.totalFiles
                  ? dashboardStats.defectiveCount / dashboardStats.totalFiles
                  : 0
              )} labelled defective
            </small>
          </div>

          <div className="dashboard-stat average-risk-stat">
            <span>Average Risk</span>
            <strong>{formatPercent(dashboardStats.averageProbability)}</strong>
            <small>Mean probability across files</small>
          </div>
        </div>

        <div className="dashboard-detail-grid">
          <div className="risk-panel risk-distribution-panel">
            <div className="risk-panel-header">
              <h2>Risk Distribution</h2>
              <span>{dashboardStats.totalFiles} files</span>
            </div>
            <p className="risk-panel-note">
              This chart shows how the scanned files are split across high,
              medium, and low risk categories.
            </p>

            <div className="risk-chart-layout">
              <div
                className="risk-donut"
                style={{ background: riskDonutBackground }}
                aria-hidden="true"
              >
                <div className="risk-donut-center">
                  <strong>{formatPercent(dashboardStats.averageProbability)}</strong>
                  <span>Avg risk</span>
                </div>
              </div>

              <div className="risk-breakdown-list">
                {dashboardStats.riskDistribution.map((item) => (
                  <div className="risk-breakdown-row" key={item.label}>
                    <span>
                      <i className={`legend-dot ${item.className}-dot`} />
                      {item.label}
                    </span>
                    <strong>{item.count}</strong>
                    <small>{formatPercent(item.percent)}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="risk-panel">
            <div className="risk-panel-header">
              <h2>Highest Risk File</h2>
              <span>
                {dashboardStats.highestRiskFile
                  ? formatPercent(
                      dashboardStats.highestRiskFile.defect_risk_probability
                    )
                  : "0.0%"}
              </span>
            </div>

            <p className="dashboard-file-path">
              {dashboardStats.highestRiskFile?.file_path || "No file available"}
            </p>
            <p className="dashboard-muted">
              {dashboardStats.highestRiskFile?.language || "No language"} |{" "}
              {dashboardStats.highestRiskFile?.risk_level || "No risk"}
            </p>
            <p className="dashboard-muted">
              Start here if you only have time to inspect one file.
            </p>
          </div>

          <div className="risk-panel">
            <div className="risk-panel-header">
              <h2>Riskiest Folder</h2>
              <span>{formatPercent(dashboardStats.riskiestFolderAverage)}</span>
            </div>

            <p className="dashboard-file-path">{dashboardStats.riskiestFolder}</p>
            <p className="dashboard-muted">
              Folder with the highest average defect probability among scanned
              files.
            </p>
          </div>
        </div>

        {dashboardStats.languageBreakdown.length > 0 && (
          <div className="risk-panel language-chart-panel">
            <div className="risk-panel-header">
              <h2>Language Risk Overview</h2>
              <span>Count and average risk</span>
            </div>
            <p className="risk-panel-note">
              Blue bars show how many files were scanned for each language. Red
              bars show the average risk score for that language.
            </p>

            <div className="language-column-chart">
              {dashboardStats.languageBreakdown.map((item) => (
                <div className="language-column-item" key={item.language}>
                  <div className="language-column-bars">
                    <span
                      className="language-count-bar"
                      style={{
                        height: `${Math.max(
                          12,
                          (item.count / dashboardStats.totalFiles) * 100
                        )}%`,
                      }}
                    />
                    <span
                      className="language-risk-bar"
                      style={{
                        height: `${Math.max(12, item.averageProbability * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="language-column-label">
                    <strong>{item.language}</strong>
                    <span>{item.count} files</span>
                    <small>{formatPercent(item.averageProbability)} avg</small>
                  </div>
                </div>
              ))}
            </div>

            <div className="chart-legend">
              <span>
                <i className="legend-line count-line" /> File volume
              </span>
              <span>
                <i className="legend-line risk-line" /> Average risk
              </span>
            </div>
          </div>
        )}
      </section>

      <div className="result-filters">
        <div className="result-section-heading">
          <div>
            <h2>File-Level Results</h2>
            <p>
              Filter, sort, select, and export the files that matter for your
              review. The table shows the model score and a plain-language
              explanation for each file.
            </p>
          </div>
        </div>

        <div className="filter-summary">
          <strong>{sortedResults.length}</strong> of{" "}
          <strong>{predictionResponse.results.length}</strong> files shown
          <span className="selection-summary">
            <strong>{selectedResults.length}</strong> selected
          </span>
        </div>

        <div className="filter-grid">
          <label className="filter-field filter-field-wide">
            <span>Search File Path</span>
            <input
              type="search"
              value={fileSearch}
              onChange={(event) => setFileSearch(event.target.value)}
              placeholder="Search by folder or file name"
            />
          </label>

          <label className="filter-field">
            <span>Language</span>
            <select
              value={languageFilter}
              onChange={(event) => setLanguageFilter(event.target.value)}
            >
              <option value="All">All languages</option>
              {availableLanguages.map((language) => (
                <option key={language} value={language}>
                  {language}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span>Risk Level</span>
            <select
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(event.target.value as RiskFilter)
              }
            >
              <option value="All">All risks</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </label>

          <label className="filter-field">
            <span>Prediction</span>
            <select
              value={predictionFilter}
              onChange={(event) =>
                setPredictionFilter(event.target.value as PredictionFilter)
              }
            >
              <option value="All">All predictions</option>
              <option value="Defective">Defective</option>
              <option value="Non-defective">Non-defective</option>
            </select>
          </label>

          <label className="filter-field">
            <span>Min Probability %</span>
            <input
              type="number"
              value={minProbability}
              min="0"
              max="100"
              onChange={(event) => setMinProbability(event.target.value)}
              placeholder="0"
            />
          </label>

          <label className="filter-field">
            <span>Max Probability %</span>
            <input
              type="number"
              value={maxProbability}
              min="0"
              max="100"
              onChange={(event) => setMaxProbability(event.target.value)}
              placeholder="100"
            />
          </label>
        </div>

        <button
          className="filter-reset-button"
          onClick={resetFilters}
          disabled={!hasActiveFilters}
        >
          Reset Filters
        </button>

        <div className="export-selection-panel">
          <div>
            <strong>Export Selection</strong>
            <span>Select rows in the table, then export them as CSV or PDF.</span>
          </div>

          <div className="export-selection-actions">
            <button
              className="secondary-export-button"
              onClick={handleToggleAllShown}
              disabled={sortedResults.length === 0}
            >
              {allShownSelected ? "Unselect Shown" : "Select Shown"}
            </button>
            <button
              className="secondary-export-button"
              onClick={handleClearSelection}
              disabled={selectedResults.length === 0}
            >
              Clear
            </button>
            <button
              className="export-report-button"
              onClick={() => handleExportReport("csv")}
              disabled={selectedResults.length === 0 || exportingFormat !== ""}
            >
              {exportingFormat === "csv" ? "Exporting CSV..." : "Export CSV"}
            </button>
            <button
              className="export-report-button"
              onClick={() => handleExportReport("pdf")}
              disabled={selectedResults.length === 0 || exportingFormat !== ""}
            >
              {exportingFormat === "pdf" ? "Exporting PDF..." : "Export PDF"}
            </button>
          </div>
        </div>
      </div>

      <PredictionTable
        results={sortedResults}
        probabilitySortDirection={probabilitySortDirection}
        selectedResultKeys={selectedResultKeys}
        getResultKey={getResultKey}
        onToggleResultSelection={handleToggleResultSelection}
        onToggleAllShown={handleToggleAllShown}
        allShownSelected={allShownSelected}
        onToggleProbabilitySort={() =>
          setProbabilitySortDirection((current) =>
            current === "desc" ? "asc" : "desc"
          )
        }
      />

      <MetricGuide
        isOpen={isMetricGuideOpen}
        onClose={() => setIsMetricGuideOpen(false)}
      />
    </div>
  );
}

export default PredictionResultPage;
