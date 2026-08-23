import { createHash, randomUUID } from "node:crypto";
import mammoth from "mammoth";
import pdf from "pdf-parse";
import demoCandidate from "@/data/demo/candidate-profile.json";
import { AppError } from "@/backend/errors";
import { guardedGenerate } from "@/backend/ai/guardedGenerate";
import {
  CandidateProfileSilverSchema,
  type CandidateProfileSilver,
  type ProfileReviewTask
} from "@/backend/schemas/artifacts";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export async function extractDocumentText(file: File): Promise<{ text: string; sourceType: "pdf" | "docx" }> {
  if (file.size > MAX_FILE_SIZE) throw new AppError("FILE_TOO_LARGE", "CV must be 10 MB or smaller", 413);
  const bytes = Buffer.from(await file.arrayBuffer());
  if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
    const result = await pdf(bytes);
    if (!result.text.trim()) throw new AppError("OCR_NOT_SUPPORTED", "Image-only PDFs are not supported; upload a text-based PDF or DOCX", 422);
    return { text: result.text, sourceType: "pdf" };
  }
  if (file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" || file.name.toLowerCase().endsWith(".docx")) {
    const result = await mammoth.extractRawText({ buffer: bytes });
    if (!result.value.trim()) throw new AppError("EMPTY_DOCUMENT", "DOCX contains no extractable text", 422);
    return { text: result.value, sourceType: "docx" };
  }
  throw new AppError("UNSUPPORTED_FILE_TYPE", "Only PDF and DOCX files are supported", 415);
}

function demoProfile(profileId: string, rawHash: string, fileName: string, sourceType: "pdf" | "docx" | "demo"): CandidateProfileSilver {
  const role = demoCandidate.role;
  return {
    profileId,
    revision: 1,
    name: { value: demoCandidate.name, status: "extracted", reason: null, sourceExcerpt: demoCandidate.name },
    document: { rawHash, sourceType, fileName, consentConfirmed: true },
    roles: [{
      id: randomUUID(),
      title: { value: role.title, status: "ambiguous", reason: "Confirm the local interpretation of this title", sourceExcerpt: role.title },
      employer: { value: role.employer, status: "extracted", reason: null, sourceExcerpt: role.employer },
      country: { value: role.country, status: "extracted", reason: null, sourceExcerpt: role.country },
      startDate: { value: role.startDate, status: "extracted", reason: null, sourceExcerpt: role.startDate },
      endDate: { value: role.endDate, status: "extracted", reason: null, sourceExcerpt: role.endDate },
      responsibilities: role.responsibilities.map((text) => ({ id: randomUUID(), text, sourceExcerpt: text }))
    }],
    provenanceEvents: []
  };
}

export async function parseProfile(file: File | null, consentConfirmed: boolean): Promise<{ profile: CandidateProfileSilver; rawText: string }> {
  if (!consentConfirmed) throw new AppError("CONSENT_REQUIRED", "Confirm consent before processing a CV", 400);
  const profileId = randomUUID();
  let rawText = "Skill Bridge synthetic demo profile";
  let fileName = "Linh_Nguyen_Demo_CV.pdf";
  let sourceType: "pdf" | "docx" | "demo" = "demo";

  if (file) {
    const extracted = await extractDocumentText(file);
    rawText = extracted.text;
    sourceType = extracted.sourceType;
    fileName = file.name;
  }
  const rawHash = createHash("sha256").update(rawText).digest("hex");
  const profile = await guardedGenerate({
    promptName: "CV_EXTRACT_V1",
    input: { profileId, rawHash, fileName, sourceType, rawText },
    schema: CandidateProfileSilverSchema,
    demoFactory: () => demoProfile(profileId, rawHash, fileName, sourceType)
  });
  return { profile, rawText };
}

export function buildReviewTasks(profile: CandidateProfileSilver): ProfileReviewTask[] {
  const tasks: ProfileReviewTask[] = [];
  profile.roles.forEach((role, index) => {
    (["title", "employer", "country", "startDate", "endDate"] as const).forEach((field) => {
      const value = role[field];
      if (value.status === "missing" || value.status === "ambiguous") {
        tasks.push({
          fieldPath: `roles.${index}.${field}`,
          sourceExcerpt: value.sourceExcerpt,
          reason: value.reason ?? "Candidate confirmation required",
          resolutionStatus: "open"
        });
      }
    });
  });
  return tasks;
}

export function applyProfileEdits(
  profile: CandidateProfileSilver,
  expectedRevision: number,
  edits: Array<{ fieldPath: string; value: string; action: "edit" | "confirm" }>
): CandidateProfileSilver {
  if (profile.revision !== expectedRevision) throw new AppError("REVISION_CONFLICT", "Profile changed; reload before saving", 409, false);
  const next = structuredClone(profile);
  for (const edit of edits) {
    const match = /^roles\.(\d+)\.(title|employer|country|startDate|endDate)$/.exec(edit.fieldPath);
    if (!match) throw new AppError("INVALID_FIELD_PATH", `Unsupported editable field: ${edit.fieldPath}`, 400, false, [edit.fieldPath]);
    const role = next.roles[Number(match[1])];
    if (!role) throw new AppError("INVALID_FIELD_PATH", `Role does not exist: ${edit.fieldPath}`, 400, false, [edit.fieldPath]);
    const key = match[2] as "title" | "employer" | "country" | "startDate" | "endDate";
    const previousValue = role[key].value;
    role[key] = { value: edit.value, status: edit.action === "edit" ? "candidate_edited" : "candidate_confirmed", reason: null, sourceExcerpt: role[key].sourceExcerpt };
    next.provenanceEvents.push({ id: randomUUID(), fieldPath: edit.fieldPath, previousValue, newValue: edit.value, action: edit.action, actor: "candidate", createdAt: new Date().toISOString() });
  }
  next.revision += 1;
  return CandidateProfileSilverSchema.parse(next);
}
