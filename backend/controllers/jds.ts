import { extractJd } from "@/backend/domain/matching";
import { extractDocumentText } from "@/backend/domain/profile";
import { AppError } from "@/backend/errors";

export async function parseJd(file: File | null, pastedText: string, sourceLabel: string) {
  let rawText = pastedText.trim();
  let fileName = "Pasted job description";
  if (file) {
    const extracted = await extractDocumentText(file, "JD");
    rawText = extracted.text.trim();
    fileName = file.name;
  }
  if (rawText.length < 20) throw new AppError("JD_TEXT_REQUIRED", "Upload a PDF/DOCX JD or paste at least 20 characters", 400);
  return { jd: extractJd(rawText, sourceLabel || fileName), rawText, fileName };
}
