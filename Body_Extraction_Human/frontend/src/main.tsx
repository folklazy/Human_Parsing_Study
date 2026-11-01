import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ScanLine,
  Upload,
  Search,
  Layers,
  Image as ImageIcon,
  Film,
  ChevronRight,
  ChevronLeft,
  LoaderCircle,
  CheckCircle2,
  AlertCircle,
  LogOut,
  Trash2,
  RefreshCw,
  Play,
  Eye,
  Clock,
  User,
  ShieldCheck,
  X,
  FolderOpen,
} from "lucide-react";
import "@fontsource/noto-sans-thai/400.css";
import "@fontsource/noto-sans-thai/500.css";
import "@fontsource/noto-sans-thai/600.css";
import "@fontsource/noto-sans-thai/700.css";
import "./style.css";

type Row = Record<string, any>;
const names: Record<string, string> = {
  black: "ดำ",
  white: "ขาว",
  gray: "เทา",
  red: "แดง",
  orange: "ส้ม",
  yellow: "เหลือง",
  green: "เขียว",
  sky_blue: "ฟ้า",
  blue: "น้ำเงิน",
  purple: "ม่วง",
  pink: "ชมพู",
  brown: "น้ำตาล",
};
const learnedNames: Record<number, string> = {
  1: "โทนมืด (รวมกรมท่า)",
  2: "โทนกลาง",
  3: "โทนอ่อน",
  4: "น้ำตาล",
  5: "แดง",
  6: "ชมพู",
  7: "เหลือง",
  8: "ส้ม",
  9: "เขียว",
  10: "น้ำเงิน",
  11: "ม่วง",
  12: "หลายสี",
};
const swatches: Record<string, string> = {
  black: "#1d2939",
  white: "#fafafa",
  gray: "#8d98a8",
  red: "#e64b4b",
  orange: "#f19542",
  yellow: "#edc44b",
  green: "#4d9971",
  sky_blue: "#83c7e7",
  blue: "#487bc1",
  purple: "#9570bf",
  pink: "#e48fae",
  brown: "#926c4b",
};
const statuses: Record<string, string> = {
  QUEUED: "รอประมวลผล",
  RUNNING: "กำลังวิเคราะห์",
  SUCCEEDED: "สำเร็จ",
  FAILED: "ล้มเหลว",
  CANCELLED: "ยกเลิกแล้ว",
};
const clothes: Record<string, string> = {
  upper_clothing: "เสื้อผ้าส่วนบน",
  lower_clothing: "เสื้อผ้าส่วนล่าง",
  coat: "เสื้อคลุม",
  pants: "กางเกง",
  skirt: "กระโปรง",
};
const fileUrl = (path: string) =>
  "/api/files/" + path.split("/").map(encodeURIComponent).join("/");
const stamp = (seconds: number) => {
  const h = Math.floor(seconds / 3600),
    m = Math.floor((seconds % 3600) / 60),
    s = (seconds % 60).toFixed(3).padStart(6, "0");
  return `${h ? String(h).padStart(2, "0") + ":" : ""}${String(m).padStart(2, "0")}:${s}`;
};
async function api(path: string, init: RequestInit = {}) {
  const r = await fetch("/api" + path, {
    ...init,
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "BodyExtraction",
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });
  const value = await r.json();
  if (!r.ok)
    throw Error(
      typeof value.detail === "string"
        ? value.detail
        : JSON.stringify(value.detail),
    );
  return value;
}
function Badge({ status }: { status: string }) {
  return (
    <span className={"badge " + status}>
      {status === "RUNNING" ? (
        <LoaderCircle size={13} className="spin" />
      ) : status === "SUCCEEDED" ? (
        <CheckCircle2 size={13} />
      ) : null}
      {statuses[status] || status}
    </span>
  );
}
function Colors({ result, label }: { result: Row; label: string }) {
  return (
    <div className="color-section">
      <span className="muted">{label}</span>
      {result?.colors?.length ? (
        <div className="chips">
          {result.palette
            .filter((p: Row) => result.colors.includes(p.name))
            .map((p: Row) => (
              <span className="color-chip" key={p.name}>
                <i style={{ background: p.hex }} />
                {names[p.name]} <small>{Math.round(p.fraction * 100)}%</small>
              </span>
            ))}
        </div>
      ) : (
        <p className="unknown">
          ไม่สามารถระบุได้ · {result?.reason || "ไม่มีข้อมูล"}
        </p>
      )}
      {result?.learned && (
        <small className="subtle">
          MLP CCIHP-12:{" "}
          {learnedNames[result.learned.color_id] ?? "ประเภท/สีหลายชั้นกำกวม"} ·
          ไม่ใช่คะแนนความเชื่อมั่น
        </small>
      )}
      {result?.warnings?.map((w: string) => (
        <small className="notice" key={w}>
          {w}
        </small>
      ))}
    </div>
  );
}

function App() {
  const [session, setSession] = useState<Row | null | undefined>(undefined),
    [loginError, setLoginError] = useState(""),
    [ready, setReady] = useState<Row>(),
    [page, setPage] = useState(
      location.hash.startsWith("#search")
        ? "search"
        : location.hash.startsWith("#job=")
          ? "result"
          : "upload",
    );
  const [jobId, setJobId] = useState(
      location.hash.startsWith("#job=")
        ? new URLSearchParams(location.hash.slice(1)).get("job") || ""
        : "",
    ),
    [wantedFrame, setWantedFrame] = useState(
      new URLSearchParams(location.hash.slice(1)).get("frame") || "",
    ),
    [wantedPerson, setWantedPerson] = useState(
      new URLSearchParams(location.hash.slice(1)).get("person") || "",
    );
  const [toast, setToast] = useState("");
  const [searchScope, setSearchScope] = useState(
    new URLSearchParams(location.hash.slice(1)).get("video_job") || "",
  );
  useEffect(() => {
    api("/me")
      .then(setSession)
      .catch(() => setSession(null));
  }, []);
  useEffect(() => {
    if (session)
      api("/ready")
        .then(setReady)
        .catch((e) => setToast(e.message));
  }, [session]);
  function navigate(next: string, job = "", frame = "", person = "") {
    setPage(next);
    setJobId(job);
    setWantedFrame(frame);
    setWantedPerson(person);
    setSearchScope(next === "search" ? job : "");
    location.hash =
      next === "result"
        ? new URLSearchParams({ job, frame, person }).toString()
        : next === "search" && job
          ? "search&video_job=" + encodeURIComponent(job)
          : next;
  }
  useEffect(() => {
    const f = () => {
      const p = new URLSearchParams(location.hash.slice(1));
      if (p.get("job")) {
        setPage("result");
        setJobId(p.get("job")!);
        setWantedFrame(p.get("frame") || "");
        setWantedPerson(p.get("person") || "");
      } else {
        setPage(location.hash.startsWith("#search") ? "search" : "upload");
        setSearchScope(p.get("video_job") || "");
      }
    };
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 9000);
      return () => clearTimeout(t);
    }
  }, [toast]);
  if (session === undefined)
    return (
      <div className="loading">
        <LoaderCircle className="spin" />
        กำลังเชื่อมต่อระบบ
      </div>
    );
  if (!session)
    return (
      <div className="login-shell">
        <form
          className="login-card"
          onSubmit={async (e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            try {
              setSession(
                await api("/login", {
                  method: "POST",
                  body: JSON.stringify(Object.fromEntries(f)),
                }),
              );
            } catch (x) {
              setLoginError((x as Error).message);
            }
          }}
        >
          <div className="brand-icon">
            <ScanLine size={30} />
          </div>
          <p className="eyebrow">BODY EXTRACTION HUMAN</p>
          <h1>วิเคราะห์ภาพ เข้าใจรายละเอียด</h1>
          <p className="muted">
            พื้นที่ส่วนตัวสำหรับวิเคราะห์บุคคลและสีเสื้อผ้า
          </p>
          <label>
            ชื่อผู้ใช้
            <input
              name="username"
              autoComplete="username"
              required
              defaultValue="admin"
            />
          </label>
          <label>
            รหัสผ่าน
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {loginError && (
            <div role="alert" className="error">
              {loginError}
            </div>
          )}
          <button className="primary">
            เข้าสู่ระบบ <ChevronRight size={17} />
          </button>
          <small className="subtle">
            ไม่มีการยืนยันตัวตนจากใบหน้า หรือการเชื่อมบุคคลข้ามกล้อง
          </small>
        </form>
      </div>
    );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" onClick={() => navigate("upload")}>
          <span className="brand-icon">
            <ScanLine size={25} />
          </span>
          <span>
            Body Extraction<small>HUMAN ANALYSIS WORKSPACE</small>
          </span>
        </a>
        <p className="nav-label">พื้นที่ทำงาน</p>
        <button
          className={"nav " + (page === "upload" ? "active" : "")}
          onClick={() => navigate("upload")}
        >
          <Upload size={19} />
          อัปโหลดและงานวิเคราะห์
        </button>
        <button
          className={"nav " + (page === "search" ? "active" : "")}
          onClick={() => navigate("search")}
        >
          <Search size={19} />
          ประวัติและค้นหาบุคคล
        </button>
        <div className="sidebar-note">
          <ShieldCheck size={20} />
          <strong>ไฟล์และผลวิเคราะห์เป็นส่วนตัว</strong>
          <p>ค้นหาจากลักษณะเสื้อผ้า ไม่ใช่การยืนยันตัวบุคคล</p>
        </div>
        <div className="account">
          <span className="avatar">A</span>
          <div>
            {session.username}
            <small>พื้นที่ทำงานบนเซิร์ฟเวอร์</small>
          </div>
          <button
            title="ออกจากระบบ"
            onClick={async () => {
              await api("/logout", { method: "POST" });
              setSession(null);
            }}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>
            <span className="connection-dot" />
            เชื่อมต่อระบบแล้ว
          </span>
          <a href="/docs" target="_blank" rel="noreferrer">
            API documentation ↗
          </a>
        </header>
        <div className="content">
          {toast && (
            <div className="toast" role="alert">
              <AlertCircle size={18} />
              {toast}
              <button onClick={() => setToast("")}>
                <X size={17} />
              </button>
            </div>
          )}
          {page === "upload" ? (
            <UploadPage ready={ready} open={navigate} error={setToast} />
          ) : page === "search" ? (
            <SearchPage
              key={searchScope || "all"}
              initialVideoJob={searchScope}
              ready={ready}
              open={navigate}
              error={setToast}
            />
          ) : (
            <ResultPage
              id={jobId}
              wantedFrame={wantedFrame}
              wantedPerson={wantedPerson}
              error={setToast}
              searchVideo={(id: string) => navigate("search", id)}
            />
          )}
        </div>
        <footer>
          Body Extraction Human · YOLO26x-Seg +{" "}
          {ready?.config?.parser || "Human Parsing"} · สีจากพิกเซลต้นฉบับ
        </footer>
      </main>
    </div>
  );
}

function UploadPage({
  ready,
  open,
  error,
}: {
  ready?: Row;
  open: Function;
  error: (s: string) => void;
}) {
  const [file, setFile] = useState<File>(),
    [preview, setPreview] = useState(""),
    [previewLoaded, setPreviewLoaded] = useState(false),
    [previewError, setPreviewError] = useState(""),
    [source, setSource] = useState(""),
    [interval, setIntervalValue] = useState(1),
    [eventStart, setEventStart] = useState(""),
    [busy, setBusy] = useState(false),
    [jobs, setJobs] = useState<Row[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  async function reload() {
    try {
      const r = await api("/jobs?page=" + page);
      setJobs(r.items);
      setTotal(r.total);
    } catch (e) {
      error((e as Error).message);
    }
  }
  useEffect(() => {
    reload();
    const timer = window.setInterval(reload, 4000);
    return () => clearInterval(timer);
  }, [page]);
  useEffect(() => {
    if (!file) return;
    setPreviewLoaded(false);
    setPreviewError("");
    const u = URL.createObjectURL(file);
    setPreview(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  function choose(f?: File) {
    if (!f) return;
    if (!/\.(jpe?g|png|mp4)$/i.test(f.name)) {
      error("รองรับ JPG, PNG และ MP4 เท่านั้น");
      return;
    }
    if (f.size > (ready?.limits.max_upload_bytes || 500 * 1024 ** 2)) {
      error("ไฟล์ใหญ่เกินขีดจำกัด");
      return;
    }
    setFile(f);
  }
  async function submit() {
    if (!file) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("source", source);
      if (eventStart)
        form.append("event_start", new Date(eventStart).toISOString());
      const media = await api("/media", { method: "POST", body: form });
      const job = await api("/jobs", {
        method: "POST",
        body: JSON.stringify({
          media_id: media.id,
          sampling_seconds: interval,
        }),
      });
      setFile(undefined);
      await reload();
      open("result", job.id);
    } catch (e) {
      error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function action(id: string, kind: string) {
    try {
      await api(`/jobs/${id}/${kind}`, { method: "POST" });
      reload();
    } catch (e) {
      error((e as Error).message);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS WORKSPACE</p>
          <h1>อัปโหลดและวิเคราะห์</h1>
          <p>เปลี่ยนภาพและวิดีโอให้เป็นข้อมูลเสื้อผ้าที่ค้นหาได้</p>
        </div>
        <span className="pill">
          <Layers size={16} />
          Pipeline จริง · บันทึกอัตโนมัติ
        </span>
      </div>
      <section className="upload-layout">
        <div className="card upload-card">
          <div
            className={"dropzone " + (drag ? "drag" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              choose(e.dataTransfer.files[0]);
            }}
            onClick={() => !busy && input.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter") input.current?.click();
            }}
          >
            <input
              ref={input}
              type="file"
              accept="image/jpeg,image/png,video/mp4"
              hidden
              onChange={(e) => choose(e.target.files?.[0])}
            />
            {file ? (
              <>
                {file.name.toLowerCase().endsWith(".mp4") ? (
                  <video
                    src={preview}
                    controls
                    onLoadedMetadata={(e) => {
                      const v = e.currentTarget;
                      if (
                        v.videoWidth * v.videoHeight > 40000000 ||
                        v.duration > (ready?.limits.max_video_seconds || 3600)
                      ) {
                        setPreviewError("วิดีโอมีขนาดหรือระยะเวลาเกินขีดจำกัด");
                        return;
                      }
                      setPreviewLoaded(true);
                    }}
                    onError={() =>
                      setPreviewError(
                        "เบราว์เซอร์เปิดวิดีโอนี้ไม่ได้ กรุณาใช้ MP4 ที่มี codec รองรับ เช่น H.264",
                      )
                    }
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <img
                    src={preview}
                    alt="ตัวอย่างไฟล์ที่เลือก"
                    onLoad={(e) => {
                      if (
                        e.currentTarget.naturalWidth *
                          e.currentTarget.naturalHeight >
                        40000000
                      ) {
                        setPreviewError("ภาพมีขนาดเกิน 40 ล้าน pixels");
                        return;
                      }
                      setPreviewLoaded(true);
                    }}
                    onError={() =>
                      setPreviewError("เปิดภาพนี้ไม่ได้ หรือไฟล์ภาพเสีย")
                    }
                  />
                )}
                <strong>{file.name}</strong>
                {previewError && <p className="error">{previewError}</p>}
                <span>
                  {(file.size / 1024 ** 2).toFixed(2)} MB · คลิกเพื่อเปลี่ยนไฟล์
                </span>
              </>
            ) : (
              <>
                <span className="upload-icon">
                  <Upload size={28} />
                </span>
                <h3>ลากไฟล์มาวางที่นี่</h3>
                <p>
                  หรือ <b>เลือกไฟล์จากเครื่อง</b>
                </p>
                <small>
                  JPG, PNG, MP4 · สูงสุด{" "}
                  {Math.round(
                    (ready?.limits.max_upload_bytes || 500 * 1024 ** 2) /
                      1024 ** 2,
                  )}{" "}
                  MB
                </small>
              </>
            )}
          </div>
          <div className="upload-options">
            <label>
              ชื่อแหล่งข้อมูล / กล้อง
              <input
                placeholder="เช่น ชุดภาพทดสอบ A"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                maxLength={200}
              />
            </label>
            <div className="form-row">
              <label>
                สุ่มเฟรมทุก (วินาที)
                <input
                  type="number"
                  min="0.2"
                  max="3600"
                  step="0.2"
                  value={interval}
                  onChange={(e) => setIntervalValue(Number(e.target.value))}
                />
              </label>
              <label>
                เวลาเริ่มเหตุการณ์ (ถ้าทราบ)
                <input
                  type="datetime-local"
                  value={eventStart}
                  onChange={(e) => setEventStart(e.target.value)}
                />
              </label>
            </div>
            <p className="subtle">
              เวลาเริ่มอ้างอิง timezone ของเครื่องคุณ · ไม่ระบุ =
              แสดงเฉพาะเวลาในคลิป
            </p>
            <button
              className="primary"
              disabled={
                !file ||
                !previewLoaded ||
                !!previewError ||
                busy ||
                ready?.ready === false
              }
              onClick={submit}
            >
              {busy ? (
                <LoaderCircle className="spin" size={18} />
              ) : (
                <ScanLine size={18} />
              )}{" "}
              {busy ? "กำลังส่งไฟล์…" : "ส่งวิเคราะห์"}
            </button>
          </div>
        </div>
        <aside className="card workflow">
          <span className="eyebrow">HOW IT WORKS</span>
          <h2>จากภาพ สู่รายละเอียด</h2>
          {[
            [
              "01",
              "แยกบุคคล",
              "YOLO26x-Seg ตรวจจับเฉพาะคน พร้อม instance mask",
            ],
            ["02", "แบ่งส่วนเสื้อผ้า", "Human Parsing บน ROI และคืนพิกัดเดิม"],
            [
              "03",
              "อ่านสีที่มองเห็น",
              "โมเดลสีที่เลือก + palette จาก RGB ต้นฉบับ",
            ],
            ["04", "บันทึกและค้นหา", "เก็บผลใน PostgreSQL พร้อมตำแหน่งเวลา"],
          ].map(([n, h, p]) => (
            <div className="step" key={n}>
              <span>{n}</span>
              <div>
                <strong>{h}</strong>
                <p>{p}</p>
              </div>
            </div>
          ))}
          <div className="info-box">
            <Clock size={17} />
            <p>
              วิดีโอวิเคราะห์เฉพาะเฟรมที่สุ่ม อาจพลาดเหตุการณ์ระหว่างเฟรม
              และไม่ได้เชื่อมเป็นคนเดียวกันข้ามเฟรม
            </p>
          </div>
          {ready?.missing?.length > 0 && (
            <p className="error">
              ระบบยังไม่พร้อม: {ready!.missing.join(", ")}
            </p>
          )}
        </aside>
      </section>
      <div className="section-heading">
        <h2>
          งานวิเคราะห์ <span className="count">{total}</span>
        </h2>
        <button className="text-button" onClick={reload}>
          <RefreshCw size={15} />
          รีเฟรช
        </button>
      </div>
      <div className="card jobs-table">
        <table>
          <thead>
            <tr>
              <th>ไฟล์ / แหล่งข้อมูล</th>
              <th>สถานะ</th>
              <th>ความคืบหน้าจริง</th>
              <th>วันที่อัปโหลด</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>
                  <div className="file-cell">
                    {j.kind === "video" ? <Film /> : <ImageIcon />}
                    <div>
                      <button
                        className="job-link"
                        onClick={() => open("result", j.id)}
                      >
                        {j.filename}
                      </button>
                      <small>
                        {j.source || "ไม่ได้ระบุแหล่งข้อมูล"} ·{" "}
                        {j.id.slice(0, 8)}
                      </small>
                    </div>
                  </div>
                </td>
                <td>
                  <Badge status={j.status} />
                  {j.cancel_requested && j.status === "RUNNING" && (
                    <small>รอจบการเขียนเฟรมเพื่อยกเลิก</small>
                  )}
                </td>
                <td>
                  <strong>
                    {j.completed_frames} เฟรม · {j.processed_people} รายการ
                  </strong>
                  {j.last_timestamp !== null && (
                    <small>ถึง {stamp(j.last_timestamp)}</small>
                  )}
                  {j.error && (
                    <small className="error-inline">{j.error.message}</small>
                  )}
                </td>
                <td>{new Date(j.created_at).toLocaleString("th-TH")}</td>
                <td>
                  <div className="actions">
                    {["QUEUED", "RUNNING"].includes(j.status) ? (
                      <button
                        className="secondary"
                        onClick={() => action(j.id, "cancel")}
                      >
                        ยกเลิก
                      </button>
                    ) : ["FAILED", "CANCELLED"].includes(j.status) ? (
                      <button
                        className="secondary"
                        onClick={() => action(j.id, "retry")}
                      >
                        ลองใหม่
                      </button>
                    ) : null}
                    <button
                      className="icon-button"
                      title="เปิดผลวิเคราะห์"
                      onClick={() => open("result", j.id)}
                    >
                      <ChevronRight size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!jobs.length && (
          <div className="empty">
            <FolderOpen size={32} />
            <h3>ยังไม่มีงานวิเคราะห์</h3>
            <p>อัปโหลดไฟล์แรกเพื่อเริ่มต้น</p>
          </div>
        )}
      </div>
      <Pagination page={page} total={total} size={20} change={setPage} />
    </>
  );
}

function Pagination({
  page,
  total,
  size,
  change,
}: {
  page: number;
  total: number;
  size: number;
  change: (n: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        {total} รายการ · หน้า {page} / {Math.max(1, Math.ceil(total / size))}
      </span>
      <button disabled={page === 1} onClick={() => change(page - 1)}>
        <ChevronLeft size={16} />
      </button>
      <button disabled={page * size >= total} onClick={() => change(page + 1)}>
        <ChevronRight size={16} />
      </button>
    </div>
  );
}

function ResultPage({
  id,
  wantedFrame,
  wantedPerson,
  error,
  searchVideo,
}: {
  id: string;
  wantedFrame: string;
  wantedPerson: string;
  error: (s: string) => void;
  searchVideo: (id: string) => void;
}) {
  const [job, setJob] = useState<Row>(),
    [frame, setFrame] = useState<Row>(),
    [selected, setSelected] = useState(wantedPerson),
    [fid, setFid] = useState(wantedFrame),
    [boxes, setBoxes] = useState(true),
    [masks, setMasks] = useState(false),
    [parsing, setParsing] = useState(true),
    [numbers, setNumbers] = useState(true),
    [showVideo, setShowVideo] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    setJob(undefined);
    setFrame(undefined);
    setFid(wantedFrame);
    setSelected(wantedPerson);
    const load = () =>
      api("/jobs/" + id)
        .then((j) => {
          setJob(j);
          setFid((old) =>
            j.frames.some((f: Row) => f.id === old)
              ? old
              : j.frames[0]?.id || "",
          );
        })
        .catch((e) => error(e.message));
    load();
    const timer = window.setInterval(load, 4000);
    return () => clearInterval(timer);
  }, [id, wantedFrame, wantedPerson]);
  useEffect(() => {
    if (!fid) {
      setFrame(undefined);
      return;
    }
    if (fid)
      api("/frames/" + fid)
        .then((f) => {
          setFrame(f);
          setSelected((old) =>
            f.persons.some((p: Row) => p.id === old)
              ? old
              : f.persons[0]?.id || "",
          );
        })
        .catch((e) => error(e.message));
  }, [fid]);
  function selectPerson(pid: string) {
    setSelected(pid);
    history.replaceState(
      null,
      "",
      `#${new URLSearchParams({ job: id, frame: fid, person: pid })}`,
    );
  }
  const person = frame?.persons.find((p: Row) => p.id === selected);
  useEffect(() => {
    if (video.current && frame && showVideo)
      video.current.currentTime = frame.timestamp_seconds;
  }, [frame?.timestamp_seconds, showVideo]);
  if (!job)
    return (
      <div className="loading">
        <LoaderCircle className="spin" />
        กำลังอ่านงาน
      </div>
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS RESULTS</p>
          <h1>{job.filename}</h1>
          <p>
            {job.source || "ไม่ได้ระบุแหล่งข้อมูล"} · รหัสงาน {id.slice(0, 12)}
          </p>
        </div>
        <Badge status={job.status} />
      </div>
      <div className="result-summary">
        <span>
          <ImageIcon size={17} />
          {job.completed_frames} เฟรม
        </span>
        <span>
          <User size={17} />
          {job.processed_people} รายการบุคคล
        </span>
        <span>
          <Layers size={17} />
          {job.config.parser}
        </span>
        {job.kind === "video" && (
          <span>
            <Clock size={17} />
            สุ่มทุก {job.sampling_seconds}s
          </span>
        )}
      </div>
      {job.partial && (
        <div className="notice">
          ผลเพียงบางส่วน: งานยังไม่สำเร็จทั้งหมด การค้นหาจะไม่รวมงานนี้
        </div>
      )}
      {job.error && <div className="error">{job.error.message}</div>}
      {job.kind === "video" && (
        <div className="video-bar">
          <label>
            เฟรมที่วิเคราะห์
            <select
              aria-label="เฟรมที่วิเคราะห์"
              value={fid}
              onChange={(e) => {
                setFid(e.target.value);
                setSelected("");
              }}
            >
              {job.frames.map((f: Row) => (
                <option value={f.id} key={f.id}>
                  #{f.sample_index + 1} · {stamp(f.timestamp_seconds)} ·{" "}
                  {f.people} คน
                </option>
              ))}
            </select>
          </label>
          <button
            className="secondary"
            onClick={() => {
              setShowVideo(true);
              setTimeout(() => {
                if (video.current) {
                  video.current.currentTime = frame?.timestamp_seconds || 0;
                  video.current.play().catch(() => {});
                }
              }, 100);
            }}
          >
            <Play size={16} />
            เปิดคลิป ณ เวลาที่พบ
          </button>
          <button className="secondary" onClick={() => searchVideo(job.id)}>
            <Search size={16} />
            ค้นหาบุคคลในคลิปนี้
          </button>
        </div>
      )}
      {showVideo && (
        <div className="card">
          <video
            ref={video}
            controls
            src={fileUrl(job.media_path)}
            className="video-player"
            onLoadedMetadata={() => {
              if (video.current)
                video.current.currentTime = frame?.timestamp_seconds || 0;
            }}
          />
          <p className="subtle">
            เวลาของเฟรมอ้างจาก PTS ของ video stream · Codec บางชนิดเปิดใน
            browser ไม่ได้ ให้ดาวน์โหลดไฟล์ต้นฉบับ
          </p>
          <a href={fileUrl(job.media_path)} download>
            ดาวน์โหลดวิดีโอต้นฉบับ
          </a>
        </div>
      )}
      {frame ? (
        <section className="result-layout">
          <div className="card image-workspace">
            <div className="viewer-toolbar">
              <span>
                <Eye size={16} />
                การแสดงผล
              </span>
              {[
                [boxes, setBoxes, "Bounding Box"],
                [masks, setMasks, "Instance Mask"],
                [parsing, setParsing, "Human Parsing"],
                [numbers, setNumbers, "หมายเลข"],
              ].map(([value, setter, label]) => (
                <label key={label as string}>
                  <input
                    type="checkbox"
                    checked={value as boolean}
                    onChange={(e) => (setter as Function)(e.target.checked)}
                  />
                  {label as string}
                </label>
              ))}
            </div>
            <div
              className="image-stage"
              style={{ aspectRatio: `${frame.width}/${frame.height}` }}
            >
              <img
                className="original"
                src={fileUrl(frame.path)}
                alt="เฟรมต้นฉบับ"
              />
              {frame.persons
                .filter((p: Row) => !selected || p.id === selected)
                .map((p: Row) => (
                  <React.Fragment key={p.id}>
                    {masks && (
                      <img
                        className="overlay"
                        src={fileUrl(p.mask_path)}
                        alt="instance mask"
                      />
                    )}
                    {parsing && (
                      <img
                        className="overlay"
                        src={fileUrl(p.parsing_path)}
                        alt="human parsing"
                      />
                    )}
                  </React.Fragment>
                ))}
              <svg
                className="box-layer"
                viewBox={`0 0 ${frame.width} ${frame.height}`}
              >
                {frame.persons.map((p: Row) => (
                  <g
                    key={p.id}
                    onClick={() => selectPerson(p.id)}
                    className="person-box"
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && selectPerson(p.id)}
                    aria-label={"เลือกบุคคล " + p.ordinal}
                  >
                    <rect
                      x={p.bbox[0]}
                      y={p.bbox[1]}
                      width={p.bbox[2] - p.bbox[0]}
                      height={p.bbox[3] - p.bbox[1]}
                      fill="transparent"
                      stroke={
                        boxes
                          ? p.id === selected
                            ? "#0d9488"
                            : "#ffffff"
                          : "transparent"
                      }
                      strokeWidth={p.id === selected ? 5 : 2}
                    />
                    {numbers && (
                      <>
                        <rect
                          x={p.bbox[0]}
                          y={Math.max(0, p.bbox[1] - 25)}
                          width="65"
                          height="25"
                          rx="4"
                          fill={p.id === selected ? "#0d9488" : "#334155"}
                        />
                        <text
                          x={p.bbox[0] + 7}
                          y={Math.max(18, p.bbox[1] - 7)}
                          fill="white"
                          fontSize="15"
                        >
                          #{p.ordinal}
                        </text>
                      </>
                    )}
                  </g>
                ))}
              </svg>
            </div>
            <div className="viewer-legend">
              <span className="muted">สี overlay (ไม่ใช่สีเสื้อ):</span>
              <span>
                <i style={{ background: "#28c8ff" }} /> Hair
              </span>
              <span>
                <i style={{ background: "#ffd21e" }} /> Face
                {job.config.parser === "sapiens2_1b" ? "/Neck" : ""}
              </span>
              <span>
                <i style={{ background: "#28dc5a" }} /> Upper
              </span>
              <span>
                <i style={{ background: "#f046d2" }} /> Lower
              </span>
            </div>
            <div className="image-caption">
              {frame.width} × {frame.height}px ·{" "}
              {job.kind === "video"
                ? `เวลาในคลิป ${stamp(frame.timestamp_seconds)}`
                : "ภาพนิ่ง"}
              {job.event_start &&
                ` · เวลาเหตุการณ์ ${new Date(new Date(job.event_start).getTime() + frame.timestamp_seconds * 1000).toLocaleString("th-TH")}`}
            </div>
          </div>
          <aside className="card person-panel">
            <h2>
              บุคคลในเฟรม <span className="count">{frame.persons.length}</span>
            </h2>
            <div className="person-tabs">
              {frame.persons.map((p: Row) => (
                <button
                  className={selected === p.id ? "active" : ""}
                  key={p.id}
                  onClick={() => selectPerson(p.id)}
                >
                  #{p.ordinal}
                </button>
              ))}
            </div>
            {person ? (
              <>
                <img
                  className="person-crop"
                  src={fileUrl(person.crop_path)}
                  alt={"ภาพบุคคล " + person.ordinal}
                />
                <div className="person-heading">
                  <h2>บุคคล #{person.ordinal}</h2>
                  <span className="pill">
                    Detector {(person.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="chips">
                  {person.garment_types.map((g: string) => (
                    <span className="tag" key={g}>
                      {clothes[g] || g}
                    </span>
                  ))}
                </div>
                <Colors result={person.upper_result} label="สีเสื้อผ้าส่วนบน" />
                <Colors
                  result={person.lower_result}
                  label="สีเสื้อผ้าส่วนล่าง"
                />
                <p className="subtle">
                  สัดส่วนสีคือพื้นที่พิกเซลที่สังเกต
                  ไม่ใช่ความน่าจะเป็นว่าทำนายถูก
                </p>
                <details>
                  <summary>รายละเอียดพิกัดและโมเดล</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        bbox: person.bbox,
                        geometry: person.details,
                        upper: person.upper_result.learned,
                        lower: person.lower_result.learned,
                      },
                      null,
                      2,
                    )}
                  </pre>
                  <a href={fileUrl(person.native_path)} download>
                    ดาวน์โหลด native parsing mask
                  </a>
                </details>
              </>
            ) : (
              <div className="empty">
                <User size={30} />
                <h3>ไม่พบบุคคลในเฟรมนี้</h3>
                <p>การวิเคราะห์ภาพนี้สำเร็จโดยไม่มีรายการบุคคล</p>
              </div>
            )}
          </aside>
        </section>
      ) : (
        <div className="card empty">
          <LoaderCircle
            className={job.status === "RUNNING" ? "spin" : ""}
            size={32}
          />
          <h3>
            {job.status === "QUEUED"
              ? "รอ Worker รับงาน"
              : job.status === "RUNNING"
                ? "กำลังเตรียมโมเดลและวิเคราะห์เฟรมแรก"
                : "ยังไม่มีเฟรมที่ประมวลผลสำเร็จ"}
          </h3>
          <p>สถานะอัปเดตจากฐานข้อมูลอัตโนมัติทุก 4 วินาที</p>
        </div>
      )}
      <details className="card provenance">
        <summary>ประวัติ attempts และขอบเขตการประมวลผล</summary>
        <pre>
          {JSON.stringify(
            { config: job.config, attempts: job.attempts },
            null,
            2,
          )}
        </pre>
      </details>
      <button
        className="danger-link"
        onClick={async () => {
          if (!confirm("ลบไฟล์ต้นฉบับและผลทั้งหมดของไฟล์นี้?")) return;
          try {
            await api("/media/" + job.media_id, { method: "DELETE" });
            location.hash = "upload";
          } catch (e) {
            error((e as Error).message);
          }
        }}
      >
        <Trash2 size={16} />
        ลบไฟล์และผลที่เกี่ยวข้อง
      </button>
    </>
  );
}

function SearchPage({
  ready,
  open,
  error,
  initialVideoJob = "",
}: {
  ready?: Row;
  open: Function;
  error: (s: string) => void;
  initialVideoJob?: string;
}) {
  const [filter, setFilter] = useState<Row>({
      upper: "",
      lower: "",
      garment: "",
      kind: "",
      q: "",
      uploaded_from: "",
      uploaded_to: "",
      event_from: "",
      event_to: "",
      job_id: initialVideoJob,
      time_from_seconds: "",
      time_to_seconds: "",
    }),
    [items, setItems] = useState<Row[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [busy, setBusy] = useState(false),
    [submitted, setSubmitted] = useState<Row>(
      initialVideoJob ? { job_id: initialVideoJob } : {},
    ),
    [moments, setMoments] = useState<Row[]>([]),
    [momentTotal, setMomentTotal] = useState(0),
    [momentPage, setMomentPage] = useState(1),
    [videos, setVideos] = useState<Row[]>([]),
    [videoPage, setVideoPage] = useState(1),
    [videoTotal, setVideoTotal] = useState(0),
    [videoQuery, setVideoQuery] = useState(""),
    [chosenVideo, setChosenVideo] = useState<Row>();
  const requestSeq = useRef(0);
  useEffect(() => {
    let active = true;
    const timer = setTimeout(
      () =>
        api(
          "/video-jobs?" +
            new URLSearchParams({ page: String(videoPage), q: videoQuery }),
        )
          .then((r) => {
            if (active) {
              setVideos(r.items);
              setVideoTotal(r.total);
            }
          })
          .catch((e) => {
            if (active) error(e.message);
          }),
      250,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [videoPage, videoQuery]);
  useEffect(() => {
    if (initialVideoJob)
      api("/jobs/" + initialVideoJob)
        .then((j) => setChosenVideo({ ...j, job_id: j.id }))
        .catch((e) => error(e.message));
  }, [initialVideoJob]);
  function field(k: string, v: string) {
    setFilter({ ...filter, [k]: v });
  }
  async function search() {
    const sequence = ++requestSeq.current;
    setBusy(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "18",
        include_moments: "true",
        moment_page: String(momentPage),
        moment_page_size: "12",
      });
      Object.entries(submitted).forEach(([k, v]) => {
        if (v)
          params.set(
            k,
            ["uploaded_from", "uploaded_to", "event_from", "event_to"].includes(
              k,
            )
              ? new Date(v).toISOString()
              : v,
          );
      });
      const r = await api("/search?" + params);
      if (sequence !== requestSeq.current) return;
      setItems(r.items);
      setTotal(r.total);
      setMoments(r.moments || []);
      setMomentTotal(r.total_moments || 0);
    } catch (e) {
      if (sequence === requestSeq.current) error((e as Error).message);
    } finally {
      if (sequence === requestSeq.current) setBusy(false);
    }
  }
  useEffect(() => {
    search();
  }, [page, momentPage, submitted]);
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">CLOTHING APPEARANCE SEARCH</p>
          <h1>ค้นหาจากลักษณะเสื้อผ้า</h1>
          <p>ค้นหาผลที่บันทึกไว้ แล้วเปิดกลับไปยังบุคคลและเวลาที่พบ</p>
        </div>
        <span className="pill">
          <Search size={16} />
          ฐานข้อมูลจริง
        </span>
      </div>
      <form
        className="card search-form"
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setMomentPage(1);
          setSubmitted({ ...filter });
        }}
      >
        <div className="video-search-scope">
          <div className="form-row">
            <label>
              ค้นชื่อวิดีโอที่วิเคราะห์แล้ว
              <input
                value={videoQuery}
                placeholder="พิมพ์ชื่อคลิปหรือแหล่งข้อมูล"
                onChange={(e) => {
                  setVideoQuery(e.target.value);
                  setVideoPage(1);
                }}
              />
            </label>
            <label>
              ขอบเขตวิดีโอ
              <select
                aria-label="ขอบเขตวิดีโอ"
                value={filter.job_id}
                onChange={(e) => {
                  const id = e.target.value;
                  field("job_id", id);
                  setChosenVideo(videos.find((v) => v.job_id === id));
                }}
              >
                <option value="">ทุกไฟล์ที่วิเคราะห์สำเร็จ</option>
                {Array.from(
                  new Map(
                    [...videos, ...(chosenVideo ? [chosenVideo] : [])].map(
                      (v) => [v.job_id, v],
                    ),
                  ).values(),
                ).map((v) => (
                  <option value={v.job_id} key={v.job_id}>
                    {v.filename} · {v.source || "ไม่ระบุแหล่งข้อมูล"} · #
                    {v.job_id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {videoTotal > 50 && (
            <Pagination
              page={videoPage}
              total={videoTotal}
              size={50}
              change={setVideoPage}
            />
          )}
          {filter.job_id && chosenVideo && (
            <p className="subtle">
              งาน #{filter.job_id.slice(0, 8)} · สุ่มเฟรมทุก{" "}
              {chosenVideo.sampling_seconds} วินาที · วิเคราะห์แล้ว{" "}
              {chosenVideo.completed_frames} เฟรม
            </p>
          )}
        </div>
        <div className="search-primary">
          {[
            ["upper", "สีเสื้อผ้าส่วนบน"],
            ["lower", "สีเสื้อผ้าส่วนล่าง"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <select
                aria-label={label}
                value={filter[key]}
                onChange={(e) => field(key, e.target.value)}
              >
                <option value="">ทุกสี</option>
                {Object.entries(names).map(([v, n]) => (
                  <option key={v} value={v}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <label>
            ชื่อไฟล์ / แหล่งข้อมูล
            <input
              placeholder="ค้นหาด้วยชื่อ"
              value={filter.q}
              onChange={(e) => field("q", e.target.value)}
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? (
              <LoaderCircle size={18} className="spin" />
            ) : (
              <Search size={18} />
            )}
            ค้นหา
          </button>
        </div>
        <details>
          <summary>ตัวกรองเพิ่มเติม</summary>
          <div className="search-extra">
            <label>
              เวลาในคลิป ตั้งแต่ (วินาที)
              <input
                type="number"
                min="0"
                step="0.001"
                placeholder="เช่น 30"
                value={filter.time_from_seconds}
                onChange={(e) => field("time_from_seconds", e.target.value)}
              />
            </label>
            <label>
              เวลาในคลิป ถึง (วินาที)
              <input
                type="number"
                min="0"
                step="0.001"
                placeholder="เช่น 90"
                value={filter.time_to_seconds}
                onChange={(e) => field("time_to_seconds", e.target.value)}
              />
            </label>
            <label>
              ประเภทเสื้อผ้า
              <select
                aria-label="ประเภทเสื้อผ้า"
                value={filter.garment}
                onChange={(e) => field("garment", e.target.value)}
              >
                <option value="">ทุกประเภทที่รองรับ</option>
                {Object.entries(clothes)
                  .filter(
                    ([v]) =>
                      !ready?.supported_garments ||
                      ready.supported_garments.includes(v),
                  )
                  .map(([v, n]) => (
                    <option value={v} key={v}>
                      {n}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              ประเภทไฟล์
              <select
                aria-label="ประเภทไฟล์"
                value={filter.kind}
                onChange={(e) => field("kind", e.target.value)}
              >
                <option value="">ภาพและวิดีโอ</option>
                <option value="image">ภาพ</option>
                <option value="video">วิดีโอ</option>
              </select>
            </label>
            {[
              ["uploaded_from", "อัปโหลดตั้งแต่"],
              ["uploaded_to", "อัปโหลดก่อน"],
              ["event_from", "เหตุการณ์ตั้งแต่"],
              ["event_to", "เหตุการณ์ก่อน"],
            ].map(([k, n]) => (
              <label key={k}>
                {n}
                <input
                  type="datetime-local"
                  value={filter[k]}
                  onChange={(e) => field(k, e.target.value)}
                />
              </label>
            ))}
          </div>
        </details>
        <p className="subtle">
          ทุกเงื่อนไขใช้ AND กับรายการบุคคลเดียวกัน ·
          ค้นสีหลัก/รองที่มีพื้นที่อย่างน้อย 15% · แสดงเฉพาะงานสำเร็จ
        </p>
      </form>
      {(momentTotal > 0 || submitted.job_id) && (
        <section className="card found-moments">
          <div className="section-heading">
            <h2>
              เวลาที่พบในวิดีโอ{" "}
              <span className="count">{momentTotal} เฟรมที่ตรงเงื่อนไข</span>
            </h2>
            <Clock size={18} />
          </div>
          <p className="subtle">
            แต่ละเวลาเป็นเฟรมที่วิเคราะห์จริง อาจมีคนลักษณะคล้ายกันหลายคน
            ไม่ใช่ช่วงปรากฏตัวต่อเนื่องหรือการยืนยันตัวตน
          </p>
          <div className="moment-list">
            {moments.map((m) => (
              <article className="moment" key={m.frame_id}>
                <button
                  className="moment-time"
                  onClick={() =>
                    open("result", m.job_id, m.frame_id, m.persons[0].id)
                  }
                >
                  <Play size={15} />
                  {stamp(m.timestamp_seconds)}
                </button>
                <div>
                  <strong>{m.filename}</strong>
                  <p>
                    {m.source || "ไม่ระบุแหล่งข้อมูล"} · ตรงเงื่อนไข{" "}
                    {m.matching_observations} รายการ · สุ่มทุก{" "}
                    {m.sampling_seconds}s
                  </p>
                  {m.event_start && (
                    <small>
                      เวลาอ้างอิงจากผู้ใช้:{" "}
                      {new Date(
                        new Date(m.event_start).getTime() +
                          m.timestamp_seconds * 1000,
                      ).toLocaleString("th-TH")}
                    </small>
                  )}
                </div>
                <div className="moment-persons">
                  {m.persons.map((p: Row) => (
                    <button
                      key={p.id}
                      onClick={() => open("result", m.job_id, m.frame_id, p.id)}
                    >
                      บุคคล #{p.ordinal}
                      <ChevronRight size={13} />
                    </button>
                  ))}
                </div>
              </article>
            ))}
          </div>
          {!moments.length && (
            <p className="muted">
              ไม่มีเฟรมวิดีโอที่ตรงเงื่อนไขในงานที่สำเร็จแล้ว
            </p>
          )}
          <Pagination
            page={momentPage}
            total={momentTotal}
            size={12}
            change={setMomentPage}
          />
        </section>
      )}
      <div className="section-heading">
        <h2>พบ {total} รายการบุคคล</h2>
        <span className="muted">
          รายการข้ามเฟรมอาจเป็นคนเดียวกัน ไม่ได้ทำ tracking
        </span>
      </div>
      <div className="search-grid">
        {items.map((p) => (
          <button
            className="card search-result"
            key={p.id}
            onClick={() => open("result", p.job_id, p.frame_id, p.id)}
          >
            <div className="search-image">
              <img src={fileUrl(p.crop_path)} alt={"ผลจาก " + p.filename} />
              <span>
                {p.kind === "video" ? (
                  <Film size={13} />
                ) : (
                  <ImageIcon size={13} />
                )}{" "}
                {stamp(p.timestamp_seconds)}
              </span>
            </div>
            <div className="search-result-body">
              <h3>{p.source || p.filename}</h3>
              <p className="muted">{p.filename}</p>
              <Colors result={p.upper_result} label="ส่วนบน" />
              <Colors result={p.lower_result} label="ส่วนล่าง" />
              <span className="open-result">
                เปิดเฟรมและเน้นบุคคล <ChevronRight size={15} />
              </span>
            </div>
          </button>
        ))}
      </div>
      {!items.length && !busy && (
        <div className="card empty">
          <Search size={36} />
          <h3>ไม่พบรายการที่ตรงเงื่อนไข</h3>
          <p>ลองเปลี่ยนสีหรือตัวกรอง หรือวิเคราะห์ไฟล์ใหม่ก่อน</p>
        </div>
      )}
      <Pagination page={page} total={total} size={18} change={setPage} />
    </>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
