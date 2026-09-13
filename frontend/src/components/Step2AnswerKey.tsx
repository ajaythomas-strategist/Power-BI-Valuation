"use client";

import React, { useState } from "react";
import {
  KeyRound,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Code2,
  AlertCircle,
} from "lucide-react";
import { parseAnswerKeyApi } from "@/lib/api";
import { EvaluationRuleSet } from "@/types";

interface Step2Props {
  answerKeyText: string;
  onUpdateText: (text: string) => void;
  onRuleSetParsed: (ruleSet: EvaluationRuleSet) => void;
  onNext: () => void;
  onBack: () => void;
  onUseSample: () => void;
  questionPaperText: string;
}

export const Step2AnswerKey: React.FC<Step2Props> = ({
  answerKeyText,
  onUpdateText,
  onRuleSetParsed,
  onNext,
  onBack,
  onUseSample,
  questionPaperText,
}) => {
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleFileUpload = (file: File) => {
    setFileName(file.name);
    setFileSize((file.size / 1024).toFixed(1) + " KB");
    setParseError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      onUpdateText(content);
    };
    reader.readAsText(file);
  };

  const handleParseAndProceed = async () => {
    if (!answerKeyText.trim()) return;
    setIsParsing(true);
    setParseError(null);

    try {
      const ruleSet = await parseAnswerKeyApi(undefined, answerKeyText);
      onRuleSetParsed(ruleSet);
      onNext();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse answer key";
      setParseError(msg);
    } finally {
      setIsParsing(false);
    }
  };

  const handleAutoGenerate = async () => {
    if (!questionPaperText.trim()) return;
    setIsParsing(true);
    setParseError(null);

    try {
      const ruleSet = await parseAnswerKeyApi(undefined, questionPaperText);
      onUpdateText(JSON.stringify(ruleSet, null, 2));
      onRuleSetParsed(ruleSet);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not auto-generate rules";
      setParseError("Could not auto-generate rules from question paper. " + msg);
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <KeyRound className="w-5 h-5 text-blue-600" />
              <span>Step 2: Upload Answer Key</span>
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              The Answer Key is the authoritative specification for machine-verifiable evaluation rules.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={onUseSample}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Load Official Sample Key</span>
            </button>
            {questionPaperText && (
              <button
                onClick={handleAutoGenerate}
                disabled={isParsing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md transition-colors disabled:opacity-50"
              >
                <Code2 className="w-3.5 h-3.5 text-slate-600" />
                <span>Auto-Parse from Question Paper</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Upload Box */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        className={`bg-white border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? "border-blue-500 bg-blue-50/50"
            : fileName
            ? "border-emerald-400 bg-emerald-50/20"
            : "border-slate-300 hover:border-slate-400"
        }`}
      >
        <input
          type="file"
          id="ak-file-input"
          className="hidden"
          accept=".json,.yaml,.yml,.csv,.txt"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
            <KeyRound className="w-6 h-6" />
          </div>

          <div>
            <label
              htmlFor="ak-file-input"
              className="text-sm font-semibold text-blue-600 hover:text-blue-700 cursor-pointer underline underline-offset-2"
            >
              Click to browse Answer Key file
            </label>
            <span className="text-sm text-slate-500"> or drag and drop here</span>
          </div>
          <p className="text-xs text-slate-400">
            Supports JSON, YAML, CSV, or structured criteria text
          </p>

          {fileName && (
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium mt-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>{fileName}</span>
              <span className="text-emerald-600">({fileSize})</span>
            </div>
          )}
        </div>
      </div>

      {/* Parse Error Notification */}
      {parseError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Parsing Issue: </span>
            <span>{parseError}</span>
          </div>
        </div>
      )}

      {/* Editor Preview */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
            <Code2 className="w-4 h-4 text-slate-500" />
            <span>Answer Key Specification</span>
          </label>
          <span className="text-xs text-slate-400">
            {answerKeyText.length > 0 ? "Specification loaded" : "Empty"}
          </span>
        </div>

        <textarea
          rows={11}
          value={answerKeyText}
          onChange={(e) => onUpdateText(e.target.value)}
          placeholder="Paste JSON or structured Answer Key specification here..."
          className="w-full text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none leading-relaxed"
        />
      </div>

      {/* Navigation Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded-lg shadow-sm transition-all text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Step 1</span>
        </button>

        <button
          onClick={handleParseAndProceed}
          disabled={!answerKeyText.trim() || isParsing}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <span>{isParsing ? "Parsing Rules..." : "Review Evaluation Rules"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
