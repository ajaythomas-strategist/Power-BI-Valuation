"use client";

import React from "react";
import { Sparkles, RotateCcw, BarChart3 } from "lucide-react";

interface NavbarProps {
  backendConnected: boolean;
  onNewEvaluation: () => void;
  onTryDemo: () => void;
  isEvaluating?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  backendConnected,
  onNewEvaluation,
  onTryDemo,
  isEvaluating,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={onNewEvaluation}>
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold text-slate-900 tracking-tight">
                  Power BI Answer Evaluator
                </span>
                <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded border border-blue-200">
                  Phase 1
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Automated Power BI Project Assessment Platform
              </p>
            </div>
          </div>

          {/* Status & Actions */}
          <div className="flex items-center space-x-4">
            {/* Backend Status Pill */}
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
                backendConnected
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-rose-50 text-rose-700 border-rose-200"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                }`}
              />
              <span>{backendConnected ? "Backend Ready" : "Backend Offline"}</span>
            </div>

            {/* Quick Demo Button */}
            <button
              onClick={onTryDemo}
              disabled={isEvaluating}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors shadow-sm disabled:opacity-50"
              title="Loads sample Question Paper, Answer Key, and 5 student submissions instantly"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Instant Sample Demo</span>
            </button>

            {/* New Evaluation Reset Button */}
            <button
              onClick={onNewEvaluation}
              disabled={isEvaluating}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-md transition-colors shadow-sm disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
              <span>New Assessment</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
