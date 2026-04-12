"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle, Loader2, Upload } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface QuestionnaireItem {
  id: string;
  question_id: string;
  cma_row: number;
  cma_column: string;
  ai_value: number | null;
  father_value: number | null;
  source_items: Array<{ source_text: string; raw_amount: number }>;
  options: Array<{ value: string; label: string; description: string }>;
  selected_option: string | null;
  cma_row_correction: number | null;
  note: string | null;
}

interface Questionnaire {
  id: string;
  status: string;
  created_at: string;
  items: QuestionnaireItem[];
}

export default function QuestionnairePage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [answers, setAnswers] = useState<Record<string, {
    selected_option: string;
    cma_row_correction?: number;
    note?: string;
  }>>({});

  useEffect(() => {
    if (!reportId) return;
    fetchQuestionnaire();
  }, [reportId]);

  async function fetchQuestionnaire() {
    try {
      const data = await apiClient<Questionnaire>(
        `/api/learning/${reportId}/questionnaire`
      );
      setQuestionnaire(data);
    } catch {
      // No questionnaire yet — that's fine
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !reportId) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const result = await apiClient<{
        questionnaire_id: string | null;
        diff_count: number;
        question_count?: number;
      }>(`/api/learning/${reportId}/upload-corrected`, {
        method: "POST",
        body: formData,
        headers: {},
      });

      if (result.questionnaire_id) {
        toast.success(`Found ${result.diff_count} differences`);
        fetchQuestionnaire();
      } else {
        toast.info("No differences found — AI output matches corrected file");
      }
    } catch (err) {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function setAnswer(questionId: string, option: string) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], selected_option: option },
    }));
  }

  async function handleSubmit() {
    if (!questionnaire || !reportId) return;
    setSubmitting(true);

    const answerList = Object.entries(answers).map(([question_id, data]) => ({
      question_id,
      ...data,
    }));

    try {
      const result = await apiClient<{ rules_created: number }>(
        `/api/learning/${reportId}/answer`,
        {
          method: "POST",
          body: JSON.stringify({
            questionnaire_id: questionnaire.id,
            answers: answerList,
          }),
        }
      );
      toast.success(`${result.rules_created} rules proposed`);
      fetchQuestionnaire();
    } catch {
      toast.error("Failed to submit answers");
    } finally {
      setSubmitting(false);
    }
  }

  const allAnswered =
    questionnaire?.items.every((item) => answers[item.question_id]) ?? false;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div className="flex items-center gap-2">
        <Link href={`/cma/${reportId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">Father Review</h1>
      </div>

      {!questionnaire ? (
        <Card>
          <CardHeader>
            <CardTitle>Upload Corrected File</CardTitle>
            <CardDescription>
              Upload the father-corrected CMA file to generate a review questionnaire.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <label className="flex flex-col items-center gap-2 p-8 border-2 border-dashed rounded-lg cursor-pointer hover:border-primary">
              <Upload className="h-8 w-8 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {uploading ? "Uploading..." : "Click to upload corrected .xlsx"}
              </span>
              <input
                type="file"
                accept=".xlsx,.xlsm"
                className="hidden"
                onChange={handleUpload}
                disabled={uploading}
              />
            </label>
          </CardContent>
        </Card>
      ) : questionnaire.status === "answered" ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Questionnaire Completed
            </CardTitle>
            <CardDescription>
              Answers submitted. Proposed rules are pending approval.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            {questionnaire.items.length} differences found. Select the correct
            value for each.
          </p>

          <div className="space-y-4">
            {questionnaire.items.map((item) => (
              <Card key={item.question_id}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">
                    Row {item.cma_row}, Column {item.cma_column}
                  </CardTitle>
                  {item.source_items.length > 0 && (
                    <CardDescription>
                      Source: {item.source_items.map((s) => s.source_text).join(", ")}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">AI value:</span>{" "}
                      <strong>{item.ai_value ?? "—"}</strong>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Father value:</span>{" "}
                      <strong>{item.father_value ?? "—"}</strong>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2">
                    {item.options.map((opt) => (
                      <Button
                        key={opt.value}
                        variant={
                          answers[item.question_id]?.selected_option === opt.value
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        onClick={() => setAnswer(item.question_id, opt.value)}
                      >
                        {opt.label}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Button
            className="w-full"
            disabled={!allAnswered || submitting}
            onClick={handleSubmit}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              `Submit ${Object.keys(answers).length} Answers`
            )}
          </Button>
        </>
      )}
    </div>
  );
}
