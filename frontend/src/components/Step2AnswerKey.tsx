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
  FolderArchive,
  Layers,
  FileCode,
  FileCheck,
} from "lucide-react";
import {
  extractDocumentTextApi,
  parseAnswerKeyApi,
  generateRulesFromMasterPBIPApi,
} from "@/lib/api";
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
  const [activeTab, setActiveTab] = useState<"pbip" | "spec">("pbip");
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [extractedSummary, setExtractedSummary] = useState<string | null>(null);

  // Handle Master PBIP ZIP upload
  const handleMasterPBIPUpload = async (file: File) => {
    setFileName(file.name);
    setFileSize((file.size / (1024 * 1024)).toFixed(2) + " MB");
    setParseError(null);
    setIsParsing(true);
    setExtractedSummary(null);

    try {
      const ruleSet = await generateRulesFromMasterPBIPApi(file, 100.0);
      const formattedJson = JSON.stringify(ruleSet, null, 2);
      onUpdateText(formattedJson);
      onRuleSetParsed(ruleSet);

      const totalCriteria = ruleSet.questions.reduce(
        (acc, q) => acc + q.criteria.length,
        0
      );
      setExtractedSummary(
        `Successfully extracted ${ruleSet.questions.length} questions (${totalCriteria} criteria) across DAX, Model, & Visuals (${ruleSet.total_marks} Marks total)`
      );
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to extract rules from Master PBIP";
      setParseError(msg);
    } finally {
      setIsParsing(false);
    }
  };

  // Handle JSON / YAML / DOCX / TXT upload
  const handleSpecUpload = async (file: File) => {
    setFileName(file.name);
    setFileSize((file.size / 1024).toFixed(1) + " KB");
    setParseError(null);
    setIsParsing(true);
    setExtractedSummary(null);

    try {
      const ext = file.name.toLowerCase();
      if (ext.endsWith(".zip") || ext.endsWith(".pbip")) {
        // Automatically route to Master PBIP parser
        await handleMasterPBIPUpload(file);
        return;
      }

      const extracted = await extractDocumentTextApi(file);
      if (extracted && extracted.trim()) {
        onUpdateText(extracted);
      } else {
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target?.result as string;
          onUpdateText(content);
        };
        reader.readAsText(file);
      }
    } catch {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        onUpdateText(content);
      };
      reader.readAsText(file);
    } finally {
      setIsParsing(false);
    }
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
      const msg =
        err instanceof Error ? err.message : "Failed to parse answer key";
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
      setExtractedSummary(
        `Auto-parsed ${ruleSet.questions.length} questions from Question Paper.`
      );
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Could not auto-generate rules";
      setParseError("Could not auto-generate rules from question paper. " + msg);
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <KeyRound className="w-5 h-5 text-blue-600" />
              <span>Step 2: Upload Answer Key or Master Solution</span>
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Provide the Master Power BI Solution Project or upload an Answer Key specification.
            </p>
          </div>
          <div className="flex items-center space-x-2 flex-wrap gap-y-2">
            <button
              onClick={onUseSample}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Load Sample Key</span>
            </button>
            {questionPaperText && (
              <button
                onClick={handleAutoGenerate}
                disabled={isParsing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md transition-colors disabled:opacity-50"
              >
                <Code2 className="w-3.5 h-3.5 text-slate-600" />
                <span>Parse from Question Paper</span>
              </button>
            )}
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center space-x-3 mt-6 border-b border-slate-200">
          <button
            onClick={() => setActiveTab("pbip")}
            className={`flex items-center space-x-2 pb-3 px-1 text-sm font-semibold border-b-2 transition-all ${
              activeTab === "pbip"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <FolderArchive className="w-4 h-4" />
            <span>Master Power BI Project (.pbip / .zip)</span>
            <span className="text-[10px] uppercase font-bold bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
              Recommended
            </span>
          </button>

          <button
            onClick={() => setActiveTab("spec")}
            className={`flex items-center space-x-2 pb-3 px-1 text-sm font-semibold border-b-2 transition-all ${
              activeTab === "spec"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>Specification File (JSON / YAML / DOCX / TXT)</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Master PBIP Upload */}
      {activeTab === "pbip" ? (
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
              handleMasterPBIPUpload(e.dataTransfer.files[0]);
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
            id="master-pbip-input"
            className="hidden"
            accept=".zip,.pbip,.rar,.7z"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleMasterPBIPUpload(e.target.files[0]);
              }
            }}
          />

          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
              <Layers className="w-6 h-6" />
            </div>

            <div>
              <label
                htmlFor="master-pbip-input"
                className="text-sm font-semibold text-blue-600 hover:text-blue-700 cursor-pointer underline underline-offset-2"
              >
                Click to browse Master PBIP Solution ZIP
              </label>
              <span className="text-sm text-slate-500"> or drag and drop here</span>
            </div>
            <p className="text-xs text-slate-400 max-w-lg">
              Upload the trainer&apos;s Solution Power BI Project (.pbip zipped). The system automatically extracts DAX formulas, schema tables, relationships, and visual configurations.
            </p>

            {isParsing ? (
              <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 font-medium mt-2 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                <span>Parsing Master PBIP & synthesizing rules...</span>
              </div>
            ) : fileName ? (
              <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium mt-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>{fileName}</span>
                <span className="text-emerald-600">({fileSize})</span>
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        /* Tab 2: Standard Specification Upload */
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
              handleSpecUpload(e.dataTransfer.files[0]);
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
            accept=".json,.yaml,.yml,.csv,.txt,.docx,.doc,.md"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleSpecUpload(e.target.files[0]);
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
              Supports JSON, YAML, CSV, Word (.docx), or structured criteria text
            </p>

            {isParsing ? (
              <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 font-medium mt-2 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                <span>Reading document text...</span>
              </div>
            ) : fileName ? (
              <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium mt-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>{fileName}</span>
                <span className="text-emerald-600">({fileSize})</span>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Success Extraction Summary Banner */}
      {extractedSummary && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-3 text-emerald-900 text-sm">
          <FileCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span className="font-medium">{extractedSummary}</span>
        </div>
      )}

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
            <span>Synthesized Answer Key Specification (JSON)</span>
          </label>
          <span className="text-xs text-slate-400">
            {answerKeyText.length > 0 ? `${(answerKeyText.length / 1024).toFixed(1)} KB loaded` : "Empty"}
          </span>
        </div>

        <textarea
          rows={11}
          value={answerKeyText}
          onChange={(e) => onUpdateText(e.target.value)}
          placeholder="Answer key specification will populate here automatically from Master PBIP or uploaded file..."
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
          <span>{isParsing ? "Processing..." : "Review Evaluation Rules"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

