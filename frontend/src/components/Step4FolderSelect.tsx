"use client";

import React, { useState } from "react";
import {
  FolderArchive,
  Upload,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  AlertCircle,
  FolderTree,
} from "lucide-react";
import { scanSubmissionsApi } from "@/lib/api";
import { ScanResult } from "@/types";

interface Step4Props {
  onScanCompleted: (scanResult: ScanResult) => void;
  onNext: () => void;
  onBack: () => void;
  onUseSample: () => void;
}

export const Step4FolderSelect: React.FC<Step4Props> = ({
  onScanCompleted,
  onNext,
  onBack,
  onUseSample,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setScanError(null);
  };

  const handleScanSubmissions = async () => {
    if (!selectedFile) return;
    setIsScanning(true);
    setScanError(null);

    try {
      const scanResult = await scanSubmissionsApi(selectedFile);
      onScanCompleted(scanResult);
      onNext();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to scan submissions archive";
      setScanError(msg);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <FolderArchive className="w-5 h-5 text-blue-600" />
              <span>Step 4: Select Main Student Submissions Folder</span>
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Select the main folder or ZIP bundle containing individual student Register Number subfolders.
            </p>
          </div>
          <button
            onClick={onUseSample}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Load 5 Sample Submissions</span>
          </button>
        </div>
      </div>

      {/* Expected Folder Structure Guide Card */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center space-x-2 text-slate-800 font-bold text-xs uppercase tracking-wider">
          <FolderTree className="w-4 h-4 text-blue-600" />
          <span>Required Subfolder Hierarchy</span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          The application captures each student’s <strong>Register Number</strong> directly from the immediate subfolder name.
          Inside each subfolder, the Power BI project (.pbip, .Report, .Dataset/model.bim) is automatically detected.
        </p>

        {/* Tree Diagram */}
        <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-800 space-y-1">
          <div className="text-blue-700 font-bold">Main_Submissions_Folder/</div>
          <div className="pl-4 text-slate-700">├── <span className="text-emerald-700 font-bold">23001</span>/ <span className="text-slate-400">→ (Register No = 23001)</span></div>
          <div className="pl-8 text-slate-500">├── Student_Answer.pbip</div>
          <div className="pl-8 text-slate-500">└── Student_Answer.Report / Dataset / TMDL</div>
          <div className="pl-4 text-slate-700">├── <span className="text-emerald-700 font-bold">23002</span>/ <span className="text-slate-400">→ (Register No = 23002)</span></div>
          <div className="pl-8 text-slate-500">└── MySubmission.pbip</div>
          <div className="pl-4 text-slate-700">└── <span className="text-emerald-700 font-bold">23003</span>/ ...</div>
        </div>
      </div>

      {/* Upload Zone */}
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
            handleFileChange(e.dataTransfer.files[0]);
          }
        }}
        className={`bg-white border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? "border-blue-500 bg-blue-50/50"
            : selectedFile
            ? "border-emerald-400 bg-emerald-50/20"
            : "border-slate-300 hover:border-slate-400"
        }`}
      >
        <input
          type="file"
          id="student-folder-input"
          className="hidden"
          accept=".zip,.tar.gz"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileChange(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
            <Upload className="w-6 h-6" />
          </div>

          <div>
            <label
              htmlFor="student-folder-input"
              className="text-sm font-semibold text-blue-600 hover:text-blue-700 cursor-pointer underline underline-offset-2"
            >
              Browse and select Student Submissions ZIP archive
            </label>
            <span className="text-sm text-slate-500"> or drag and drop your .zip file here</span>
          </div>
          <p className="text-xs text-slate-400">
            Compress your Main Student Folder into a .zip file and upload for instantaneous batch processing.
          </p>

          {selectedFile && (
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium mt-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>{selectedFile.name}</span>
              <span className="text-emerald-600">
                ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Error Notification */}
      {scanError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Scan Issue: </span>
            <span>{scanError}</span>
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
          <span>Back to Step 3</span>
        </button>

        <button
          onClick={handleScanSubmissions}
          disabled={!selectedFile || isScanning}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <span>{isScanning ? "Scanning Folders..." : "Scan Submissions"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
