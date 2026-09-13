import {
  EvaluationRuleSet,
  ScanResult,
  BatchEvaluationSummary,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "healthy";
  } catch {
    return false;
  }
}

export async function extractDocumentTextApi(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/extract-text`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to extract text from document");
  }

  const data = await res.json();
  return data.text || "";
}

export async function parseAnswerKeyApi(
  file?: File,
  rawContent?: string
): Promise<EvaluationRuleSet> {
  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  } else if (rawContent) {
    formData.append("raw_content", rawContent);
  }

  const res = await fetch(`${API_BASE}/api/rules/parse-answer-key`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to parse answer key" }));
    throw new Error(err.detail || "Failed to parse answer key");
  }

  return res.json();
}

export async function scanSubmissionsApi(
  zipFile: File,
  sessionId?: string
): Promise<ScanResult> {
  const formData = new FormData();
  formData.append("file", zipFile);
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  const res = await fetch(`${API_BASE}/api/evaluate/scan-submissions`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to scan submissions" }));
    throw new Error(err.detail || "Failed to scan student submissions");
  }

  return res.json();
}

export async function runEvaluationApi(
  sessionId: string,
  ruleSet: EvaluationRuleSet
): Promise<BatchEvaluationSummary> {
  const res = await fetch(`${API_BASE}/api/evaluate/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      rule_set: ruleSet,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Evaluation run failed" }));
    throw new Error(err.detail || "Evaluation run failed");
  }

  return res.json();
}

export function getExcelDownloadUrl(sessionId: string): string {
  return `${API_BASE}/api/evaluate/export-excel/${sessionId}`;
}

export async function cleanupSessionApi(sessionId: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/evaluate/cleanup/${sessionId}`, {
      method: "POST",
    });
  } catch (e) {
    console.error("Cleanup error:", e);
  }
}

export async function loadSampleDataApi(): Promise<{
  session_id: string;
  question_paper: string;
  answer_key: EvaluationRuleSet;
  scan_result: ScanResult;
}> {
  const res = await fetch(`${API_BASE}/api/samples/load`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load sample test data");
  }
  return res.json();
}
