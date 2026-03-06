import { useEffect, useRef, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Settings,
  AlertTriangle,
  RefreshCw,
  User,
  Bot,
  ShieldCheck,
  Users,
  ArrowLeft,
  Wallet,
  Percent,
  BadgeCheck,
  CreditCard,
  FileUp,
} from "lucide-react";

type Role = "user" | "bot";

type Message = {
  role: Role;
  content: string;
};

type Config = {
  url: string;
  guidelines: string[];
};

type ChatHistoryItem = ["human" | "ai", string];

type PopupKind = "success" | "error" | "info" | "loading";

type PopupState = {
  open: boolean;
  title: string;
  message: string;
  kind: PopupKind;
};

type UserMode = "customer" | "manager";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const GET_APP_URL = "https://www.atome.sg/get-the-app";

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      content: "Hello! I am your Atome assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const [config, setConfig] = useState<Config>({ url: "", guidelines: [] });
  const [showConfig, setShowConfig] = useState(false);
  const [managerInstruction, setManagerInstruction] = useState("");
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [replaceExistingDocs, setReplaceExistingDocs] = useState(false);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [refreshingConfig, setRefreshingConfig] = useState(false);
  const [applyingInstruction, setApplyingInstruction] = useState(false);

  const [reportingMistake, setReportingMistake] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [popup, setPopup] = useState<PopupState>({
    open: false,
    title: "",
    message: "",
    kind: "info",
  });
  const [userMode, setUserMode] = useState<UserMode | null>(null);
  const isManager = userMode === "manager";

  useEffect(() => {
    if (isManager) {
      fetchConfig();
    }
  }, [isManager]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchConfig = async () => {
    try {
      const res = await axios.get<Config>(`${API_BASE}/config`);
      const data = res.data;
      const normalized: Config = {
        url: data?.url ?? "",
        guidelines: data?.guidelines ?? [],
      };
      setConfig(normalized);
    } catch (error) {
      console.error("Failed to fetch config", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history: ChatHistoryItem[] = messages
        .slice(-5)
        .map((m) => [m.role === "user" ? "human" : "ai", m.content]);
      const res = await axios.post<{ response: { output: string } }>(
        `${API_BASE}/chat`,
        {
          message: userMsg.content,
          chat_history: history,
        },
      );
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: res.data.response.output },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "Sorry, I encountered an error." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleManagerInstruction = async () => {
    if (!managerInstruction.trim() || applyingInstruction) return;
    setApplyingInstruction(true);
    setPopup({
      open: true,
      title: "Applying Instruction",
      message: "Please wait while meta-agent updates the bot behavior.",
      kind: "loading",
    });
    try {
      const res = await axios.post<{ summary: string }>(
        `${API_BASE}/manager/instruct`,
        {
          instruction: managerInstruction,
        },
      );
      setPopup({
        open: true,
        title: "Update Summary",
        message: res.data.summary,
        kind: "success",
      });
      setManagerInstruction("");
      fetchConfig();
    } catch {
      setPopup({
        open: true,
        title: "Request Failed",
        message: "Failed to process instruction.",
        kind: "error",
      });
    } finally {
      setApplyingInstruction(false);
    }
  };

  const handleReportMistake = async (index: number) => {
    const botMsg = messages[index];
    const userMsg = messages[index - 1];
    if (!userMsg || botMsg.role !== "bot") return;

    try {
      const res = await axios.post<{ new_rule: string }>(
        `${API_BASE}/feedback`,
        {
          user_query: userMsg.content,
          bot_response: botMsg.content,
          feedback: feedbackText,
        },
      );
      setPopup({
        open: true,
        title: "Auto-fix Applied",
        message: `New Rule: ${res.data.new_rule}`,
        kind: "success",
      });
      setReportingMistake(null);
      setFeedbackText("");
      fetchConfig();
    } catch {
      setPopup({
        open: true,
        title: "Request Failed",
        message: "Failed to report mistake.",
        kind: "error",
      });
    }
  };

  const handleUploadDocs = async () => {
    if (!uploadFiles.length) return;
    setUploadingDocs(true);
    setPopup({
      open: true,
      title: "Uploading Documents",
      message:
        "Please wait while documents are parsed and added to knowledge base.",
      kind: "loading",
    });
    try {
      const formData = new FormData();
      uploadFiles.forEach((file) => formData.append("files", file));
      formData.append("replace_existing", String(replaceExistingDocs));

      const res = await axios.post<{
        ingested_documents: number;
        ingested_files: number;
        accepted_files?: Array<{ file_name: string; score: number }>;
        rejected_files?: Array<{
          file_name: string;
          score: number;
          reason: string;
        }>;
        failed_files: Array<{ file_name: string; error: string }>;
      }>(`${API_BASE}/manager/upload-docs`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const failed = res.data.failed_files ?? [];
      const rejected = res.data.rejected_files ?? [];
      const failedSummary = failed.length
        ? `\nFailed: ${failed.map((f) => `${f.file_name} (${f.error})`).join(", ")}`
        : "";
      const rejectedSummary = rejected.length
        ? `\nRejected: ${rejected.map((f) => `${f.file_name} (score ${f.score})`).join(", ")}`
        : "";

      setPopup({
        open: true,
        title: "Documents Uploaded",
        message: `Accepted Files: ${res.data.ingested_files}, Chunks: ${res.data.ingested_documents}${rejectedSummary}${failedSummary}`,
        kind: "success",
      });
      setUploadFiles([]);
      fetchConfig();
    } catch (error) {
      const message =
        axios.isAxiosError(error) && error.response?.data?.detail
          ? String(error.response.data.detail)
          : "Failed to upload documents.";
      setPopup({
        open: true,
        title: "Upload Failed",
        message,
        kind: "error",
      });
    } finally {
      setUploadingDocs(false);
    }
  };

  const handleRefreshKnowledgeBase = async () => {
    if (!config.url || refreshingConfig) return;
    setRefreshingConfig(true);
    setPopup({
      open: true,
      title: "Refreshing Knowledge Base",
      message:
        "Please wait while backend is recrawling and rebuilding knowledge.",
      kind: "loading",
    });
    try {
      const res = await axios.post<{
        recrawled?: boolean;
        documents_indexed?: number;
      }>(`${API_BASE}/config`, {
        url: config.url,
        guidelines: config.guidelines || [],
        force_recrawl: true,
      });
      const indexed = res.data?.documents_indexed ?? 0;
      setPopup({
        open: true,
        title: "Configuration Updated",
        message: `Knowledge base refreshed successfully. Indexed ${indexed} documents.`,
        kind: "success",
      });
      fetchConfig();
    } catch (error) {
      const message =
        axios.isAxiosError(error) && error.response?.data?.detail
          ? String(error.response.data.detail)
          : "Failed to update config.";
      setPopup({
        open: true,
        title: "Request Failed",
        message,
        kind: "error",
      });
    } finally {
      setRefreshingConfig(false);
    }
  };

  const handleGetApp = () => {
    const ua = (navigator.userAgent || "").toLowerCase();
    const platform = /android/.test(ua)
      ? "android"
      : /iphone|ipad|ipod/.test(ua)
        ? "ios"
        : "web";
    const targetUrl = `${GET_APP_URL}?platform=${platform}`;
    window.open(targetUrl, "_blank", "noopener,noreferrer");
  };

  if (!userMode) {
    return (
      <div className="min-h-screen bg-white text-black">
        <header className="sticky top-0 z-10 border-b border-black/10 bg-white/95 backdrop-blur">
          <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 md:px-6">
            <div className="flex items-center gap-2 text-2xl font-black tracking-tight">
              <span>atome</span>
              <span className="text-lg">ᴀ</span>
            </div>
            <nav className="hidden items-center gap-7 text-sm font-semibold md:flex">
              <span>Shop with Atome</span>
              <span>Atome+</span>
              <span>Business</span>
              <span>Help</span>
            </nav>
            <button
              onClick={handleGetApp}
              className="rounded-full bg-[#e9ff4f] px-5 py-2 text-sm font-bold text-black"
            >
              Get the app
            </button>
          </div>
        </header>

        <main className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-10 md:grid-cols-2 md:px-6 md:py-14">
          <section>
            <h1 className="text-4xl font-black leading-tight md:text-6xl">
              We call this empowered support.
              <br />
              You&apos;re in control.
            </h1>

            <div className="mt-8 space-y-4 text-base font-semibold">
              <p className="flex items-center gap-3">
                <Wallet size={18} /> Stretch your service productivity with AI
                assistance
              </p>
              <p className="flex items-center gap-3">
                <Percent size={18} /> Split customer and manager experiences
                clearly
              </p>
              <p className="flex items-center gap-3">
                <BadgeCheck size={18} /> Configure behavior safely via
                meta-agent workspace
              </p>
              <p className="flex items-center gap-3">
                <CreditCard size={18} /> Keep customer chat simple and focused
              </p>
            </div>

            <div className="mt-9 space-y-3">
              <button
                onClick={() => {
                  setUserMode("customer");
                  setShowConfig(false);
                }}
                className="w-full rounded-full bg-black px-6 py-4 text-left text-white transition hover:bg-black/85"
              >
                <span className="flex items-center gap-2 text-base font-bold">
                  <Users size={18} /> Continue as Customer
                </span>
                <span className="mt-1 block text-xs text-white/75">
                  Chat with the bot only. All current bot interaction features
                  are preserved.
                </span>
              </button>

              <button
                onClick={() => {
                  setUserMode("manager");
                  setShowConfig(true);
                }}
                className="w-full rounded-full border border-black px-6 py-4 text-left transition hover:bg-black/5"
              >
                <span className="flex items-center gap-2 text-base font-bold">
                  <ShieldCheck size={18} /> Continue as Customer Service Manager
                </span>
                <span className="mt-1 block text-xs text-gray-600">
                  Open configure + bot workbench to co-build, debug, and repair
                  with meta-agent.
                </span>
              </button>
            </div>
          </section>

          <section className="flex items-center justify-center">
            <div className="relative w-full max-w-sm rounded-[2.4rem] border-[10px] border-gray-200 bg-[#e9ff4f] p-10 shadow-xl">
              <div className="mx-auto flex h-40 w-40 items-center justify-center text-8xl font-black leading-none">
                A
              </div>
              <p className="mt-10 text-center text-xl font-black tracking-tight">
                atome
              </p>
              <p className="mt-1 text-center text-sm font-semibold">
                Customer Experience AI
              </p>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100 text-gray-800 font-sans">
      {popup.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div
            className="absolute inset-0"
            onClick={() =>
              popup.kind !== "loading" &&
              setPopup((prev) => ({ ...prev, open: false }))
            }
          />
          <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-black/10">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className={`h-10 w-10 rounded-full flex items-center justify-center ${
                    popup.kind === "success"
                      ? "bg-emerald-100 text-emerald-600"
                      : popup.kind === "error"
                        ? "bg-rose-100 text-rose-600"
                        : popup.kind === "loading"
                          ? "bg-indigo-100 text-indigo-600"
                          : "bg-indigo-100 text-indigo-600"
                  }`}
                >
                  {popup.kind === "success" ? (
                    <span className="text-lg">✓</span>
                  ) : popup.kind === "error" ? (
                    <span className="text-lg">!</span>
                  ) : popup.kind === "loading" ? (
                    <span className="inline-block h-5 w-5 rounded-full border-2 border-indigo-300 border-t-indigo-600 animate-spin" />
                  ) : (
                    <span className="text-lg">i</span>
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {popup.title}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 whitespace-pre-wrap">
                    {popup.message}
                  </p>
                </div>
              </div>
              {popup.kind !== "loading" && (
                <button
                  className="rounded-full p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                  onClick={() => setPopup((prev) => ({ ...prev, open: false }))}
                  aria-label="Close"
                >
                  ×
                </button>
              )}
            </div>
            {popup.kind !== "loading" && (
              <div className="mt-6 flex justify-end gap-2">
                <button
                  className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                  onClick={() => setPopup((prev) => ({ ...prev, open: false }))}
                >
                  OK
                </button>
              </div>
            )}
          </div>
        </div>
      )}
      {isManager && (
        <div
          className={`w-full md:w-1/3 bg-white border-r border-gray-200 p-6 flex flex-col transition-all ${
            showConfig ? "" : "hidden"
          }`}
        >
          <div className="mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2 text-indigo-600">
              <Settings size={20} /> Agent Configuration
            </h2>
            <p className="text-sm text-gray-500">
              Manage knowledge base and guidelines
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">
              Knowledge Base URL
            </label>
            <div className="flex gap-2">
              <input
                className="flex-1 p-2 border rounded text-sm bg-gray-50"
                value={config.url}
                onChange={(event) =>
                  setConfig({ ...config, url: event.target.value })
                }
              />
              <button
                onClick={handleRefreshKnowledgeBase}
                disabled={refreshingConfig || !config.url}
                className="p-2 bg-indigo-100 text-indigo-600 rounded hover:bg-indigo-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <RefreshCw
                  size={16}
                  className={refreshingConfig ? "animate-spin" : ""}
                />
              </button>
            </div>
          </div>

          <div className="mb-6 rounded-xl border border-indigo-100 bg-indigo-50/40 p-3">
            <label className="block text-sm font-medium mb-2 text-indigo-700">
              Upload Knowledge Docs
            </label>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              onChange={(event) =>
                setUploadFiles(Array.from(event.target.files || []))
              }
              className="w-full rounded border border-gray-200 bg-white p-2 text-xs text-gray-700"
            />
            <p className="mt-2 text-xs text-gray-500">
              Supports .pdf/.docx/.txt/.md, up to 10 files, 10MB each.
            </p>
            <label className="mt-2 flex items-center gap-2 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={replaceExistingDocs}
                onChange={(event) =>
                  setReplaceExistingDocs(event.target.checked)
                }
              />
              Replace existing knowledge base
            </label>
            {uploadFiles.length > 0 && (
              <p className="mt-2 text-xs text-gray-500">
                Selected: {uploadFiles.map((file) => file.name).join(", ")}
              </p>
            )}
            <button
              onClick={handleUploadDocs}
              disabled={uploadingDocs || uploadFiles.length === 0}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <FileUp size={14} />
              {uploadingDocs ? "Uploading..." : "Upload Documents"}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto mb-6">
            <label className="block text-sm font-medium mb-1">
              Current Guidelines
            </label>
            <ul className="list-disc pl-5 text-sm space-y-1 text-gray-600">
              {config.guidelines.map((guideline, index) => (
                <li key={index}>{guideline}</li>
              ))}
            </ul>
          </div>

          <div className="border-t pt-4">
            <label className="block text-sm font-medium mb-2 text-indigo-700">
              Manager Instruction (Meta-Agent)
            </label>
            <textarea
              className="w-full p-2 border rounded text-sm mb-2 h-24"
              placeholder="E.g., 'If users ask about refund, tell them it takes 3-5 days.'"
              value={managerInstruction}
              onChange={(event) => setManagerInstruction(event.target.value)}
            />
            <button
              onClick={handleManagerInstruction}
              disabled={applyingInstruction || !managerInstruction.trim()}
              className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition disabled:cursor-not-allowed disabled:opacity-60"
            >
              {applyingInstruction ? "Applying..." : "Apply Instruction"}
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col relative">
        <header className="bg-white p-4 shadow-sm flex justify-between items-center z-10">
          <h1 className="text-lg font-semibold text-gray-800">
            {isManager ? "Manager Workspace" : "Customer Chat"}
          </h1>
          <div className="flex items-center gap-2">
            {isManager && (
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="md:hidden p-2 text-gray-600"
              >
                <Settings />
              </button>
            )}
            <button
              onClick={() => setUserMode(null)}
              className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
            >
              <ArrowLeft size={14} /> Logout
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-none"
                    : "bg-white text-gray-800 border border-gray-100 rounded-bl-none"
                }`}
              >
                <div className="flex items-start gap-2">
                  <div
                    className={`mt-1 ${msg.role === "user" ? "order-last" : ""}`}
                  >
                    {msg.role === "user" ? (
                      <User size={16} />
                    ) : (
                      <Bot size={16} />
                    )}
                  </div>
                  <div>
                    {msg.role === "bot" ? (
                      <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-800">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: (props) => (
                              <a
                                {...props}
                                className="text-indigo-600 underline underline-offset-2"
                                target="_blank"
                                rel="noreferrer"
                              />
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">
                        {msg.content}
                      </p>
                    )}

                    {msg.role === "bot" && idx > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <button
                          onClick={() =>
                            setReportingMistake(
                              reportingMistake === idx ? null : idx,
                            )
                          }
                          className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1"
                        >
                          <AlertTriangle size={12} /> Report Mistake
                        </button>

                        {reportingMistake === idx && (
                          <div className="mt-2 bg-red-50 p-2 rounded border border-red-100">
                            <p className="text-xs text-red-800 mb-1">
                              What was the correct answer?
                            </p>
                            <textarea
                              className="w-full p-1 text-xs border rounded mb-1 text-gray-800"
                              rows={2}
                              value={feedbackText}
                              onChange={(event) =>
                                setFeedbackText(event.target.value)
                              }
                            />
                            <button
                              onClick={() => handleReportMistake(idx)}
                              className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 w-full"
                            >
                              Submit Fix
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start w-full">
              <div className="flex max-w-[90%] gap-3 flex-row">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border border-gray-200 text-emerald-600 flex items-center justify-center shadow-sm">
                  <Bot size={18} />
                </div>
                <div className="bg-white p-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-2 text-gray-400 border border-gray-100">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-75" />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-150" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
          <div className="flex gap-3 max-w-4xl mx-auto items-center">
            <input
              type="text"
              className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-5 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all shadow-inner"
              placeholder="Type your message..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && sendMessage()}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-indigo-600 text-white p-3 rounded-full hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl active:scale-95"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
