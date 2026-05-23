"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { Business } from "../lib";
import { patchBusiness } from "./api";

const ACCEPT = ".txt,.md,.markdown,.pdf";
const MAX_BYTES = 5 * 1024 * 1024;

export default function KnowledgeForm({ business }: { business: Business }) {
  const router = useRouter();
  const initial = business.knowledge_base ?? "";
  const [value, setValue] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<string | null>(null);

  const dirty = value !== initial;

  async function onSave() {
    if (!dirty || saving) return;
    setSaving(true);
    setError(null);
    const res = await patchBusiness(business.id, { knowledge_base: value });
    setSaving(false);
    if (!res.ok) {
      setError(res.error ?? "Failed to save");
      return;
    }
    setSavedAt(new Date());
    router.refresh();
  }

  async function onUpload(file: File) {
    setError(null);
    setUploadInfo(null);
    if (file.size > MAX_BYTES) {
      setError(`File too large (max ${MAX_BYTES / 1024 / 1024} MB).`);
      return;
    }
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`/api/proxy/businesses/${business.id}/knowledge/upload/`, {
      method: "POST",
      body: fd,
    });
    setUploading(false);
    if (fileInput.current) fileInput.current.value = "";
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      try {
        const j = JSON.parse(text);
        setError(j.detail ?? text ?? `HTTP ${res.status}`);
      } catch {
        setError(text || `HTTP ${res.status}`);
      }
      return;
    }
    const data = await res.json();
    setValue(data.knowledge_base ?? "");
    setSavedAt(new Date());
    setUploadInfo(`Added ${data.characters_added.toLocaleString()} characters from ${data.filename}.`);
    router.refresh();
  }

  return (
    <article className="dash-card settings-knowledge">
      <div className="dash-card-head">
        <h2>Knowledge base</h2>
        <div className="settings-saved">
          {error && <span className="settings-saved-err">{error}</span>}
          {!error && savedAt && <span className="settings-saved-ok">Saved · {savedAt.toLocaleTimeString()}</span>}
          {!error && !savedAt && dirty && <span className="settings-saved-dirty">Unsaved changes</span>}
          {!dirty && !savedAt && !error && <span className="dash-card-meta">Used by Mary on every call</span>}
        </div>
      </div>

      <textarea
        className="text-input text-input-area"
        value={value}
        onChange={(e) => { setValue(e.target.value); setSavedAt(null); setError(null); }}
        placeholder="Pricing, service area, hours, common objections — anything Mary should know."
        rows={10}
      />

      <div className="kb-upload">
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPT}
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void onUpload(f);
          }}
        />
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => fileInput.current?.click()}
          disabled={uploading}
        >
          {uploading ? "Uploading…" : "+ Upload document"}
        </button>
        <span className="kb-upload-hint">
          {uploadInfo ?? `.txt, .md, or .pdf — up to ${MAX_BYTES / 1024 / 1024} MB`}
        </span>
      </div>

      <div className="settings-actions">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => { setValue(initial); setError(null); }}
          disabled={!dirty || saving}
        >
          Reset
        </button>
        <button type="button" className="btn btn-primary" onClick={onSave} disabled={!dirty || saving}>
          {saving ? "Saving…" : "Save knowledge base"}
        </button>
      </div>
    </article>
  );
}
