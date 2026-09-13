"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { Stepper } from "@/components/Stepper";
import { Step1QuestionPaper } from "@/components/Step1QuestionPaper";
import { Step2AnswerKey } from "@/components/Step2AnswerKey";
import { Step3ReviewRules } from "@/components/Step3ReviewRules";
import { Step4FolderSelect } from "@/components/Step4FolderSelect";
import { Step5ScanSubmissions } from "@/components/Step5ScanSubmissions";
import { Step6EvaluationProgress } from "@/components/Step6EvaluationProgress";
import { Step7Results } from "@/components/Step7Results";
import { Step8Export } from "@/components/Step8Export";

import {
  checkBackendHealth,
  loadSampleDataApi,
  runEvaluationApi,
  cleanupSessionApi,
} from "@/lib/api";
import {
  EvaluationRuleSet,
  ScanResult,
  BatchEvaluationSummary,
} from "@/types";

export default function Home() {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [maxAccessibleStep, setMaxAccessibleStep] = useState<number>(1);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);

  // Workflow state
  const [sessionId, setSessionId] = useState<string>("");
  const [questionPaperText, setQuestionPaperText] = useState<string>("");
  const [answerKeyText, setAnswerKeyText] = useState<string>("");
  const [ruleSet, setRuleSet] = useState<EvaluationRuleSet>({
    title: "Power BI Evaluation",
    total_marks: 100,
    questions: [],
  });
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [evaluationSummary, setEvaluationSummary] = useState<BatchEvaluationSummary | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // Check backend health on mount
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      const isHealthy = await checkBackendHealth();
      if (isMounted) setBackendConnected(isHealthy);
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const goToStep = (step: number) => {
    setCurrentStep(step);
    if (step > maxAccessibleStep) {
      setMaxAccessibleStep(step);
    }
  };

  const handleNewEvaluation = async () => {
    if (sessionId) {
      await cleanupSessionApi(sessionId);
    }
    setCurrentStep(1);
    setMaxAccessibleStep(1);
    setSessionId("");
    setQuestionPaperText("");
    setAnswerKeyText("");
    setRuleSet({
      title: "Power BI Evaluation",
      total_marks: 100,
      questions: [],
    });
    setScanResult(null);
    setEvaluationSummary(null);
    setIsEvaluating(false);
  };

  const handleUseSample = async () => {
    try {
      const sampleData = await loadSampleDataApi();
      setSessionId(sampleData.session_id);
      setQuestionPaperText(sampleData.question_paper);
      setAnswerKeyText(JSON.stringify(sampleData.answer_key, null, 2));
      setRuleSet(sampleData.answer_key);
      setScanResult(sampleData.scan_result);
      setMaxAccessibleStep(5);
      goToStep(3); // Take trainer directly to Step 3 (Review Rules) to inspect
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "An error occurred";
      alert("Failed to load sample test data: " + errorMsg);
    }
  };

  const handleRunEvaluation = async () => {
    if (!sessionId || !scanResult) return;
    setIsEvaluating(true);
    goToStep(6); // Step 6: Evaluation Progress

    try {
      const summary = await runEvaluationApi(sessionId, ruleSet);
      setEvaluationSummary(summary);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "An error occurred";
      alert("Evaluation failed: " + errorMsg);
      goToStep(5);
      setIsEvaluating(false);
    }
  };

  const handleEvaluationFinished = () => {
    setIsEvaluating(false);
    goToStep(7); // Step 7: Results
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col selection:bg-blue-100 selection:text-blue-900">
      {/* Top Navbar */}
      <Navbar
        backendConnected={backendConnected}
        onNewEvaluation={handleNewEvaluation}
        onTryDemo={handleUseSample}
        isEvaluating={isEvaluating}
      />

      {/* 8-Step Navigation Bar */}
      <Stepper
        currentStep={currentStep}
        maxAccessibleStep={maxAccessibleStep}
        onSelectStep={(step) => !isEvaluating && goToStep(step)}
      />

      {/* Main Assessment Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step 1: Upload Question Paper */}
        {currentStep === 1 && (
          <Step1QuestionPaper
            questionPaperText={questionPaperText}
            onUpdateText={setQuestionPaperText}
            onNext={() => goToStep(2)}
            onUseSample={handleUseSample}
          />
        )}

        {/* Step 2: Upload Answer Key */}
        {currentStep === 2 && (
          <Step2AnswerKey
            answerKeyText={answerKeyText}
            onUpdateText={setAnswerKeyText}
            onRuleSetParsed={(parsed) => setRuleSet(parsed)}
            onNext={() => goToStep(3)}
            onBack={() => goToStep(1)}
            onUseSample={handleUseSample}
            questionPaperText={questionPaperText}
          />
        )}

        {/* Step 3: Review & Edit Evaluation Rules */}
        {currentStep === 3 && (
          <Step3ReviewRules
            ruleSet={ruleSet}
            onUpdateRuleSet={setRuleSet}
            onNext={() => {
              if (scanResult) {
                goToStep(5);
              } else {
                goToStep(4);
              }
            }}
            onBack={() => goToStep(2)}
          />
        )}

        {/* Step 4: Select Main Student Folder / ZIP */}
        {currentStep === 4 && (
          <Step4FolderSelect
            onScanCompleted={(scanned) => {
              setScanResult(scanned);
              setSessionId(scanned.session_id);
            }}
            onNext={() => goToStep(5)}
            onBack={() => goToStep(3)}
            onUseSample={handleUseSample}
          />
        )}

        {/* Step 5: Scan Submissions Summary */}
        {currentStep === 5 && scanResult && (
          <Step5ScanSubmissions
            scanResult={scanResult}
            onRunEvaluation={handleRunEvaluation}
            onBack={() => goToStep(4)}
            isEvaluating={isEvaluating}
          />
        )}

        {/* Step 6: Evaluation Progress */}
        {currentStep === 6 && scanResult && (
          <Step6EvaluationProgress
            scanResult={scanResult}
            onFinished={handleEvaluationFinished}
          />
        )}

        {/* Step 7: Consolidated Results */}
        {currentStep === 7 && evaluationSummary && (
          <Step7Results
            summary={evaluationSummary}
            onNext={() => goToStep(8)}
            onBack={() => goToStep(5)}
          />
        )}

        {/* Step 8: Export Excel */}
        {currentStep === 8 && evaluationSummary && (
          <Step8Export
            summary={evaluationSummary}
            onNewEvaluation={handleNewEvaluation}
          />
        )}
      </main>

      {/* Institutional Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-4 sm:px-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Power BI Answer Evaluator — Automated Project Assessment Platform
          </span>
          <span>
            Strict Rule-Based & Deterministic Engine • Ephemeral Session Processing
          </span>
        </div>
      </footer>
    </div>
  );
}
