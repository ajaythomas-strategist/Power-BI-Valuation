"use client";

import React, { useState } from "react";
import {
  Sliders,
  Plus,
  Trash2,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Award,
} from "lucide-react";
import { EvaluationRuleSet, EvaluationRule, CriterionRule, TargetComponent } from "@/types";

interface Step3Props {
  ruleSet: EvaluationRuleSet;
  onUpdateRuleSet: (ruleSet: EvaluationRuleSet) => void;
  onNext: () => void;
  onBack: () => void;
}

export const Step3ReviewRules: React.FC<Step3Props> = ({
  ruleSet,
  onUpdateRuleSet,
  onNext,
  onBack,
}) => {
  const [questions, setQuestions] = useState<EvaluationRule[]>(ruleSet.questions || []);

  const totalCalculatedMarks = questions.reduce((acc, q) => acc + (Number(q.marks) || 0), 0);

  const handleUpdateQuestion = (qIndex: number, updated: Partial<EvaluationRule>) => {
    const updatedList = [...questions];
    updatedList[qIndex] = { ...updatedList[qIndex], ...updated };
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList, total_marks: totalCalculatedMarks });
  };

  const handleUpdateCriterion = (
    qIndex: number,
    cIndex: number,
    updated: Partial<CriterionRule>
  ) => {
    const updatedList = [...questions];
    const updatedCriteria = [...updatedList[qIndex].criteria];
    updatedCriteria[cIndex] = { ...updatedCriteria[cIndex], ...updated };
    updatedList[qIndex].criteria = updatedCriteria;
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList });
  };

  const handleAddCriterion = (qIndex: number) => {
    const updatedList = [...questions];
    const newId = `C${updatedList[qIndex].criteria.length + 1}`;
    updatedList[qIndex].criteria.push({
      id: newId,
      title: "New Criterion",
      component: TargetComponent.VISUAL,
      target_property: "visual_type",
      expected_value: "Line Chart",
      accepted_variations: [],
      marks: 5.0,
    });
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList });
  };

  const handleDeleteCriterion = (qIndex: number, cIndex: number) => {
    const updatedList = [...questions];
    updatedList[qIndex].criteria.splice(cIndex, 1);
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList });
  };

  const handleAddQuestion = () => {
    const nextQNum = questions.length + 1;
    const newQ: EvaluationRule = {
      question_id: `Q${nextQNum}`,
      question_text: `Question ${nextQNum}`,
      marks: 10.0,
      accepted_variations: [],
      criteria: [
        {
          id: "C1",
          title: "Primary Verification",
          component: TargetComponent.VISUAL,
          target_property: "visual_type",
          expected_value: "Line Chart",
          accepted_variations: [],
          marks: 10.0,
        },
      ],
    };
    const updatedList = [...questions, newQ];
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList });
  };

  const handleDeleteQuestion = (qIndex: number) => {
    const updatedList = questions.filter((_, idx) => idx !== qIndex);
    setQuestions(updatedList);
    onUpdateRuleSet({ ...ruleSet, questions: updatedList });
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header & Marks Summary Bar */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-blue-600" />
            <span>Step 3: Review Evaluation Rules</span>
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Verify or refine the criteria, accepted variations, and marks before running student evaluation.
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 px-4 py-2 rounded-lg">
          <Award className="w-5 h-5 text-blue-600" />
          <div>
            <span className="text-xs text-slate-500 font-medium block">Total Assessment Marks</span>
            <span className="text-lg font-bold text-slate-900">{totalCalculatedMarks} Marks</span>
          </div>
          <span className="text-xs bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded">
            {questions.length} Questions
          </span>
        </div>
      </div>

      {/* Rules Notice */}
      <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 space-y-1">
        <p className="font-semibold flex items-center space-x-1.5">
          <CheckCircle2 className="w-4 h-4 text-blue-600" />
          <span>Deterministic & Explainable Evaluation</span>
        </p>
        <p className="text-blue-800">
          The evaluator checks for machine-verifiable requirements (visual types, field bindings, DAX formulas, relationships, data types).
          Any explicitly specified <strong>accepted variations</strong> will be awarded full marks without penalty.
        </p>
      </div>

      {/* Questions List */}
      <div className="space-y-6">
        {questions.map((q, qIndex) => (
          <div
            key={q.question_id || qIndex}
            className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
          >
            {/* Question Card Header */}
            <div className="bg-slate-50/80 px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-3 flex-1">
                <span className="px-2.5 py-1 bg-blue-600 text-white font-bold text-xs rounded-md shadow-xs">
                  {q.question_id}
                </span>
                <input
                  type="text"
                  value={q.question_text}
                  onChange={(e) => handleUpdateQuestion(qIndex, { question_text: e.target.value })}
                  className="font-semibold text-slate-900 text-sm bg-transparent border-b border-transparent hover:border-slate-300 focus:border-blue-500 focus:outline-none flex-1 py-0.5"
                  placeholder="Enter Question title..."
                />
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1.5">
                  <label className="text-xs font-medium text-slate-500">Marks:</label>
                  <input
                    type="number"
                    value={q.marks}
                    onChange={(e) =>
                      handleUpdateQuestion(qIndex, { marks: parseFloat(e.target.value) || 0 })
                    }
                    className="w-16 px-2 py-1 text-xs font-bold text-slate-900 bg-white border border-slate-300 rounded text-right focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <button
                  onClick={() => handleDeleteQuestion(qIndex)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded transition-colors"
                  title="Delete Question"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Criteria Table */}
            <div className="p-6 space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                      <th className="pb-2 w-1/4">Criterion / Property</th>
                      <th className="pb-2 w-1/5">Target Component</th>
                      <th className="pb-2 w-1/4">Expected Value</th>
                      <th className="pb-2 w-1/5">Accepted Variations</th>
                      <th className="pb-2 w-16 text-right">Marks</th>
                      <th className="pb-2 w-10"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {q.criteria.map((c, cIndex) => (
                      <tr key={c.id || cIndex} className="hover:bg-slate-50/50">
                        {/* Title & Target Property */}
                        <td className="py-2.5 pr-3">
                          <input
                            type="text"
                            value={c.title}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, { title: e.target.value })
                            }
                            className="font-medium text-slate-800 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-blue-500 focus:outline-none w-full"
                          />
                          <input
                            type="text"
                            value={c.target_property}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, {
                                target_property: e.target.value,
                              })
                            }
                            className="text-[11px] text-slate-400 font-mono bg-transparent border-b border-transparent hover:border-slate-300 focus:border-blue-500 focus:outline-none w-full mt-0.5"
                            placeholder="e.g. visual_type, x_axis, dax_formula"
                          />
                        </td>

                        {/* Component Selector */}
                        <td className="py-2.5 pr-3">
                          <select
                            value={c.component}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, {
                                component: e.target.value as TargetComponent,
                              })
                            }
                            className="bg-slate-50 border border-slate-300 rounded px-2 py-1 text-slate-800 text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          >
                            <option value="Visual">Visual</option>
                            <option value="DAX Measure">DAX Measure</option>
                            <option value="Semantic Model">Semantic Model</option>
                            <option value="Calculated Column">Calculated Column</option>
                            <option value="Relationship">Relationship</option>
                            <option value="Filter/Slicer">Filter/Slicer</option>
                          </select>
                        </td>

                        {/* Expected Value */}
                        <td className="py-2.5 pr-3">
                          <input
                            type="text"
                            value={String(c.expected_value || "")}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, {
                                expected_value: e.target.value,
                              })
                            }
                            className="w-full font-mono text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1 text-slate-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          />
                        </td>

                        {/* Accepted Variations */}
                        <td className="py-2.5 pr-3">
                          <input
                            type="text"
                            value={c.accepted_variations?.join("; ") || ""}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, {
                                accepted_variations: e.target.value
                                  .split(";")
                                  .map((s) => s.trim())
                                  .filter(Boolean),
                              })
                            }
                            placeholder="e.g. Date Hierarchy; OrderDate"
                            className="w-full text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1 text-slate-700 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          />
                        </td>

                        {/* Marks */}
                        <td className="py-2.5 text-right">
                          <input
                            type="number"
                            value={c.marks}
                            onChange={(e) =>
                              handleUpdateCriterion(qIndex, cIndex, {
                                marks: parseFloat(e.target.value) || 0,
                              })
                            }
                            className="w-14 px-1.5 py-1 text-xs font-bold text-slate-800 bg-slate-50 border border-slate-300 rounded text-right focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          />
                        </td>

                        {/* Delete Button */}
                        <td className="py-2.5 text-center">
                          <button
                            onClick={() => handleDeleteCriterion(qIndex, cIndex)}
                            className="text-slate-400 hover:text-rose-600 transition-colors p-1"
                            title="Remove criterion"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add Criterion Button */}
              <button
                onClick={() => handleAddCriterion(qIndex)}
                className="inline-flex items-center space-x-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline pt-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Sub-Criterion to {q.question_id}</span>
              </button>
            </div>
          </div>
        ))}

        {/* Add Question Button */}
        <button
          onClick={handleAddQuestion}
          className="w-full py-3.5 border-2 border-dashed border-slate-300 hover:border-blue-500 hover:bg-blue-50/30 rounded-xl text-xs font-bold text-slate-600 hover:text-blue-700 transition-all flex items-center justify-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Question to Rule Set</span>
        </button>
      </div>

      {/* Navigation Actions */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded-lg shadow-sm transition-all text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Step 2</span>
        </button>

        <button
          onClick={onNext}
          disabled={questions.length === 0}
          className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <span>Confirm Rules & Select Student Folder</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
