"use client";

import React, { useState } from "react";
import {
  Award,
  Users,
  TrendingUp,
  AlertTriangle,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  X,
  Check,
  AlertCircle,
} from "lucide-react";
import {
  BatchEvaluationSummary,
  StudentEvaluationResult,
  EvaluationStatus,
} from "@/types";

interface Step7Props {
  summary: BatchEvaluationSummary;
  onNext: () => void;
  onBack: () => void;
}

export const Step7Results: React.FC<Step7Props> = ({ summary, onNext, onBack }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [selectedStudent, setSelectedStudent] = useState<StudentEvaluationResult | null>(null);

  // Filter results
  const filteredResults = summary.results.filter((res) => {
    const matchesSearch = res.register_no.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "CORRECT" && res.status === EvaluationStatus.CORRECT) ||
      (statusFilter === "PARTIAL" && res.status === EvaluationStatus.PARTIAL) ||
      (statusFilter === "INCORRECT" && res.status === EvaluationStatus.INCORRECT) ||
      (statusFilter === "EXCEPTION" && res.status === EvaluationStatus.EXCEPTION);

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <Award className="w-5 h-5 text-blue-600" />
            <span>Step 7: Consolidated Evaluation Results</span>
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Question-by-question deterministic marks awarded to student submissions.
          </p>
        </div>
        <button
          onClick={onNext}
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all text-sm"
        >
          <span>Export Excel Report</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4">
        {/* Total Students */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Total Evaluated</span>
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{summary.evaluated_count}</p>
          <span className="text-[11px] text-slate-400 mt-0.5 block">
            out of {summary.total_students} submissions
          </span>
        </div>

        {/* Class Average */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Average Score</span>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">
            {summary.average_score} <span className="text-sm font-normal text-slate-400">/ {summary.rule_set.total_marks}</span>
          </p>
          <span className="text-[11px] text-emerald-600 font-semibold mt-0.5 block">
            {Math.round((summary.average_score / (summary.rule_set.total_marks || 100)) * 100)}% Average
          </span>
        </div>

        {/* Highest Score */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-emerald-200 shadow-sm bg-emerald-50/10">
          <div className="flex items-center justify-between text-emerald-700 text-xs font-semibold uppercase">
            <span>Highest Score</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-700 mt-2">{summary.highest_score}</p>
          <span className="text-[11px] text-emerald-600 mt-0.5 block">Maximum awarded</span>
        </div>

        {/* Lowest Score */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-amber-200 shadow-sm bg-amber-50/10">
          <div className="flex items-center justify-between text-amber-700 text-xs font-semibold uppercase">
            <span>Lowest Score</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-2">{summary.lowest_score}</p>
          <span className="text-[11px] text-amber-600 mt-0.5 block">Minimum evaluated</span>
        </div>

        {/* Exceptions */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200 shadow-sm col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Exceptions</span>
            <AlertCircle className="w-4 h-4 text-rose-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{summary.exception_count}</p>
          <span className="text-[11px] text-rose-600 mt-0.5 block">Missing/Invalid files</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Register Number..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          {[
            { id: "ALL", label: "All Students" },
            { id: "CORRECT", label: "Full Marks" },
            { id: "PARTIAL", label: "Partial" },
            { id: "INCORRECT", label: "Low Score" },
            { id: "EXCEPTION", label: "Exceptions" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                statusFilter === f.id
                  ? "bg-blue-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Consolidated Results Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-6">Register No.</th>
                <th className="py-3 px-4 text-right">Total Marks</th>
                <th className="py-3 px-4 text-right">Max Marks</th>
                <th className="py-3 px-4 text-right">Percentage</th>
                <th className="py-3 px-4 text-center">Questions Breakdown</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-6 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredResults.map((res) => (
                <tr key={res.register_no} className="hover:bg-slate-50/70">
                  {/* Register Number */}
                  <td className="py-3.5 px-6 font-bold text-slate-900">
                    <span className="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-800">
                      {res.register_no}
                    </span>
                  </td>

                  {/* Marks */}
                  <td className="py-3.5 px-4 text-right font-bold text-slate-900">
                    {res.status === EvaluationStatus.EXCEPTION ? "—" : res.total_marks}
                  </td>

                  {/* Max Marks */}
                  <td className="py-3.5 px-4 text-right text-slate-500">
                    {res.maximum_marks}
                  </td>

                  {/* Percentage */}
                  <td className="py-3.5 px-4 text-right font-semibold">
                    {res.status === EvaluationStatus.EXCEPTION ? (
                      <span className="text-slate-400">N/A</span>
                    ) : (
                      <span
                        className={
                          res.percentage >= 80
                            ? "text-emerald-700"
                            : res.percentage >= 50
                            ? "text-blue-700"
                            : "text-rose-700"
                        }
                      >
                        {res.percentage}%
                      </span>
                    )}
                  </td>

                  {/* Questions Breakdown */}
                  <td className="py-3.5 px-4 text-center">
                    {res.status === EvaluationStatus.EXCEPTION ? (
                      <span className="text-slate-400 text-[11px]">Exception</span>
                    ) : (
                      <div className="inline-flex items-center space-x-2 text-[11px] font-semibold">
                        <span className="text-emerald-700" title="Correct">
                          ✓ {res.questions_correct}
                        </span>
                        <span className="text-amber-700" title="Partially Correct">
                          ~ {res.questions_partially_correct}
                        </span>
                        <span className="text-rose-700" title="Incorrect">
                          ✗ {res.questions_incorrect}
                        </span>
                      </div>
                    )}
                  </td>

                  {/* Status Badge */}
                  <td className="py-3.5 px-4 text-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        res.status === EvaluationStatus.CORRECT
                          ? "bg-emerald-100 text-emerald-800"
                          : res.status === EvaluationStatus.PARTIAL
                          ? "bg-amber-100 text-amber-800"
                          : res.status === EvaluationStatus.EXCEPTION
                          ? "bg-slate-100 text-slate-700"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {res.status}
                    </span>
                  </td>

                  {/* Detail Action */}
                  <td className="py-3.5 px-6 text-center">
                    <button
                      onClick={() => setSelectedStudent(res)}
                      className="inline-flex items-center space-x-1 px-3 py-1 bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-200 rounded-md transition-colors text-xs font-semibold"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Details</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student Question-by-Question Detail Modal */}
      {selectedStudent && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-3">
                <span className="font-mono text-base font-bold text-white bg-blue-600 px-3 py-1 rounded-lg">
                  {selectedStudent.register_no}
                </span>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Student Evaluation Breakdown
                  </h3>
                  <p className="text-xs text-slate-500">
                    Score: {selectedStudent.total_marks} / {selectedStudent.maximum_marks} ({selectedStudent.percentage}%) — {selectedStudent.status}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedStudent(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4">
              {selectedStudent.exception ? (
                <div className="p-5 bg-rose-50 border border-rose-200 rounded-xl space-y-2">
                  <div className="flex items-center space-x-2 text-rose-800 font-bold text-sm">
                    <AlertCircle className="w-5 h-5 text-rose-600" />
                    <span>Submission Exception</span>
                  </div>
                  <p className="text-xs text-rose-900 font-medium">
                    {selectedStudent.exception.description}
                  </p>
                  {selectedStudent.exception.details && (
                    <p className="text-[11px] font-mono text-rose-700 bg-rose-100/50 p-2 rounded">
                      {selectedStudent.exception.details}
                    </p>
                  )}
                </div>
              ) : (
                selectedStudent.question_details.map((qd) => (
                  <div
                    key={qd.question_id}
                    className="border border-slate-200 rounded-xl p-4 bg-white shadow-xs space-y-3"
                  >
                    {/* Question Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                          {qd.question_id}
                        </span>
                        <span className="font-semibold text-slate-900 text-xs">
                          {qd.question_text}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-900">
                          {qd.marks_awarded} / {qd.maximum_marks} Marks
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            qd.status === EvaluationStatus.CORRECT
                              ? "bg-emerald-100 text-emerald-800"
                              : qd.status === EvaluationStatus.PARTIAL
                              ? "bg-amber-100 text-amber-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {qd.status}
                        </span>
                      </div>
                    </div>

                    {/* Criteria Breakdown */}
                    <div className="bg-slate-50 rounded-lg p-3 space-y-2 text-xs">
                      {qd.criteria_results.map((cr, idx) => (
                        <div
                          key={cr.criterion_id || idx}
                          className="flex items-start justify-between border-b border-slate-200/60 pb-1.5 last:border-0 last:pb-0"
                        >
                          <div className="space-y-0.5 flex-1 pr-4">
                            <div className="flex items-center space-x-1.5 font-medium text-slate-800">
                              {cr.is_met ? (
                                <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                              ) : (
                                <X className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
                              )}
                              <span>{cr.title}</span>
                            </div>
                            <div className="text-[11px] text-slate-500 pl-5">
                              <span>Expected: </span>
                              <code className="text-slate-700 bg-slate-200/60 px-1 rounded">
                                {cr.expected_value}
                              </code>
                              <span className="mx-1">|</span>
                              <span>Found: </span>
                              <code className="text-slate-700 bg-slate-200/60 px-1 rounded">
                                {cr.student_value || "None"}
                              </code>
                            </div>
                            {cr.remarks && (
                              <p className="text-[11px] text-blue-700 pl-5 italic">
                                ↳ {cr.remarks}
                              </p>
                            )}
                          </div>
                          <span className="font-bold text-xs text-slate-900 whitespace-nowrap">
                            {cr.marks_awarded} / {cr.maximum_marks}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedStudent(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded-lg shadow-sm transition-all text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Scans</span>
        </button>

        <button
          onClick={onNext}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all text-sm"
        >
          <span>Continue to Step 8: Export Excel</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
