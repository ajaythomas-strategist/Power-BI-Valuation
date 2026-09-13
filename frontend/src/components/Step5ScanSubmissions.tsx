"use client";

import React from "react";
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  ArrowLeft,
  Users,
  ShieldCheck,
  FileCheck2,
} from "lucide-react";
import { ScanResult } from "@/types";

interface Step5Props {
  scanResult: ScanResult;
  onRunEvaluation: () => void;
  onBack: () => void;
  isEvaluating: boolean;
}

export const Step5ScanSubmissions: React.FC<Step5Props> = ({
  scanResult,
  onRunEvaluation,
  onBack,
  isEvaluating,
}) => {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <Search className="w-5 h-5 text-blue-600" />
          <span>Step 5: Student Submissions Scan Results</span>
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          The scanner verified immediate student subfolders and detected Power BI Project structures.
        </p>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Total Folders */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Submissions
            </span>
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{scanResult.total_folders}</p>
          <span className="text-[11px] text-slate-400 mt-1 block">Subfolders discovered</span>
        </div>

        {/* Valid PBIPs */}
        <div className="bg-white p-5 rounded-xl border border-emerald-200 shadow-sm bg-emerald-50/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
              Valid Projects
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-700 mt-2">{scanResult.valid_count}</p>
          <span className="text-[11px] text-emerald-600 mt-1 block">Ready for evaluation</span>
        </div>

        {/* Missing Projects */}
        <div className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm bg-amber-50/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
              Missing PBIPs
            </span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-2">{scanResult.missing_count}</p>
          <span className="text-[11px] text-amber-600 mt-1 block">Empty student folders</span>
        </div>

        {/* Invalid Projects */}
        <div className="bg-white p-5 rounded-xl border border-rose-200 shadow-sm bg-rose-50/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-700 uppercase tracking-wider">
              Invalid / Corrupt
            </span>
            <XCircle className="w-4 h-4 text-rose-600" />
          </div>
          <p className="text-2xl font-bold text-rose-700 mt-2">{scanResult.invalid_count}</p>
          <span className="text-[11px] text-rose-600 mt-1 block">Exceptions isolated</span>
        </div>
      </div>

      {/* Non-blocking Notice */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 flex items-center space-x-2">
        <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>
          <strong>Fault-Tolerant Batch Execution:</strong> Submissions with missing or corrupted projects will be recorded as exceptions in the final Excel workbook. They will not halt the evaluation of valid students.
        </span>
      </div>

      {/* Scanned Student Submissions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <FileCheck2 className="w-4 h-4 text-slate-500" />
            <span>Detected Student Register Numbers</span>
          </h3>
          <span className="text-xs text-slate-500">
            {scanResult.items.length} Submissions Listed
          </span>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-6">Register No.</th>
                <th className="py-2.5 px-4">PBIP File</th>
                <th className="py-2.5 px-4">Report Folder</th>
                <th className="py-2.5 px-4">Model Folder / BIM</th>
                <th className="py-2.5 px-4">Integrity Status</th>
                <th className="py-2.5 px-6">Diagnostic Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scanResult.items.map((item) => (
                <tr key={item.register_no} className="hover:bg-slate-50/60">
                  {/* Register Number */}
                  <td className="py-3 px-6 font-bold text-slate-900">
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded font-mono">
                      {item.register_no}
                    </span>
                  </td>

                  {/* PBIP File */}
                  <td className="py-3 px-4">
                    {item.pbip_file_found ? (
                      <span className="text-emerald-700 font-medium flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> <span>Found</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">None</span>
                    )}
                  </td>

                  {/* Report Folder */}
                  <td className="py-3 px-4">
                    {item.report_folder_found ? (
                      <span className="text-emerald-700 font-medium flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> <span>Found</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">None</span>
                    )}
                  </td>

                  {/* Model Folder */}
                  <td className="py-3 px-4">
                    {item.model_folder_found ? (
                      <span className="text-emerald-700 font-medium flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> <span>Found</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">None</span>
                    )}
                  </td>

                  {/* Status Badge */}
                  <td className="py-3 px-4">
                    {item.is_valid ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                        Valid PBIP
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">
                        {item.issue_type || "Exception"}
                      </span>
                    )}
                  </td>

                  {/* Notes */}
                  <td className="py-3 px-6 text-slate-500 text-[11px] max-w-xs truncate">
                    {item.issue_message || "Structure verified successfully."}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Navigation Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          disabled={isEvaluating}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded-lg shadow-sm transition-all text-sm disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Step 4</span>
        </button>

        <button
          onClick={onRunEvaluation}
          disabled={scanResult.valid_count === 0 || isEvaluating}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <span>{isEvaluating ? "Evaluating Submissions..." : "Run Batch Evaluation"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
