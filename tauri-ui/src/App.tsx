
import { useEffect, useState } from "react";
import "./App.css";

type Card = {
  source: string;
  translation: string;
  captured_at?: string;
};

const API_HOST = import.meta.env.VITE_API_HOST ?? "127.0.0.1";
const API_PORT = import.meta.env.VITE_API_PORT ?? "51847";

const BASE_URL = `http://${API_HOST}:${API_PORT}`;
const WS_URL = `ws://${API_HOST}:${API_PORT}/ws`;

const POLL_INTERVAL = 2000;
const RECONNECT_INTERVAL = 2000;

/* ── timestamp ── */

function normalizeTimestamp(timestamp: string): number | null {
  const value = Number(timestamp);

  if (!Number.isFinite(value)) {
    return null;
  }

  // Unix timestamp in seconds
  if (value < 100_000_000_000) {
    return value * 1000;
  }

  // Unix timestamp in milliseconds
  return value;
}

function formatRelativeDate(timestamp?: string): string {
  if (!timestamp) {
    return "";
  }

  const milliseconds = normalizeTimestamp(timestamp);

  if (milliseconds === null) {
    return "";
  }

  const date = new Date(milliseconds);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const now = new Date();

  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );

  const startOfDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate()
  );

  const diffDays = Math.floor(
    (startOfToday.getTime() - startOfDate.getTime()) /
      (1000 * 60 * 60 * 24)
  );

  if (diffDays === 0) {
    return "Today";
  }

  if (diffDays === 1) {
    return "Yesterday";
  }

  if (diffDays > 1) {
    return `${diffDays} days ago`;
  }

  // Future timestamps should not produce
  // negative values such as "-1 days ago".
  return "Today";
}

/* ── backend ── */

async function waitForBackend(
  timeoutMs = 15000
): Promise<void> {
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(`${BASE_URL}/health`, {
        cache: "no-store",
      });

      if (response.ok) {
        return;
      }
    } catch {
      // Backend is not ready yet.
    }

    await new Promise((resolve) => {
      setTimeout(resolve, 300);
    });
  }

  throw new Error("Backend not ready");
}

/* ── cards ── */

function getCardKey(card: Card): string {
  return `${card.source}__${card.captured_at ?? ""}`;
}

function getTimestamp(card: Card): number {
  if (!card.captured_at) {
    return 0;
  }

  return normalizeTimestamp(card.captured_at) ?? 0;
}

function upsertCards(
  previous: Card[],
  incoming: Card[]
): Card[] {
  const map = new Map<string, Card>();

  // Existing cards
  for (const card of previous) {
    map.set(getCardKey(card), card);
  }

  // New cards overwrite existing cards with the same key
  for (const card of incoming) {
    map.set(getCardKey(card), card);
  }

  const merged = Array.from(map.values());

  // Newest first
  merged.sort(
    (a, b) => getTimestamp(b) - getTimestamp(a)
  );

  return merged;
}

/* ── feed ── */

function Feed({
  cards,
  connected,
}: {
  cards: Card[];
  connected: boolean;
}) {
  if (!cards.length) {
    return (
      <div className="empty">
        <p>
          {connected
            ? "Waiting for clipboard updates..."
            : "Backend is offline..."}
        </p>
      </div>
    );
  }

  return (
    <div className="feed">
      {cards.map((card, index) => (
        <div
          className="card"
          key={`${getCardKey(card)}-${index}`}
        >
          <div className="card-main">
            <div className="source">
              {card.source}
            </div>

            {card.captured_at && (
              <div className="time">
                {formatRelativeDate(card.captured_at)}
              </div>
            )}
          </div>

          <div className="translation">
            {card.translation}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── review ── */

function Review({
  cards,
}: {
  cards: Card[];
}) {
  const [known, setKnown] = useState<Set<string>>(
    new Set()
  );

  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  const remaining = cards.filter(
    (card) => !known.has(card.source)
  );

  if (!remaining.length) {
    return (
      <div className="empty">
        <p>Nothing to review 🎉</p>
      </div>
    );
  }

  const current =
    remaining[index % remaining.length];

  function next() {
    setRevealed(false);

    setIndex(
      (currentIndex) =>
        (currentIndex + 1) % remaining.length
    );
  }

  function markKnown() {
    setKnown(
      (previousKnown) =>
        new Set([
          ...previousKnown,
          current.source,
        ])
    );

    setRevealed(false);

    setIndex(
      (currentIndex) =>
        currentIndex %
        Math.max(remaining.length - 1, 1)
    );
  }

  function toggleReveal() {
    setRevealed(
      (previousRevealed) => !previousRevealed
    );
  }

  return (
    <div className="review">
      <div
        className="review-card"
        onClick={toggleReveal}
      >
        <div className="review-word">
          {current.source}
        </div>

        {revealed ? (
          <div className="review-translation">
            {current.translation}
          </div>
        ) : (
          <div className="review-hint">
            tap to reveal
          </div>
        )}
      </div>

      <div className="review-controls">
        <button
          type="button"
          className="btn btn-skip"
          onClick={next}
        >
          Skip
        </button>

        <button
          type="button"
          className="btn btn-know"
          onClick={markKnown}
        >
          I know this ✓
        </button>
      </div>

      <div className="review-counter">
        {remaining.length} remaining ·{" "}
        {known.size} learned
      </div>
    </div>
  );
}

/* ── app ── */

export default function App() {
  const [tab, setTab] =
    useState<"feed" | "review">("feed");

  const [cards, setCards] = useState<Card[]>([]);

  const [connected, setConnected] =
    useState(false);

  useEffect(() => {
    let ws: WebSocket | undefined;

    let cancelled = false;

    let reconnectTimer:
      | ReturnType<typeof setTimeout>
      | undefined;

    let pollTimer:
      | ReturnType<typeof setInterval>
      | undefined;

    /* ── REST sync ── */

    async function syncFlashcards(): Promise<void> {
      try {
        const response = await fetch(
          `${BASE_URL}/flashcards`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          return;
        }

        const data: Card[] =
          await response.json();

        if (cancelled) {
          return;
        }

        setCards((previous) =>
          upsertCards(previous, data)
        );
      } catch {
        // Ignore.
        // Polling will retry automatically.
      }
    }

    /* ── polling ── */

    function startPolling(): void {
      if (pollTimer || cancelled) {
        return;
      }

      pollTimer = setInterval(() => {
        if (!cancelled) {
          void syncFlashcards();
        }
      }, POLL_INTERVAL);
    }

    /* ── websocket ── */

    function connectWebSocket(): void {
      if (cancelled) {
        return;
      }

      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        if (!cancelled) {
          setConnected(true);
        }
      };

      ws.onclose = () => {
        if (cancelled) {
          return;
        }

        setConnected(false);

        reconnectTimer = setTimeout(() => {
          reconnectTimer = undefined;
          connectWebSocket();
        }, RECONNECT_INTERVAL);
      };

      ws.onerror = () => {
        ws?.close();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(
            event.data
          );

          // Backend heartbeat
          if (message?.type === "ping") {
            return;
          }

          const card: Card = message;

          // Basic validation
          if (
            !card ||
            typeof card.source !== "string" ||
            typeof card.translation !== "string"
          ) {
            return;
          }

          setCards((previous) =>
            upsertCards(previous, [card])
          );
        } catch {
          // Ignore malformed messages.
        }
      };
    }

    /* ── initialization ── */

    async function init(): Promise<void> {
      try {
        await waitForBackend();

        if (cancelled) {
          return;
        }

        // Load persisted cards first.
        await syncFlashcards();

        if (cancelled) {
          return;
        }

        // Keep polling as a fallback.
        startPolling();

        // Then try live WebSocket.
        connectWebSocket();
      } catch (error) {
        console.error(
          "Backend failed to start:",
          error
        );

        setConnected(false);

        // Backend might become available later.
        startPolling();
      }
    }

    void init();

    /* ── cleanup ── */

    return () => {
      cancelled = true;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }

      if (pollTimer) {
        clearInterval(pollTimer);
      }

      ws?.close();
    };
  }, []);

  return (
    <>
      {/* Header */}
      <div className="header">
        <h1>Flashcard Clipboard</h1>

        <div className="status">
          <div
            className={`dot ${
              connected ? "connected" : ""
            }`}
          />

          {connected
            ? "live"
            : "offline (polling)"}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          type="button"
          className={`tab ${
            tab === "feed" ? "active" : ""
          }`}
          onClick={() => setTab("feed")}
        >
          Feed · {cards.length}
        </button>

        <button
          type="button"
          className={`tab ${
            tab === "review" ? "active" : ""
          }`}
          onClick={() => setTab("review")}
        >
          Review
        </button>
      </div>

      {/* Content */}
      {tab === "feed" ? (
        <Feed
          cards={cards}
          connected={connected}
        />
      ) : (
        <Review cards={cards} />
      )}
    </>
  );
}
