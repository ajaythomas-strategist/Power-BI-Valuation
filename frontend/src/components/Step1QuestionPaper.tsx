"use client";

import React, { useState } from "react";
import { Upload, FileText, CheckCircle, ArrowRight, Eye, Sparkles } from "lucide-react";

import { extractDocumentTextApi } from "@/lib/api";

interface Step1Props {
  questionPaperText: string;
  onUpdateText: (text: string) => void;
  onNext: () => void;
  onUseSample: () => void;
}

export const Step1QuestionPaper: React.FC<Step1Props> = ({
  questionPaperText,
  onUpdateText,
  onNext,
  onUseSample,
}) => {
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  const handleFileUpload = async (file: File) => {
    setFileName(file.name);
    setFileSize((file.size / 1024).toFixed(1) + " KB");
    setIsExtracting(true);

    try {
      // Use backend extractor for DOCX / document formats
      const extracted = await extractDocumentTextApi(file);
      if (extracted && extracted.trim()) {
        onUpdateText(extracted);
      } else {
        // Fallback to text reader
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
      setIsExtracting(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <span>Step 1: Upload Question Paper</span>
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Provide the assessment document given to the students for review and audit trail.
            </p>
          </div>
          <button
            onClick={onUseSample}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Load Sample Question Paper</span>
          </button>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
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
          id="qp-file-input"
          className="hidden"
          accept=".txt,.md,.markdown,.pdf,.docx,.json"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
            <Upload className="w-6 h-6" />
          </div>

          <div>
            <label
              htmlFor="qp-file-input"
              className="text-sm font-semibold text-blue-600 hover:text-blue-700 cursor-pointer underline underline-offset-2"
            >
              Click to browse file
            </label>
            <span className="text-sm text-slate-500"> or drag and drop your Question Paper here</span>
          </div>
          <p className="text-xs text-slate-400">
            Supported formats: Markdown (.md), Plain Text (.txt), Word (.docx), PDF (.pdf)
          </p>

          {isExtracting ? (
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 font-medium mt-2 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
              <span>Extracting document text...</span>
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

      {/* Question Paper Content & Manual Editor */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
            <Eye className="w-4 h-4 text-slate-500" />
            <span>Question Paper Content (Preview & Edit)</span>
          </label>
          <span className="text-xs text-slate-400">
            {questionPaperText.length > 0
              ? `${questionPaperText.split("\n").length} lines loaded`
              : "Paste or type directly"}
          </span>
        </div>

        <textarea
          rows={10}
          value={questionPaperText}
          onChange={(e) => onUpdateText(e.target.value)}
          placeholder="Paste Question Paper contents here if not uploading a file..."
          className="w-full text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none leading-relaxed"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end">
        <button
          onClick={onNext}
          disabled={!questionPaperText.trim()}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <span>Continue to Step 2: Answer Key</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
