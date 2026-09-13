"use client";

import React from "react";
import {
  FileText,
  KeyRound,
  Sliders,
  FolderArchive,
  Search,
  Cpu,
  Award,
  FileSpreadsheet,
  Check,
} from "lucide-react";

export interface StepItem {
  id: number;
  label: string;
  icon: React.ElementType;
  description: string;
}

export const STEPS: StepItem[] = [
  { id: 1, label: "Question Paper", icon: FileText, description: "Upload assignment" },
  { id: 2, label: "Answer Key", icon: KeyRound, description: "Upload solutions" },
  { id: 3, label: "Review Rules", icon: Sliders, description: "Inspect & edit rules" },
  { id: 4, label: "Student Folder", icon: FolderArchive, description: "Select submissions" },
  { id: 5, label: "Scan Submissions", icon: Search, description: "Verify Register IDs" },
  { id: 6, label: "Evaluation", icon: Cpu, description: "Deterministic scoring" },
  { id: 7, label: "Results", icon: Award, description: "View student marks" },
  { id: 8, label: "Export Excel", icon: FileSpreadsheet, description: "Download report" },
];

interface StepperProps {
  currentStep: number;
  onSelectStep?: (step: number) => void;
  maxAccessibleStep: number;
}

export const Stepper: React.FC<StepperProps> = ({
  currentStep,
  onSelectStep,
  maxAccessibleStep,
}) => {
  return (
    <div className="bg-white border-b border-slate-200 py-3 px-4 sm:px-6 lg:px-8 shadow-sm">
      <div className="max-w-7xl mx-auto">
        <nav aria-label="Progress">
          <ol className="flex items-center justify-between w-full overflow-x-auto pb-1 gap-2 sm:gap-4 no-scrollbar">
            {STEPS.map((step, index) => {
              const isCompleted = step.id < currentStep;
              const isCurrent = step.id === currentStep;
              const isClickable = step.id <= maxAccessibleStep && onSelectStep;

              return (
                <li
                  key={step.id}
                  className={`flex-1 min-w-[110px] flex items-center ${
                    index !== STEPS.length - 1 ? "pr-2" : ""
                  }`}
                >
                  <button
                    onClick={() => isClickable && onSelectStep && onSelectStep(step.id)}
                    disabled={!isClickable}
                    className={`group flex items-center space-x-2.5 text-left w-full transition-all ${
                      isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-60"
                    }`}
                  >
                    {/* Circle Indicator */}
                    <span
                      className={`flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold transition-all ${
                        isCompleted
                          ? "bg-emerald-600 text-white shadow-sm"
                          : isCurrent
                          ? "bg-blue-600 text-white ring-4 ring-blue-100 shadow-sm"
                          : "bg-slate-100 text-slate-500 border border-slate-300"
                      }`}
                    >
                      {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : step.id}
                    </span>

                    {/* Step Label & Subtitle */}
                    <div className="hidden md:block">
                      <span
                        className={`block text-xs font-bold leading-tight ${
                          isCurrent
                            ? "text-blue-700"
                            : isCompleted
                            ? "text-slate-800"
                            : "text-slate-400"
                        }`}
                      >
                        {step.label}
                      </span>
                      <span className="block text-[10px] text-slate-400 font-medium">
                        {step.description}
                      </span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>
      </div>
    </div>
  );
};
