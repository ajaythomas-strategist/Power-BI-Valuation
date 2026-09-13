"use client";

import React from "react";
import {
  Download,
  CheckCircle2,
  RotateCcw,
  ShieldCheck,
  TableProperties,
} from "lucide-react";
import { BatchEvaluationSummary } from "@/types";
import { getExcelDownloadUrl, cleanupSessionApi } from "@/lib/api";

interface Step8Props {
  summary: BatchEvaluationSummary;
  onNewEvaluation: () => void;
}

export const Step8Export: React.FC<Step8Props> = ({ summary, onNewEvaluation }) => {
  const downloadUrl = getExcelDownloadUrl(summary.session_id);

  const handleDownload = () => {
    window.location.href = downloadUrl;
  };

  const handleFinishAndReset = async () => {
    await cleanupSessionApi(summary.session_id);
    onNewEvaluation();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Hero Card */}
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-100 shadow-sm">
          <CheckCircle2 className="w-8 h-8 text-emerald-600" />
        </div>

        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-slate-900">
            Evaluation Completed Successfully
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            All student PBIP models and report visuals were deterministically evaluated against the official Answer Key rules.
          </p>
        </div>

        {/* Quick Stats Banner */}
        <div className="grid grid-cols-3 gap-3 max-w-xl mx-auto py-2">
          <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-500 uppercase block">
              Evaluated
            </span>
            <span className="text-lg font-bold text-slate-900">
              {summary.evaluated_count} Students
            </span>
          </div>

          <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-500 uppercase block">
              Questions
            </span>
            <span className="text-lg font-bold text-slate-900">
              {summary.rule_set.questions.length} Evaluated
            </span>
          </div>

          <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-500 uppercase block">
              Exceptions
            </span>
            <span className="text-lg font-bold text-slate-900">
              {summary.exception_count} Recorded
            </span>
          </div>
        </div>

        {/* Primary Download CTA */}
        <div className="pt-2">
          <button
            onClick={handleDownload}
            className="inline-flex items-center space-x-2.5 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg transition-all text-base group"
          >
            <Download className="w-5 h-5 group-hover:-translate-y-0.5 transition-transform" />
            <span>Download Excel Report (.xlsx)</span>
          </button>
          <p className="text-xs text-slate-400 mt-2">
            Includes professional header styling, freeze panes, auto-fit column widths, formulas, and 4 audit sheets.
          </p>
        </div>
      </div>

      {/* 4-Sheet Architecture Visual Guide */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
          <TableProperties className="w-4 h-4 text-blue-600" />
          <span>Workbook Sheets Breakdown</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {/* Sheet 1 */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
            <span className="font-bold text-blue-700 block">Sheet 1: Summary</span>
            <p className="text-slate-600 leading-relaxed">
              Consolidated register numbers, total marks, percentage, question breakdown, and status color coding with overall class average formulas.
            </p>
          </div>

          {/* Sheet 2 */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
            <span className="font-bold text-blue-700 block">Sheet 2: Question-wise Evaluation</span>
            <p className="text-slate-600 leading-relaxed">
              Detailed audit trail per student question, showing exact student implementation vs expected requirements and awarded marks.
            </p>
          </div>

          {/* Sheet 3 */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
            <span className="font-bold text-blue-700 block">Sheet 3: Exceptions</span>
            <p className="text-slate-600 leading-relaxed">
              Diagnostic log of any student submissions with missing PBIP projects, corrupted JSON, or malformed folder structures.
            </p>
          </div>

          {/* Sheet 4 */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
            <span className="font-bold text-blue-700 block">Sheet 4: Evaluation Rules</span>
            <p className="text-slate-600 leading-relaxed">
              Authoritative record of the parsed Answer Key criteria and accepted variations used during this evaluation session.
            </p>
          </div>
        </div>
      </div>

      {/* Reset & Ephemeral Storage Cleanup */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center space-x-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Temporary student files and evaluation cache will be cleaned on session exit.</span>
        </div>

        <button
          onClick={handleFinishAndReset}
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-lg shadow-sm transition-all text-xs"
        >
          <RotateCcw className="w-4 h-4 text-slate-600" />
          <span>Complete Session & Clean Temp Files</span>
        </button>
      </div>
    </div>
  );
};
