import { useEffect, useRef, useState } from "react";
import "./App.css";

interface Card {
  source: string;
  translation: string;
  captured_at: number;
}

const API_PORT = 51847;
const BASE_URL = `http://127.0.0.1:${API_PORT}`;
const WS_URL = `ws://127.0.0.1:${API_PORT}/ws`;

async function waitForBackend(maxWaitMs = 15000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (res.ok) return;
    } catch {
      // backend not up yet, keep trying
    }
  }
}

function timeAgo(ts: number) {
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function Feed({ cards, connected }: { cards: Card[]; connected: boolean }) {
  const topRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    topRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [cards.length]);

  if (cards.length === 0) {
    return (
      <div className="empty">
        <span style={{ fontSize: 32 }}>📋</span>
        <span>{connected ? "Copy an English word to start" : "Connecting to backend…"}</span>
      </div>
    );
  }

  return (
    <div className="feed">
      <div ref={topRef} />
      {cards.map((c, i) => (
        <div key={c.source + c.captured_at} className={`card ${i === 0 ? "new" : ""}`}>
          <div>
            <div className="card-source">{c.source}</div>
            <div className="card-time">{timeAgo(c.captured_at)}</div>
          </div>
          <div className="card-translation">{c.translation}</div>
        </div>
      ))}
    </div>
  );
}

function Review({ cards }: { cards: Card[] }) {
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [known, setKnown] = useState<Set<string>>(new Set());

  const remaining = cards.filter((c) => !known.has(c.source));

  if (cards.length === 0) {
    return (
      <div className="review">
        <div className="review-done">
          <span style={{ fontSize: 32 }}>📖</span>
          <span>No cards yet — copy some words first</span>
        </div>
      </div>
    );
  }

  if (remaining.length === 0) {
    return (
      <div className="review">
        <div className="review-done">
          <span style={{ fontSize: 32 }}>🎉</span>
          <span>All {known.size} words reviewed!</span>
          <button
            className="btn btn-skip"
            style={{ marginTop: 8 }}
            onClick={() => {
              setKnown(new Set());
              setIndex(0);
            }}
          >
            Start over
          </button>
        </div>
      </div>
    );
  }

  const current = remaining[index % remaining.length];

  function next() {
    setRevealed(false);
    setIndex((i) => (i + 1) % remaining.length);
  }

  function markKnown() {
    setKnown((k) => new Set([...k, current.source]));
    setRevealed(false);
    setIndex((i) => i % Math.max(remaining.length - 1, 1));
  }

  return (
    <div className="review">
      <div className="review-card" onClick={() => setRevealed((r) => !r)}>
        <div className="review-word">{current.source}</div>
        {revealed ? (
          <div className="review-translation">{current.translation}</div>
        ) : (
          <div className="review-hint">tap to reveal</div>
        )}
      </div>

      <div className="review-controls">
        <button className="btn btn-skip" onClick={next}>
          Skip
        </button>
        <button className="btn btn-know" onClick={markKnown}>
          I know this ✓
        </button>
      </div>

      <div className="review-counter">
        {remaining.length} remaining · {known.size} learned
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<"feed" | "review">("feed");
  const [cards, setCards] = useState<Card[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket;
    let cancelled = false;

    async function init() {
      try {
        await waitForBackend();
        if (cancelled) return;

        fetch(`${BASE_URL}/flashcards`)
          .then((r) => r.json())
          .then(setCards)
          .catch(() => {});

        function connect() {
          ws = new WebSocket(WS_URL);
          ws.onopen = () => setConnected(true);
          ws.onclose = () => {
            setConnected(false);
            if (!cancelled) setTimeout(connect, 2000);
          };
          ws.onerror = () => ws.close();
          ws.onmessage = (e) => {
            const card: Card = JSON.parse(e.data);
            setCards((prev) => (prev.some((c) => c.source === card.source) ? prev : [card, ...prev]));
          };
        }

        connect();
      } catch (err) {
        console.error("Backend failed to start:", err);
        setConnected(false);
      }
    }

    init();
    return () => {
      cancelled = true;
      ws?.close();
    };
  }, []);

  return (
    <>
      <div className="header">
        <h1>Flashcard Clipboard</h1>
        <div className="status">
          <div className={`dot ${connected ? "connected" : ""}`} />
          {connected ? "live" : "offline"}
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === "feed" ? "active" : ""}`} onClick={() => setTab("feed")}>
          Feed · {cards.length}
        </button>
        <button className={`tab ${tab === "review" ? "active" : ""}`} onClick={() => setTab("review")}>
          Review
        </button>
      </div>

      {tab === "feed" ? <Feed cards={cards} connected={connected} /> : <Review cards={cards} />}
    </>
  );
}
