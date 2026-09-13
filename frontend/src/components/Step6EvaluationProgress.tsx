"use client";

import React, { useEffect, useState } from "react";
import { Cpu, Loader2 } from "lucide-react";
import { ScanResult } from "@/types";

interface Step6Props {
  scanResult: ScanResult;
  onFinished: () => void;
}

export const Step6EvaluationProgress: React.FC<Step6Props> = ({
  scanResult,
  onFinished,
}) => {
  const [progress, setProgress] = useState(15);
  const [currentStudentIndex, setCurrentStudentIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Initializing evaluation engine...");

  const total = scanResult.items.length || 5;

  useEffect(() => {
    const studentList = scanResult.items.map((i) => i.register_no);
    const stages = [
      "Parsing Semantic Model and tables...",
      "Analyzing DAX formulas and measure AST...",
      "Matching Report visual types and axis fields...",
      "Calculating deterministic marks and remarks...",
    ];

    let currentIdx = 0;
    let stageIdx = 0;

    const interval = setInterval(() => {
      if (currentIdx < studentList.length) {
        const reg = studentList[currentIdx];
        const stage = stages[stageIdx % stages.length];
        setStatusMessage(`Evaluating Student Register No: ${reg} — ${stage}`);
        setCurrentStudentIndex(currentIdx + 1);

        stageIdx++;
        if (stageIdx % stages.length === 0) {
          currentIdx++;
        }

        const pct = Math.min(
          95,
          Math.round(((currentIdx * stages.length + (stageIdx % stages.length)) / (studentList.length * stages.length)) * 100)
        );
        setProgress(Math.max(15, pct));
      } else {
        setProgress(100);
        setStatusMessage("Finalizing evaluation summaries and Excel report...");
        clearInterval(interval);
        setTimeout(() => {
          onFinished();
        }, 600);
      }
    }, 280);

    return () => clearInterval(interval);
  }, [scanResult, onFinished]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center space-y-6">
        {/* Animated Icon */}
        <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>

        {/* Title & Stage */}
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-slate-900">
            Evaluating Student Power BI Projects
          </h2>
          <p className="text-sm text-slate-500 font-medium">
            Running rule-based deterministic evaluation question-by-question...
          </p>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-600">
            <span>Progress: {currentStudentIndex} of {total} Submissions</span>
            <span className="text-blue-600 font-bold">{progress}%</span>
          </div>
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Live Status Ticker */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-700 flex items-center justify-center space-x-2">
          <Cpu className="w-4 h-4 text-blue-600 flex-shrink-0 animate-pulse" />
          <span className="truncate">{statusMessage}</span>
        </div>

        {/* Ephemeral Processing Notice */}
        <p className="text-[11px] text-slate-400">
          Zero permanent storage: all student files are processed in ephemeral memory and discarded upon completion.
        </p>
      </div>
    </div>
  );
};
